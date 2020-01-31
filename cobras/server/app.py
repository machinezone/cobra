'''Main entry point for the cobra websocket server

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''
import asyncio
import datetime
import functools
import http
import importlib
import rapidjson as json
import logging
import time
import traceback
import zlib
from urllib.parse import parse_qs, urlparse

import websockets
from cobras.common.apps_config import STATS_APPKEY, AppsConfig
from cobras.common.memory_debugger import MemoryDebugger
from cobras.common.task_cleanup import addTaskCleanup
from cobras.common.version import getVersion
from cobras.common.banner import getBanner
from cobras.server.connection_state import ConnectionState
from cobras.server.pipelined_publishers import PipelinedPublishers
from cobras.server.protocol import processCobraMessage
from cobras.server.redis_connections import RedisConnections
from cobras.server.stats import ServerStats


def parseAppKey(path):
    '''
    Parse url
    path = /v2?appkey=FFFFFFFFFFFFEEEEEEEEEEEEE
    '''
    parseResult = urlparse(path)
    args = parse_qs(parseResult.query)
    appkey = args.get('appkey')
    if appkey is None or not isinstance(appkey, list) or len(appkey) != 1:
        return None

    appkey = appkey[0]
    return appkey


async def cobraHandler(websocket, path, app, redisUrls: str):
    start = time.time()
    msgCount = 0
    appkey = parseAppKey(path)  # appkey must have been validated

    userAgent = websocket.requestHeaders.get('User-Agent', 'unknown-user-agent')

    state: ConnectionState = ConnectionState(appkey, userAgent)
    state.log('appkey {}'.format(state.appkey))

    # For debugging
    websocket.userAgent = userAgent
    websocket.connection_id = state.connection_id

    key = state.connection_id
    app['connections'][key] = (state, websocket)

    app['stats'].incrConnections(appkey)
    connectionCount = len(app['connections'])
    state.log(f'(open) connections {connectionCount}')

    try:
        async for message in websocket:
            msgCount += 1
            await processCobraMessage(state, websocket, app, message)
            if not state.ok:
                raise Exception(state.error)

    except websockets.exceptions.ProtocolError as e:
        print(e)
        state.log('Protocol error')
    except websockets.exceptions.ConnectionClosedOK:
        state.log('Connection closed properly')
    except websockets.exceptions.ConnectionClosedError:
        state.log('Connection closed with an error')
    except Exception as e:
        print(e)
        print('Generic Exception caught in {}'.format(traceback.format_exc()))
    finally:
        del app['connections'][key]

        subCount = len(state.subscriptions)

        if subCount > 0:
            state.log('cancelling #{} subscriptions'.format(subCount))
        for val in state.subscriptions.values():
            task, role = val
            app['stats'].decrSubscriptionsBy(role, 1)
            task.cancel()

        uptime = time.time() - start
        uptimeStr = str(datetime.timedelta(seconds=uptime))
        uptimeStr, _, _ = uptimeStr.partition('.')  # skip the milliseconds

        status = f'(close) uptime {uptimeStr} msgcount {msgCount}'
        status += ' connections {}'.format(len(app['connections']))
        state.log(status)

        app['stats'].decrConnections(appkey)


class ServerProtocol(websockets.WebSocketServerProtocol):
    '''Used to validate appkey'''

    appsConfig = None
    redisConnections = None

    async def process_request(self, path, request_headers):

        if path == '/health/':
            return http.HTTPStatus.OK, [], b'OK\n'

        if path == '/version/':
            return http.HTTPStatus.OK, [], bytes(getVersion(), 'utf8') + b'\n'

        if path == '/':
            return http.HTTPStatus.OK, [], bytes(getBanner(), 'utf8') + b'\n'

        if path == '/redis':
            info = await ServerProtocol.redisConnections.getRedisInfo()
            return http.HTTPStatus.OK, [], bytes(info, 'utf8') + b'\n'

        appkey = parseAppKey(path)
        if appkey is None or not ServerProtocol.appsConfig.isAppKeyValid(appkey):
            logging.warning(f'Rejecting request with invalid appkey for {path}')
            logging.warning(f'Request headers: {request_headers}')
            return http.HTTPStatus.FORBIDDEN, [], b'KO\n'

        self.requestHeaders = request_headers

    async def read_message(self):
        '''Override that method for debugging'''

        try:
            return await super().read_message()
        except zlib.error as e:
            headers = json.dumps({k: v for (k, v) in self.requestHeaders.raw_items()})
            logging.error(
                'Error in zlib for %s, %s, %s, %s',
                self.connection_id,
                self.userAgent,
                headers,
                e,
            )
            raise


class AppRunner:
    '''From aiohttp
    '''

    def __init__(
        self,
        host,
        port,
        redisUrls,
        redisPassword,
        appsConfigPath,
        debugMemory,
        debugMemoryNoTracemalloc,
        debugMemoryPrintAllTasks,
        plugins,
        enableStats,
        maxSubscriptions,
        idleTimeout,
        probeRedisOnStartup,
        redisStartupProbingTimeout,
    ):
        self.app = {}
        self.app['connections'] = {}
        self.app['apps_config_path'] = appsConfigPath
        self.app['max_subscriptions'] = maxSubscriptions
        self.app['idle_timeout'] = idleTimeout

        self.app['memory_debugger'] = debugMemory
        self.app['memory_debugger_no_tracemalloc'] = debugMemoryNoTracemalloc
        self.app['memory_debugger_print_all_tasks'] = debugMemoryPrintAllTasks
        self.app['redis_urls'] = redisUrls
        self.app['redis_password'] = redisPassword

        self.host = host
        self.port = port
        self.redisUrls = redisUrls
        self.redisPassword = redisPassword
        self.plugins = plugins
        self.enableStats = enableStats
        self.probeRedisOnStartup = probeRedisOnStartup
        self.redisStartupProbingTimeout = redisStartupProbingTimeout

        appsConfig = AppsConfig(appsConfigPath)
        self.app['apps_config'] = appsConfig

        try:
            appsConfig.validateConfig()
        except ValueError as e:
            logging.error(f'Invalid apps config file: {e}')
            pass

        try:
            if plugins is not None:
                self.app['plugins'] = importlib.import_module(plugins)
        except ImportError:
            logging.error(f'failure to import {plugins}')

        self.app['batch_publish_size'] = appsConfig.getBatchPublishSize()
        self.app['channel_max_length'] = appsConfig.getChannelMaxLength()
        self.server = None

    async def init_app(self):
        '''Example urls:
           * redis://localhost
           * redis://redis
           * redis://172.18.176.220:7379
           * redis://sentryredis-1-002.shared.live.las1.mz-inc.com:6310
        '''
        redisUrls = self.app['redis_urls']
        redisPassword = self.app['redis_password']
        batchPublishSize = self.app['batch_publish_size']
        channelMaxLength = self.app['channel_max_length']

        # Create redis connection handler, and
        # wait until all the redis nodes are reachable
        redisConnections = RedisConnections(redisUrls, redisPassword)
        self.app['redis_connections'] = redisConnections
        if self.probeRedisOnStartup:
            await redisConnections.waitForAllConnectionsToBeReady(
                timeout=self.redisStartupProbingTimeout
            )

        pipelinedPublishers = PipelinedPublishers(
            redisConnections, batchPublishSize, channelMaxLength
        )
        self.app['pipelined_publishers'] = pipelinedPublishers

        serverStats = ServerStats(pipelinedPublishers, STATS_APPKEY)
        self.app['stats'] = serverStats

        if self.enableStats:
            self.serverStatsTask = asyncio.create_task(serverStats.run())
            addTaskCleanup(self.serverStatsTask)

        if self.app.get('memory_debugger'):
            memoryDebugger = MemoryDebugger(
                noTraceMalloc=self.app.get('memory_debugger_no_tracemalloc'),
                printAllTasks=self.app.get('memory_debugger_print_all_tasks'),
            )
            self.app['memory_debugger'] = memoryDebugger

            self.memoryDebuggerTask = asyncio.create_task(memoryDebugger.run())
            addTaskCleanup(self.memoryDebuggerTask)

    async def cleanup(self):
        # FIXME: we could speed this up
        if self.enableStats:
            self.app['stats'].terminate()
            await self.serverStatsTask

        if self.app.get('memory_debugger'):
            self.app['memory_debugger'].terminate()
            await self.memoryDebuggerTask

    async def setup(self, stop=None, block=False):
        '''It would be good to unify better unittest mode versus command mode,
           and get rid of block
        '''
        await self.init_app()

        handler = functools.partial(
            cobraHandler, app=self.app, redisUrls=self.redisUrls
        )

        ServerProtocol.appsConfig = self.app['apps_config']
        ServerProtocol.redisConnections = self.app['redis_connections']

        if block:
            async with websockets.serve(
                handler,
                self.host,
                self.port,
                create_protocol=ServerProtocol,
                subprotocols=['json'],
                ping_timeout=None,
                ping_interval=None,
            ) as self.server:
                await stop
                self.closeRedis()
                await self.cleanup()
        else:
            self.server = await websockets.serve(
                handler,
                self.host,
                self.port,
                create_protocol=ServerProtocol,
                subprotocols=['json'],
                ping_timeout=None,
                ping_interval=None,
            )

    def run(self, stop):
        asyncio.get_event_loop().run_until_complete(self.setup(stop, block=True))

    def closeRedis(self):
        db = self.app['pipelined_publishers']
        db.close()

    async def closeServer(self):
        '''Used by the unittest'''
        # Now close websocket server
        self.server.close()
        await self.server.wait_closed()

    def terminate(self):
        '''Used by the unittest'''
        self.closeRedis()
        asyncio.get_event_loop().run_until_complete(self.cleanup())
        asyncio.get_event_loop().run_until_complete(self.closeServer())

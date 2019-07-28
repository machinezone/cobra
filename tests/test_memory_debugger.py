'''Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.'''

import asyncio

from cobras.common.memory_debugger import MemoryDebugger


def test_memory_debugger():
    memoryDebugger = MemoryDebugger(0.1, 2)
    asyncio.get_event_loop().run_until_complete(memoryDebugger.run())

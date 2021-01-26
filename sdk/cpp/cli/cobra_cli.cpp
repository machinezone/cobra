/*
 *  cobra_cli.cpp
 *  Author: Benjamin Sergeant
 *  Copyright (c) 2019-2021 Machine Zone, Inc. All rights reserved.
 */

//
// Main driver for cobra utilities
//

#include <CLI/CLI.hpp>
#include <spdlog/sinks/basic_file_sink.h>
#include <spdlog/spdlog.h>

#include <ixbots/IXCobraToCobraBot.h>
#include <ixbots/IXCobraToPythonBot.h>
#include <ixbots/IXCobraToSentryBot.h>
#include <ixbots/IXCobraToStatsdBot.h>
#include <ixbots/IXCobraToStdoutBot.h>
#include <ixcobra/IXCobraMetricsPublisher.h>
#include <ixcore/utils/IXCoreLogger.h>
#include <ixwebsocket/IXUserAgent.h>

#include <sstream>
#include <string>
#include <vector>
#include <atomic>
#include <chrono>
#include <condition_variable>
#include <fstream>
#include <iostream>

#ifndef _WIN32
#include <signal.h>
#else
#include <process.h>
#define getpid _getpid
#endif

namespace
{
    bool fileExists(const std::string& fileName)
    {
        std::ifstream infile(fileName);
        return infile.good();
    }
} // namespace


namespace ix
{
    int ws_cobra_publish_main(const ix::CobraConfig& config,
                              const std::string& channel,
                              const std::string& path)
    {
        std::ifstream f(path);
        std::string str((std::istreambuf_iterator<char>(f)), std::istreambuf_iterator<char>());

        Json::Value data;
        Json::Reader reader;
        if (!reader.parse(str, data))
        {
            spdlog::info("Input file is not a JSON file");
            return 1;
        }

        ix::CobraConnection conn;
        conn.configure(config);

        // Display incoming messages
        std::atomic<bool> authenticated(false);
        std::atomic<bool> messageAcked(false);

        conn.setEventCallback(
            [&conn, &channel, &data, &authenticated, &messageAcked](const CobraEventPtr& event) {
                if (event->type == ix::CobraEventType::Open)
                {
                    spdlog::info("Publisher connected");

                    for (auto&& it : event->headers)
                    {
                        spdlog::info("{}: {}", it.first, it.second);
                    }
                }
                else if (event->type == ix::CobraEventType::Closed)
                {
                    spdlog::info("Subscriber closed: {}", event->errMsg);
                }
                else if (event->type == ix::CobraEventType::Authenticated)
                {
                    spdlog::info("Publisher authenticated");
                    authenticated = true;

                    Json::Value channels;
                    channels[0] = channel;
                    auto msgId = conn.publish(channels, data);

                    spdlog::info("Published msg {}", msgId);
                }
                else if (event->type == ix::CobraEventType::Subscribed)
                {
                    spdlog::info("Publisher: subscribed to channel {}", event->subscriptionId);
                }
                else if (event->type == ix::CobraEventType::UnSubscribed)
                {
                    spdlog::info("Publisher: unsubscribed from channel {}", event->subscriptionId);
                }
                else if (event->type == ix::CobraEventType::Error)
                {
                    spdlog::error("Publisher: error {}", event->errMsg);
                }
                else if (event->type == ix::CobraEventType::Published)
                {
                    spdlog::info("Published message id {} acked", event->msgId);
                    messageAcked = true;
                }
                else if (event->type == ix::CobraEventType::Pong)
                {
                    spdlog::info("Received websocket pong");
                }
                else if (event->type == ix::CobraEventType::HandshakeError)
                {
                    spdlog::error("Subscriber: Handshake error: {}", event->errMsg);
                }
                else if (event->type == ix::CobraEventType::AuthenticationError)
                {
                    spdlog::error("Subscriber: Authentication error: {}", event->errMsg);
                }
            });

        conn.connect();

        while (!authenticated)
            ;
        while (!messageAcked)
            ;

        return 0;
    }

    int ws_cobra_metrics_publish_main(const ix::CobraConfig& config,
                                      const std::string& channel,
                                      const std::string& path,
                                      bool stress)
    {
        std::atomic<int> sentMessages(0);
        std::atomic<int> ackedMessages(0);
        CobraConnection::setPublishTrackerCallback(
            [&sentMessages, &ackedMessages](bool sent, bool acked) {
                if (sent) sentMessages++;
                if (acked) ackedMessages++;
            });

        CobraMetricsPublisher cobraMetricsPublisher;
        cobraMetricsPublisher.enable(true);
        cobraMetricsPublisher.configure(config, channel);

        while (!cobraMetricsPublisher.isAuthenticated())
            ;

        std::ifstream f(path);
        std::string str((std::istreambuf_iterator<char>(f)), std::istreambuf_iterator<char>());

        Json::Value data;
        Json::Reader reader;
        if (!reader.parse(str, data)) return 1;

        if (!stress)
        {
            auto msgId = cobraMetricsPublisher.push(channel, data);
            spdlog::info("Sent message: {}", msgId);
        }
        else
        {
            // Stress mode to try to trigger server and client bugs
            while (true)
            {
                for (int i = 0; i < 1000; ++i)
                {
                    cobraMetricsPublisher.push(channel, data);
                }

                cobraMetricsPublisher.suspend();
                cobraMetricsPublisher.resume();

                // FIXME: investigate why without this check we trigger a lock
                while (!cobraMetricsPublisher.isAuthenticated())
                    ;
            }
        }

        // Wait a bit for the message to get a chance to be sent
        // there isn't any ack on publish right now so it's the best we can do
        // FIXME: this comment is a lie now
        std::this_thread::sleep_for(std::chrono::milliseconds(100));

        spdlog::info("Sent messages: {} Acked messages {}", sentMessages, ackedMessages);

        return 0;
    }
}

int main(int argc, char** argv)
{
    ix::initNetSystem();

    ix::CoreLogger::LogFunc logFunc = [](const char* msg, ix::LogLevel level) {
        switch (level)
        {
            case ix::LogLevel::Debug:
            {
                spdlog::debug(msg);
            }
            break;

            case ix::LogLevel::Info:
            {
                spdlog::info(msg);
            }
            break;

            case ix::LogLevel::Warning:
            {
                spdlog::warn(msg);
            }
            break;

            case ix::LogLevel::Error:
            {
                spdlog::error(msg);
            }
            break;

            case ix::LogLevel::Critical:
            {
                spdlog::critical(msg);
            }
            break;
        }
    };
    ix::CoreLogger::setLogFunction(logFunc);
    spdlog::set_level(spdlog::level::debug);

#ifndef _WIN32
    signal(SIGPIPE, SIG_IGN);
#endif

    // Display command.
    if (getenv("DEBUG"))
    {
        std::stringstream ss;
        ss << "Command: ";
        for (int i = 0; i < argc; ++i)
        {
            ss << argv[i] << " ";
        }
        spdlog::info(ss.str());
    }

    CLI::App app {"cobra_cli is a cobra cli"};

    std::string url("ws://127.0.0.1:8008");
    std::string path;
    std::string user;
    std::string data;
    std::string formData;
    std::string binaryData;
    std::string headers;
    std::string output;
    std::string hostname("127.0.0.1");
    std::string pidfile;
    std::string channel;
    std::string filter;
    std::string position;
    std::string message;
    std::string password;
    std::string prefix("ws.test.v0");
    std::string fields;
    std::string gauge;
    std::string timer;
    std::string dsn;
    std::string redisHosts("127.0.0.1");
    std::string redisPassword;
    std::string appsConfigPath("appsConfig.json");
    std::string configPath;
    std::string subprotocol;
    std::string remoteHost;
    std::string minidump;
    std::string metadata;
    std::string project;
    std::string key;
    std::string logfile;
    std::string moduleName;
    std::string republishChannel;
    std::string publisherRolename;
    std::string publisherRolesecret;
    std::string sendMsg("hello world");
    std::string filename;
    std::string httpHeaderAuthorization;
    ix::SocketTLSOptions tlsOptions;
    ix::CobraConfig cobraConfig;
    ix::CobraBotConfig cobraBotConfig;
    std::string ciphers;
    std::string redirectUrl;
    bool headersOnly = false;
    bool followRedirects = false;
    bool verbose = false;
    bool save = false;
    bool quiet = false;
    bool fluentd = false;
    bool compress = false;
    bool compressRequest = false;
    bool stress = false;
    bool disableAutomaticReconnection = false;
    bool disablePerMessageDeflate = false;
    bool greetings = false;
    bool ipv6 = false;
    bool binaryMode = false;
    bool redirect = false;
    bool version = false;
    bool verifyNone = false;
    bool disablePong = false;
    bool debug = false;
    int port = 8008;
    int redisPort = 6379;
    int statsdPort = 8125;
    int connectTimeOut = 60;
    int transferTimeout = 1800;
    int maxRedirects = 5;
    int delayMs = -1;
    int count = 1;
    int msgCount = 1000 * 1000;
    uint32_t maxWaitBetweenReconnectionRetries;
    int pingIntervalSecs = 30;
    int runCount = 1;

    auto addGenericOptions = [&pidfile](CLI::App* app) {
        app->add_option("--pidfile", pidfile, "Pid file");
    };

    auto addTLSOptions = [&tlsOptions, &verifyNone](CLI::App* app) {
        app->add_option(
               "--cert-file", tlsOptions.certFile, "Path to the (PEM format) TLS cert file")
            ->check(CLI::ExistingPath);
        app->add_option("--key-file", tlsOptions.keyFile, "Path to the (PEM format) TLS key file")
            ->check(CLI::ExistingPath);
        app->add_option("--ca-file", tlsOptions.caFile, "Path to the (PEM format) ca roots file")
            ->check(CLI::ExistingPath);
        app->add_option("--ciphers",
                        tlsOptions.ciphers,
                        "A (comma/space/colon) separated list of ciphers to use for TLS");
        app->add_flag("--tls", tlsOptions.tls, "Enable TLS (server only)");
        app->add_flag("--verify_none", verifyNone, "Disable peer cert verification");
    };

    auto addCobraConfig = [&cobraConfig](CLI::App* app) {
        app->add_option("--appkey", cobraConfig.appkey, "Appkey")->required();
        app->add_option("--endpoint", cobraConfig.endpoint, "Endpoint")->required();
        app->add_option("--rolename", cobraConfig.rolename, "Role name")->required();
        app->add_option("--rolesecret", cobraConfig.rolesecret, "Role secret")->required();
    };

    auto addCobraBotConfig = [&cobraBotConfig](CLI::App* app) {
        app->add_option("--appkey", cobraBotConfig.cobraConfig.appkey, "Appkey")->required();
        app->add_option("--endpoint", cobraBotConfig.cobraConfig.endpoint, "Endpoint")->required();
        app->add_option("--rolename", cobraBotConfig.cobraConfig.rolename, "Role name")->required();
        app->add_option("--rolesecret", cobraBotConfig.cobraConfig.rolesecret, "Role secret")
            ->required();
        app->add_option("--channel", cobraBotConfig.channel, "Channel")->required();
        app->add_option("--filter", cobraBotConfig.filter, "Filter");
        app->add_option("--position", cobraBotConfig.position, "Position");
        app->add_option("--runtime", cobraBotConfig.runtime, "Runtime");
        app->add_option("--heartbeat", cobraBotConfig.enableHeartbeat, "Runtime");
        app->add_option("--heartbeat_timeout", cobraBotConfig.heartBeatTimeout, "Runtime");
        app->add_flag(
            "--limit_received_events", cobraBotConfig.limitReceivedEvents, "Max events per minute");
        app->add_option(
            "--max_events_per_minute", cobraBotConfig.maxEventsPerMinute, "Max events per minute");
        app->add_option("--batch_size", cobraBotConfig.batchSize, "Subscription batch size");
    };

    app.add_flag("--version", version, "Print ws version");
    app.add_option("--logfile", logfile, "path where all logs will be redirected");

    CLI::App* cobraSubscribeApp = app.add_subcommand("cobra_subscribe", "Cobra subscriber");
    cobraSubscribeApp->fallthrough();
    cobraSubscribeApp->add_option("--pidfile", pidfile, "Pid file");
    cobraSubscribeApp->add_flag("-q", quiet, "Quiet / only display stats");
    cobraSubscribeApp->add_flag("--fluentd", fluentd, "Write fluentd prefix");
    addTLSOptions(cobraSubscribeApp);
    addCobraBotConfig(cobraSubscribeApp);

    CLI::App* cobraPublish = app.add_subcommand("cobra_publish", "Cobra publisher");
    cobraPublish->fallthrough();
    cobraPublish->add_option("--channel", channel, "Channel")->required();
    cobraPublish->add_option("--pidfile", pidfile, "Pid file");
    cobraPublish->add_option("path", path, "Path to the file to send")
        ->required()
        ->check(CLI::ExistingPath);
    addTLSOptions(cobraPublish);
    addCobraConfig(cobraPublish);

    CLI::App* cobraMetricsPublish =
        app.add_subcommand("cobra_metrics_publish", "Cobra metrics publisher");
    cobraMetricsPublish->fallthrough();
    cobraMetricsPublish->add_option("--channel", channel, "Channel")->required();
    cobraMetricsPublish->add_option("--pidfile", pidfile, "Pid file");
    cobraMetricsPublish->add_option("path", path, "Path to the file to send")
        ->required()
        ->check(CLI::ExistingPath);
    cobraMetricsPublish->add_flag("--stress", stress, "Stress mode");
    addTLSOptions(cobraMetricsPublish);
    addCobraConfig(cobraMetricsPublish);

    CLI::App* cobra2statsd = app.add_subcommand("cobra_to_statsd", "Cobra to statsd");
    cobra2statsd->fallthrough();
    cobra2statsd->add_option("--host", hostname, "Statsd host");
    cobra2statsd->add_option("--port", statsdPort, "Statsd port");
    cobra2statsd->add_option("--prefix", prefix, "Statsd prefix");
    cobra2statsd->add_option("--fields", fields, "Extract fields for naming the event")->join();
    cobra2statsd->add_option("--gauge", gauge, "Value to extract, and use as a statsd gauge")
        ->join();
    cobra2statsd->add_option("--timer", timer, "Value to extract, and use as a statsd timer")
        ->join();
    cobra2statsd->add_flag("-v", verbose, "Verbose");
    cobra2statsd->add_option("--pidfile", pidfile, "Pid file");
    addTLSOptions(cobra2statsd);
    addCobraBotConfig(cobra2statsd);

    CLI::App* cobra2cobra = app.add_subcommand("cobra_to_cobra", "Cobra to Cobra");
    cobra2cobra->fallthrough();
    cobra2cobra->add_option("--republish", republishChannel, "Republish channel");
    cobra2cobra->add_option("--publisher_rolename", publisherRolename, "Publisher Role name")
        ->required();
    cobra2cobra->add_option("--publisher_rolesecret", publisherRolesecret, "Publisher Role secret")
        ->required();
    cobra2cobra->add_flag("-q", quiet, "Quiet");
    addTLSOptions(cobra2cobra);
    addCobraBotConfig(cobra2cobra);

    CLI::App* cobra2python = app.add_subcommand("cobra_to_python", "Cobra to python");
    cobra2python->fallthrough();
    cobra2python->add_option("--host", hostname, "Statsd host");
    cobra2python->add_option("--port", statsdPort, "Statsd port");
    cobra2python->add_option("--prefix", prefix, "Statsd prefix");
    cobra2python->add_option("--module", moduleName, "Python module");
    cobra2python->add_option("--pidfile", pidfile, "Pid file");
    addTLSOptions(cobra2python);
    addCobraBotConfig(cobra2python);

    CLI::App* cobra2sentry = app.add_subcommand("cobra_to_sentry", "Cobra to sentry");
    cobra2sentry->fallthrough();
    cobra2sentry->add_option("--dsn", dsn, "Sentry DSN");
    cobra2sentry->add_flag("-v", verbose, "Verbose");
    cobra2sentry->add_option("--pidfile", pidfile, "Pid file");
    addTLSOptions(cobra2sentry);
    addCobraBotConfig(cobra2sentry);

    CLI::App* cobra2redisApp =
        app.add_subcommand("cobra_metrics_to_redis", "Cobra metrics to redis");
    cobra2redisApp->fallthrough();
    cobra2redisApp->add_option("--pidfile", pidfile, "Pid file");
    cobra2redisApp->add_option("--hostname", hostname, "Redis hostname");
    cobra2redisApp->add_option("--port", redisPort, "Redis port");
    cobra2redisApp->add_flag("-v", verbose, "Verbose");
    addTLSOptions(cobra2redisApp);
    addCobraBotConfig(cobra2redisApp);

    CLI11_PARSE(app, argc, argv);

    // pid file handling
    if (!pidfile.empty())
    {
        unlink(pidfile.c_str());

        std::ofstream f;
        f.open(pidfile);
        f << getpid();
        f.close();
    }

    if (verifyNone)
    {
        tlsOptions.caFile = "NONE";
    }

    if (tlsOptions.isUsingSystemDefaults())
    {
#if defined(__APPLE__)
#if defined(IXWEBSOCKET_USE_MBED_TLS) || defined(IXWEBSOCKET_USE_OPEN_SSL)
        // We could try to load some system certs as well, but this is easy enough
        tlsOptions.caFile = "/etc/ssl/cert.pem";
#endif
#elif defined(__linux__)
#if defined(IXWEBSOCKET_USE_MBED_TLS)
        std::vector<std::string> caFiles = {
            "/etc/ssl/certs/ca-bundle.crt",       // CentOS
            "/etc/ssl/certs/ca-certificates.crt", // Alpine
        };

        for (auto&& caFile : caFiles)
        {
            if (fileExists(caFile))
            {
                tlsOptions.caFile = caFile;
                break;
            }
        }
#endif
#endif
    }

    if (!logfile.empty())
    {
        try
        {
            auto fileLogger = spdlog::basic_logger_mt("ws", logfile);
            spdlog::set_default_logger(fileLogger);
            spdlog::flush_every(std::chrono::seconds(1));

            std::cerr << "All logs will be redirected to " << logfile << std::endl;
        }
        catch (const spdlog::spdlog_ex& ex)
        {
            std::cerr << "Fatal error, log init failed: " << ex.what() << std::endl;
            ix::uninitNetSystem();
            return 1;
        }
    }

    if (quiet)
    {
        spdlog::set_level(spdlog::level::info);
    }

    // Cobra config
    cobraConfig.webSocketPerMessageDeflateOptions = ix::WebSocketPerMessageDeflateOptions(true);
    cobraConfig.socketTLSOptions = tlsOptions;

    cobraBotConfig.cobraConfig.webSocketPerMessageDeflateOptions =
        ix::WebSocketPerMessageDeflateOptions(true);
    cobraBotConfig.cobraConfig.socketTLSOptions = tlsOptions;

    int ret = 1;
    if (app.got_subcommand("cobra_subscribe"))
    {
        int64_t sentCount = ix::cobra_to_stdout_bot(cobraBotConfig, fluentd, quiet);
        ret = (int) sentCount;
    }
    else if (app.got_subcommand("cobra_publish"))
    {
        ret = ix::ws_cobra_publish_main(cobraConfig, channel, path);
    }
    else if (app.got_subcommand("cobra_metrics_publish"))
    {
        ret = ix::ws_cobra_metrics_publish_main(cobraConfig, channel, path, stress);
    }
    else if (app.got_subcommand("cobra_to_statsd"))
    {
        if (!timer.empty() && !gauge.empty())
        {
            spdlog::error("--gauge and --timer options are exclusive. "
                          "you can only supply one");
            ret = 1;
        }
        else
        {
            ix::StatsdClient statsdClient(hostname, statsdPort, prefix, verbose);

            std::string errMsg;
            bool initialized = statsdClient.init(errMsg);
            if (!initialized)
            {
                spdlog::error(errMsg);
                ret = 1;
            }
            else
            {
                ret = (int) ix::cobra_to_statsd_bot(
                    cobraBotConfig, statsdClient, fields, gauge, timer, verbose);
            }
        }
    }
    else if (app.got_subcommand("cobra_to_python"))
    {
        ix::StatsdClient statsdClient(hostname, statsdPort, prefix, verbose);

        std::string errMsg;
        bool initialized = statsdClient.init(errMsg);
        if (!initialized)
        {
            spdlog::error(errMsg);
            ret = 1;
        }
        else
        {
            ret = (int) ix::cobra_to_python_bot(cobraBotConfig, statsdClient, moduleName);
        }
    }
    else if (app.got_subcommand("cobra_to_sentry"))
    {
        ix::SentryClient sentryClient(dsn);
        sentryClient.setTLSOptions(tlsOptions);

        ret = (int) ix::cobra_to_sentry_bot(cobraBotConfig, sentryClient, verbose);
    }
    else if (app.got_subcommand("cobra_to_cobra"))
    {
        ret = (int) ix::cobra_to_cobra_bot(
            cobraBotConfig, republishChannel, publisherRolename, publisherRolesecret);
    }
    else if (version)
    {
        std::cout << "ws " << ix::userAgent() << std::endl;
    }
    else
    {
        spdlog::error("A subcommand or --version is required");
    }

    ix::uninitNetSystem();
    return ret;
}

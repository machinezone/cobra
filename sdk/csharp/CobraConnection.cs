//
// CobraConnection.cs
// Author: Benjamin Sergeant
// Copyright (c) 2020 Machine Zone, Inc. All rights reserved.
//
using System;
using System.Threading;
using System.Threading.Tasks;
using System.Net.WebSockets;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Cobra
{
    //
    // Configuration to connect and authenticate to the server
    //
    public struct CobraConfig
    {
        public string endpoint { get; set; }
        public string appkey { get; set; }
        public string rolename { get; set; }
        public string rolesecret { get; set; }
    }

    public class CobraException : Exception
    {
        public CobraException(string message, Exception inner)
            : base(message, inner)
        {
        }
    }

    //
    // Handshake request
    //
    public class HandshakePdu
    {
        public string action { get; set; }
        public int id { get; set; }
        public HandshakeBody body { get; set; }
    }

    public class HandshakeBody
    {
        public string method { get; set; }
        public HandshakeBodyData data { get; set; }
    }

    public class HandshakeBodyData
    {
        public string role { get; set; }
    }

    //
    // Handshake response
    //
    public class HandshakeResponsePdu
    {
        public string action { get; set; }
        public int id { get; set; }
        public HandshakeResponseBody body { get; set; }
    }

    public class HandshakeResponseBody
    {
        public HandshakeResponseBodyData data { get; set; }
    }

    public class HandshakeResponseBodyData
    {
        public string nonce { get; set; }
        public string version { get; set; }
        public string connection_id { get; set; }
        public string node { get; set; }
    }

    //
    // Auth request
    //
    public class AuthPdu
    {
        public string action { get; set; }
        public int id { get; set; }
        public AuthBody body { get; set; }
    }

    public class AuthBody
    {
        public string method { get; set; }
        public AuthBodyCredentials credentials { get; set; }
    }

    public class AuthBodyCredentials
    {
        public string hash { get; set; }
    }

    //
    // Auth request
    //
    public class AuthResponsePdu
    {
        public string action { get; set; }
        public int id { get; set; }
    }

    public class CobraConnection
    {
        CobraConfig config;
        ClientWebSocket ws;

        public CobraConnection(CobraConfig cobraConfig)
        {
            config = cobraConfig;

            ws = new ClientWebSocket();
            ws.Options.AddSubProtocol("json");
            ws.Options.KeepAliveInterval = TimeSpan.FromSeconds(30);
        }

        public async Task Connect(CancellationToken cancellationToken)
        {
            var url = $"{config.endpoint}/v2?appkey={config.appkey}";
            System.Uri uri = new System.Uri(url);

            try
            {
                await ws.ConnectAsync(uri, cancellationToken).ConfigureAwait(false);
            }
            catch (System.Net.WebSockets.WebSocketException e)
            {
                throw new CobraException("Connection error to " + url, e);
            }

            //
            // 1. Send Handshake message
            //
            // {
            //   "action": "auth/handshake",
            //   "body": {
            //     "method": "role_secret",
            //     "data": {
            //       "role": "pubsub"
            //     }
            //   }
            // }
            //
            var handshakePdu = new HandshakePdu
            {
                action = "auth/handshake",
                id = 0,
                body = new HandshakeBody
                {
                    method = "role_secret",
                    data = new HandshakeBodyData
                    {
                        role = config.rolename
                    }
                }
            };

            byte[] bytes = JsonSerializer.SerializeToUtf8Bytes(handshakePdu);
            string str = Encoding.UTF8.GetString(bytes, 0, bytes.Length);
            Console.WriteLine(str);

            try
            {
                await ws.SendAsync(new System.ArraySegment<byte>(bytes),
                                   WebSocketMessageType.Text,
                                   true, cancellationToken).ConfigureAwait(false);
            }
            catch (System.Net.WebSockets.WebSocketException e)
            {
                throw new CobraException("Handshake send error", e);
            }

            //
            // 2. Get handshake response
            //
            // {
            //   "action": "auth/handshake/ok",
            //   "id": 0,
            //   "body": {
            //     "data": {
            //       "nonce": "MTYxMjc1MzMwOTM2MjY4OTY0MDg=",
            //       "version": "2.9.93",
            //       "connection_id": "671e0795c542",
            //       "node": "localhost"
            //     }
            //   }
            // }
            //
            var handshakeResponseStr = await this.ReceiveAsync(cancellationToken);

            // FIXME: decoding error handling
            var handshakeResponse = JsonSerializer.Deserialize<HandshakeResponsePdu>(handshakeResponseStr);
            var nonce = handshakeResponse.body.data.nonce;
            Console.WriteLine(nonce);

            //
            // 3. Send Auth request
            //
            // {
            //   "action": "auth/authenticate",
            //   "body": {
            //     "method": "role_secret",
            //     "credentials": {
            //       "hash": "exv9g4YXR3uPKZGpoHif1w=="
            //     }
            //   },
            //   "id": 1
            // }
            //
            var hash = this.ComputeAuthHash(nonce);
            var authPdu = new AuthPdu
            {
                action = "auth/authenticate",
                id = 1,
                body = new AuthBody
                {
                    method = "role_secret",
                    credentials = new AuthBodyCredentials
                    {
                        hash = hash
                    }
                }
            };

            bytes = JsonSerializer.SerializeToUtf8Bytes(authPdu);
            str = Encoding.UTF8.GetString(bytes, 0, bytes.Length);
            Console.WriteLine(str);

            try
            {
                await ws.SendAsync(new System.ArraySegment<byte>(bytes),
                                   WebSocketMessageType.Text,
                                   true, cancellationToken).ConfigureAwait(false);
            }
            catch (System.Net.WebSockets.WebSocketException e)
            {
                throw new CobraException("Handshake send error", e);
            }

            //
            // 4. Get auth response
            //
            var authResponseStr = await this.ReceiveAsync(cancellationToken);

            // FIXME: decoding error handling
            var authResponse = JsonSerializer.Deserialize<AuthResponsePdu>(authResponseStr);
            // var nonce = handshakeResponse.body.data.nonce;
            // Console.WriteLine(nonce);
            Console.WriteLine(authResponse.action);

            if (authResponse.action != "auth/handshake/ok")
            {
                throw new CobraException("Authentication error", new Exception());
            }
        }

        public async Task<string> ReceiveAsync(CancellationToken token)
        {
            // FIXME hard-coded to 512 / it's ok as responses are very small
            byte[] data = new byte[512];
            var result = await ws.ReceiveAsync(new ArraySegment<byte>(data),
                                               CancellationToken.None).ConfigureAwait(false);
            var str = Encoding.UTF8.GetString(data, 0, result.Count);
            return str;
        }

        public string ComputeAuthHash(string nonce)
        {
            // FIXME: write me
            return "foo";
        }

        public async Task Publish(string str)
        {
        }
    }
}

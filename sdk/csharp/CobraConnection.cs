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
using System.Security.Cryptography; // For md5


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
    // Auth response
    //
    public class AuthResponsePdu
    {
        public string action { get; set; }
        public int id { get; set; }
    }

    //
    // Publish message
    //
    public class PublishPdu
    {
        public string action { get; set; }
        public int id { get; set; }
        public PublishBody body { get; set; }
    }

    public class PublishBody
    {
        public string channel { get; set; }
        public string message { get; set; }
    }

    public class CobraConnection
    {
        CobraConfig config;
        ClientWebSocket ws;
        int id;

        public CobraConnection(CobraConfig cobraConfig)
        {
            id = 0;
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
                id = id++,
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
            var hash = this.ComputeAuthHash(config.rolesecret, nonce);
            var authPdu = new AuthPdu
            {
                action = "auth/authenticate",
                id = id++,
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
                throw new CobraException("Auth send error", e);
            }

            //
            // 4. Get auth response
            //
            var authResponseStr = await this.ReceiveAsync(cancellationToken);

            // FIXME: decoding error handling
            var authResponse = JsonSerializer.Deserialize<AuthResponsePdu>(authResponseStr);

            // FIXME / validate return value
            // if (authResponse.action != "auth/handshake/ok")
            // {
            //     Console.WriteLine("ERROR");
            //     Console.WriteLine(authResponse.action);
            //     // throw new CobraException("Authentication error", new Exception());
            // }
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

        //
        // def computeHash(secret: bytes, nonce: bytes) -> str:
        //     binary_hash = hmac.new(secret, nonce, hashlib.md5).digest()
        //     ascii_hash = base64.b64encode(binary_hash)
        //
        //     h = ascii_hash.decode('ascii')
        //     return h
        //
        public string ComputeAuthHash(string secret, string nonce)
        {
            var secretBin = Encoding.UTF8.GetBytes(secret);
            var nonceBin = Encoding.UTF8.GetBytes(nonce);
            using (var hmac = new HMACMD5(secretBin))
            {
                var hashBin = hmac.ComputeHash(nonceBin);
                var hash = Convert.ToBase64String(hashBin);
                return hash;
            }
        }

        public async Task Publish(string channel,
                                  string message,
                                  CancellationToken cancellationToken)
        {
            var publishPdu = new PublishPdu
            {
                action = "rtm/publish",
                id = id++,
                body = new PublishBody
                {
                    channel = channel,
                    message = message
                }
            };

            byte[] bytes = JsonSerializer.SerializeToUtf8Bytes(publishPdu);
            var str = Encoding.UTF8.GetString(bytes, 0, bytes.Length);
            Console.WriteLine(str);

            try
            {
                await ws.SendAsync(new System.ArraySegment<byte>(bytes),
                                   WebSocketMessageType.Text,
                                   true, cancellationToken).ConfigureAwait(false);
            }
            catch (System.Net.WebSockets.WebSocketException e)
            {
                throw new CobraException("Publish send error", e);
            }

            // We ignore the response at this point
            var response = await this.ReceiveAsync(cancellationToken);
            Console.WriteLine(response);
        }
    }
}

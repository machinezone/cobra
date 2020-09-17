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

            // Send Handshake message
            // let request = {
            //   'action':'auth/handshake',
            //   'body': {
            //     'method':'role_secret',
            //     'data':{
            //       'role': this.role
            //     }
            //   }
            // }

            /*
            var handshakeBodyData = new HandshakeBodyData
            {
                role = config.rolename,
            };

            var handshakeBody = new HandshakeBody
            {
                method = "role_secret",
                data = handshakeBodyData
            };

            var handshakePdu = new HandshakePdu
            {
                action = "auth/handshake",
                body = handshakeBody
            };
            */
            var handshakePdu = new HandshakePdu
            {
                action = "auth/handshake",
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

            // Send authentication message
        }

        public async Task Publish(string str)
        {
        }
    }
}

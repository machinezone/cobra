//
// CobraConnection.cs
// Author: Benjamin Sergeant
// Copyright (c) 2020 Machine Zone, Inc. All rights reserved.
//
using System;
using System.Threading;
using System.Threading.Tasks;

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

    public class CobraConnection
    {
        public async Task Connect(CobraConfig config,
                                  Action<string> logger,
                                  CancellationToken cancellationToken)
        {
        }

        public async Task Publish(string str)
        {
        }
    }
}

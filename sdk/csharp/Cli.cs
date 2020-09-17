//
// Cli.cs
// Author: Benjamin Sergeant
// Copyright (c) 2020 Machine Zone, Inc. All rights reserved.
//

using System;
using System.Threading;
using System.Threading.Tasks;
using Cobra;


public class CobraCli
{
    public static async Task Main()
    {
        var cobraConfig = new CobraConfig
        {
            //
            // uncomment this to test against a local cobra server
            // endpoint = "ws://localhost:8765",
            endpoint = "wss://bavarde.jeanserge.com",
            //
            appkey = "_pubsub",
            rolename = "pubsub",
            rolesecret = "ccc02DE4Ed8CAB9aEfC8De3e13BfBE5E",
        };

        var cancellationToken = CancellationToken.None;

        var cobraConnection = new CobraConnection(cobraConfig);
        await cobraConnection.Connect(cancellationToken);

        string line;
        while ((line = Console.ReadLine()) != null)
        {
            // Console.WriteLine(line);
            await cobraConnection.Publish(line);
        }
    }
}

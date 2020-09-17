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
        Action<string> logger = (msg) =>
        {
            Console.WriteLine(msg);
        };

        var cobraConfig = new CobraConfig
        {
            //
            // uncomment this to test against a local cobra server
            endpoint = "ws://localhost:8765",
            // endpoint = "wss://bavarde.jeanserge.com"
            //
            appkey = "blah",
            rolename = "foo",
            rolesecret = "bar",
        };

        var cancellationToken = CancellationToken.None;

        var cobraConnection = new CobraConnection();
        await cobraConnection.Connect(cobraConfig, logger, cancellationToken);

        string line;
        while ((line = Console.ReadLine()) != null)
        {
            Console.WriteLine(line);
        }
    }
}


var RTMManager = require('./rtm_manager_cobra')
var Throttler = require('./throttle')
var ArgumentParser = require('argparse').ArgumentParser


class Subscriber {
  constructor(conf) {
    this.conf = conf

    this.throttler = new Throttler(1000)
    this.cnt = 0
  }

  run(channel, filter) {
    this.rtmManager = new RTMManager(this.conf, channel, (msg) => { this.handleMsg(msg) }, filter)
  }

  handleMsg(msg) {
    this.cnt += 1
    if (this.throttler.exceedRate()) return

    console.log(`${this.cnt} messages`)
    // console.log(msg)

    this.cnt = 0
  }
}

var parser = new ArgumentParser({
  version: '0.0.1',
  addHelp:true,
  description: 'Parser for common required cobra properties'
});
parser.addArgument(
  [ '-e', '--endpoint' ],
  {
    help: 'Endpoint',
    required: true
  }
)
parser.addArgument(
  [ '-a', '--appkey' ],
  {
    help: 'Application Key',
    required: true
  }
)
parser.addArgument(
  [ '-n', '--rolename' ],
  {
    help: 'Role Name',
    required: true
  }
)
parser.addArgument(
  [ '-s', '--rolesecret' ],
  {
    help: 'Role Secret',
    required: true
  }
)
parser.addArgument(
  [ '-c', '--channel' ],
  {
    help: 'Channel',
    required: true
  }
)
parser.addArgument(
  [ '-f', '--filter' ],
  {
    help: 'Filter',
    required: false
  }
)

let args = parser.parseArgs();

let config = {
  endpoint: args.endpoint,
  appkey: args.appkey,
  rolename: args.rolename,
  rolesecret: args.rolesecret
}

var subscriber = new Subscriber(config)
subscriber.run(args.channel, args.filter)

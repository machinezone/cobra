
var SatoriClient = require('./cobra_connection')


class RTMManager {
  constructor(conf, channel, handleMsg, filter, subscribe, _) {
    this.handleMsg = handleMsg
    this.filter = filter

    this.channel = channel
    this.stopped = false

    console.log(`endpoint: ${conf.endpoint}`)
    console.log(`appkey: ${conf.appkey}`)
    console.log(`role name: ${conf.rolename}`)
    console.log(`role secret: ${conf.rolesecret}`)

    this.client = new SatoriClient(conf)

    this.client.on('authenticated', (_) => {
      console.log('Authenticated to RTM!')

      if (subscribe == null) {
        subscribe = true
      }

      if (subscribe) {
        this.client.subscribe(this.channel, filter)
      } else {
        console.log('No subscription requested')
      }
    })

    this.client.on('message-received', (data) => {
      this.handleMsg(data)
    })

    this.client.start()
  }

  publish(channel, msg) {
    this.client.publish(channel, msg)
  }

  stop() {
    if (this.stopped) return
    this.stopped = true

    this.client.stop()
  }
}

module.exports = RTMManager
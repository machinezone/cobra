
var CobraClient = require('./cobra_connection')
var { getConf, _ } = require('./conf')


class RTMManager {
  constructor(channel, handleMsg, filter, subscribe, _) {
    this.handleMsg = handleMsg
    this.filter = filter

    let conf = getConf()
    this.channel = channel
    this.stopped = false

    console.log(`endpoint: ${conf.endpoint}`)
    console.log(`appkey: ${conf.appkey}`)
    console.log(`role name: ${conf.rolename}`)
    console.log(`role secret: ${conf.rolesecret}`)

    this.client = new CobraClient(conf)

    this.client.on('authenticated', (_) => {
      console.log('Authenticated to RTM!')

      if (subscribe == null) {
        subscribe = true
      }

      if (subscribe) {
        filter = this.filter || `SELECT * from \`${this.channel}\``
        console.log('rtm filter:', filter)
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

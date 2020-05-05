
var isNode = require('detect-node')
var crypto = require('crypto')

class CobraClient {
  constructor(config) {
    this.url = `${config.endpoint}/v2?appkey=${config.appkey}`
    this.role = config.rolename
    this.secret = config.rolesecret
    this.ws = null
    this.stopped = false

    this.authenticated = false
    this.callbacks = {}
  }

  stop() {
    this.ws.close()
    this.stopped = true
  }

  on(evt, callback) {
    this.callbacks[evt] = callback
  }

  fire(evt, data) {
    this.callbacks[evt](data)
  }

  start() {
    console.log('Starting cobra connection')
    if (isNode) {
      // we need const instead of var, or require will be
      // 'parsed' and that will make WebSocket undefined in a
      // browser context. Weird.
      const WebSocket = require('ws')
      this.ws = new WebSocket(this.url)
    } else {
      this.ws = new WebSocket(this.url)
    }

    this.ws.onopen = (evt) => {
      this.onOpen()
    }
    this.ws.onmessage = (message) => {
      this.onMessage(message)
    }
    this.ws.onclose = (evt) => {
      this.onClose(evt)
    }
    this.ws.onerror = (evt) => {
      this.onError() //
    }
  }

  onClose(evt) {
    if (this.stopped) return
    this.stopped = true

    console.log('closing', evt)
    // Restart in 1 second
    setTimeout(() => {
      this.start()
    }, 1000)
  }

  onError() {
    console.log('error...')
  }

  onOpen() {
    let request = {
      'action':'auth/handshake',
      'body': {
        'method':'role_secret',
        'data':{
          'role': this.role
        }
      }
    }
    this.send(request)
  }

  send(msg) {
    // if (this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(msg))
    //}
  }

  onMessage(message) {
    let pdu = JSON.parse(message.data)
    let action = pdu.action

    // FIXME: error handling
    if (action == 'auth/handshake/ok') {
      this.handleHandShake(pdu)
    } else if (action == 'auth/authenticate/ok') {
      this.authenticated = true
      this.fire('authenticated', null)
    } else if (action == 'rtm/subscription/data') {
      this.handleSubscriptionData(pdu)
    }
  }

  handleSubscriptionData(pdu) {
    let messages = pdu.body.messages
    for (let msg of messages) {
      this.fire('message-received', msg)
    }
  }

  handleHandShake(pdu) {
    var nonce = pdu.body.data.nonce
    this.authenticate(nonce)
  }

  // can't get satori-c-sdk implementation to work
  hmacMd5(secret, nonce) {
    const hmac = crypto.createHmac('md5', secret)
    hmac.update(nonce)
    let h = hmac.digest('base64')

    // console.log(`hmac(${secret}, ${nonce}) => ${h}`)
    return h
  }

  authenticate(nonce) {
    var request = {
      action: 'auth/authenticate',
      body: {
        method: 'role_secret',
        credentials: {
          hash: this.hmacMd5(this.secret, nonce)
        }
      }
    }
    this.send(request)
  }

  subscribe(channel, filter) {
    console.log(`Subscribing to ${channel} with filter: ${filter}`)
    var pdu = {
      action: 'rtm/subscribe',
      body: {
        channel: channel
      }
    }
    if (filter != null) {
      pdu.body.filter = filter
    }

    this.send(pdu)
  }

  publish(channel, msg) {
    var pdu = {
      action: 'rtm/publish',
      body: {
        channel: channel,
        message: msg
      }
    }

    this.send(pdu)
  }
}

module.exports = CobraClient

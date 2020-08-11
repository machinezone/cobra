
var RTMManager = require('./rtm_manager_cobra')
var truncate = require('./truncate')


class BavardeChat {
  constructor(app) {
    this.app = app
    this.search = null

    this.messages = []
    this.chatMessages = []

    this.chatOk = 0
    this.chatKo = 0
    this.chatSummary = 'na / na / Error rate na'
  }

  start(query) {
    this.elem = document.getElementsByTagName('body')[0]
    this.avgDiv = 'avg_div'
    this.totalDiv = 'total_div'

    this.navbarDiv = this.app.navBar.elemId
    this.render()
    this.app.navBar.render()

    let channel = 'lobby'
    let filter = null

    this.rtmManager = new RTMManager(channel, (msg) => {
      this.handleMsg(msg)
    }, filter)
  }

  handleMsg(msg) {

    this.messages.unshift(msg)  // insert at front of array
    if (this.messages.length > 100) { // keep that list size bounded
      this.messages.length = 100      // or it can make a browser unresponsive
    }

    this.update()
  }

  update() {
    this.updateMessages()
  }

  updateMessages() {
    var div = document.getElementById('events_div')

    var s = `
    <h2>Messages</h2>

    <table class="table-condensed table-striped"">
    <tr>
      <th>User</th>
      <th>Message</th>
    </tr>`

    for (let msg of this.messages) {
      s += '<tr>'

      // user
      s += `<td>${msg.data.user}
            </td>`

      // text
      s += `<td>
            ${msg.data.text}
            </td>`

      s += '</tr>'
    }

    s += '</table>'
    div.innerHTML = s
  }

  render() {
    this.elem.innerHTML = `

      <div id="${this.navbarDiv}"> </div>

      <div class="container-fluid">
          <div class="row">
              <br />
              <div class="col-md-6" id="search_id"> </div>
          </div>

          <div class="row">
              <div class="col-md-8" id="events_div"> </div>
              <div class="col-md-4" id="chat_div"> </div>
          </div>

      </div> <!-- container-fluid -->
    `
  }
}

module.exports = BavardeChat

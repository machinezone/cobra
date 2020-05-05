
var Navigo = require('navigo')

var BavardeChat = require('./chat')
var BavardeAbout = require('./about')
var insertBavardeCss = require('./insert-bavarde-css')
var NavBar = require('./navbar')
var { getConf, _ } = require('./conf')


class App {
  constructor() {
    insertBavardeCss()

    let root = null
    let useHash = true // Defaults to: false
    let hash = '#!' // Defaults to: '#'
    this.router = new Navigo(root, useHash, hash)

    this.bavardeChat = null
    this.bavardeAbout = null

    let navbarDiv = 'navbar_div'
    this.navBar = new NavBar(navbarDiv)

    let conf = getConf()
  }

  handleDefaultParams(_) {
    // FIXME what is this again ?
    // we use to hide a toolbar here for all pages.
    // This is a global hook
  }

  createAllRoutes() {
    this.router
      .on('/chat/', (params, query) => {
        this.handleDefaultParams(query)
        this.showChatPage(query)
      })
      .resolve()

    this.router
      .on('/about/', (params, query) => {
        this.handleDefaultParams(query)
        this.showAboutPage(query)
      })
      .resolve()

    // default home screen.
    this.router
      .on((params, query) => {
        this.handleDefaultParams(query)
        this.showHomePage(query)
      })
      .resolve()
  }

  logout() {
    // FIXME
  }

  showHomePage(query) {
    this.showAboutPage(query)
  }

  showChatPage(query) {
    this.stop()
    this.navBar.name = 'about'

    if (this.bavardeAbout == null) {
      this.bavardeAbout = new BavardeAbout(this)
    }
    this.bavardeAbout.start(query)
  }

  showAboutPage(query) {
    this.stop()
    this.navBar.name = 'about'

    if (this.bavardeChat == null) {
      this.bavardeChat = new BavardeChat(this)
    }
    this.bavardeChat.start(query)
  }

  start() {
    this.createAllRoutes()
  }

  stop() {
    if (this.bavardeChat != null) {
      this.bavardeChat.rtmManager.stop()
    }
  }
}

let app = new App()
app.start()

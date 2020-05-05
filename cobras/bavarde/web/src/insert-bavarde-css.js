//
// Create a link to the version of boostrap we are using.
// It's easier to use a CDN version than it is to embed it
//

var $ = require('jquery')
window.jQuery = $

function makeStyleElement(url) {
  var link = document.createElement('link')
  link.type = 'text/css'
  link.rel = 'stylesheet'
  link.href = url

  return link
}

function makeScriptElement(url) {
  var script = document.createElement('script')
  script.src = url

  return script
}

function insertBavardeCss() {
  var head = document.getElementsByTagName('head')[0]
  var url = ''

  // Boostrap CSS
  url = 'https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css'
  head.appendChild(makeStyleElement(url))

  // Boostrap JS
  url = 'https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js'
  head.appendChild(makeScriptElement(url))
}

module.exports = insertBavardeCss

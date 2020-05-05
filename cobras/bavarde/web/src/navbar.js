

class NavBar {
  constructor(elemId) {
    this.elemId = elemId
    this.name = null
    this.hide = false
  }

  setActiveLink(name, enable) {
    let elemId = `${name}_link_div`
    let elem = document.getElementById(elemId)

    if (enable) {
      elem.classList.add('active')
    } else {
      elem.classList.remove('active')
    }
  }

  activateLink(name) {
    this.disableAllActiveLinks()
    this.setActiveLink(name, true)
  }

  disableAllActiveLinks() {
    for (let link of this.links) {
      this.setActiveLink(link, false)
    }
  }

  makeLinks(data) {
    let navs = ''

    for (let tokens of data) {
      let tok_0 = tokens[0]
      let tok_1 = tokens[1]
      let tok_2 = tokens[2]

      // update links list
      this.links.push(tok_0)

      //
      // Generate something like that
      // <li id="runs_link_div"><a href="#!/">Runs</a></li>
      //
      navs += `<li id="${tok_0}_link_div">
                   <a href="#!/${tok_1}">${tok_2}
                   </a>
               </li>\n`
    }

    return navs
  }

  render() {
    let elem = document.getElementById(this.elemId)

    if (this.hide) {
      elem.innerHTML = ''
      return
    }

    this.links = []

    let leftData = [
      ['chat', 'chat', 'Chat'],
    ]
    let leftNavs = this.makeLinks(leftData)

    let rightData = [
      ['logout', 'logout', 'Logout'],
      ['about', 'about', 'About'],
    ]
    let rightNavs = this.makeLinks(rightData)

    for (let tokens of leftData) {
      let tok_0 = tokens[0]
    }

    if (elem == null) return

    elem.innerHTML = `
      <nav class="navbar navbar-default" style="margin-bottom: 0;">
        <div class="container-fluid">
          <!-- Brand and toggle get grouped for better mobile display -->
          <div class="navbar-header">
            <button type="button"
                    class="navbar-toggle collapsed"
                    data-toggle="collapse"
                    data-target="#bs-example-navbar-collapse-1"
                    aria-expanded="false">
              <span class="sr-only">Toggle navigation</span>
              <span class="icon-bar"></span>
              <span class="icon-bar"></span>
              <span class="icon-bar"></span>
            </button>
            <a class="navbar-brand" href="#!/">Bavarde</a>
          </div>

          <div class="collapse navbar-collapse" id="bs-example-navbar-collapse-1">
            <ul class="nav navbar-nav">
              ${leftNavs}
            </ul>
            <ul class="nav navbar-nav navbar-right">
              ${rightNavs}
            </ul>
          </div><!-- /.navbar-collapse -->

        </div><!-- /.container-fluid -->
      </nav>
      `
    this.activateLink(this.name)
  }
}

module.exports = NavBar

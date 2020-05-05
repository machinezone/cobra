
class BavardeAbout {
  constructor(app) {
    this.app = app
  }

  start(_) {
    this.elem = document.getElementsByTagName('body')[0]

    this.navbarDiv = this.app.navBar.elemId
    this.render()
    this.app.navBar.render()
  }

  render() {
    this.elem.innerHTML = `

      <div id="${this.navbarDiv}"> </div>

      <div class="container-fluid">
          <div class="row">
            <div class="col-md-4">
              <h2>How does this work?</h2>
              <p>This chat goes through cobra.
              </p>
            </div>

            <div class="col-md-8">
              <img src="https://2r4s9p1yi1fa2jd7j43zph8r-wpengine.netdna-ssl.com/files/2017/05/black-box.png" style="width:600px;height:151;">
            </div>
          </div>
            </div>
          </div>

      </div> <!-- container-fluid -->
    `
  }
}


module.exports = BavardeAbout

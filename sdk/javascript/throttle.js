
class Throttler {
  constructor(rate) {
    this.last = new Date()
    this.rate = rate || 100
  }

  exceedRate() {
    let now = new Date()

    if ((now - this.last) < this.rate) {
      return true
    } else {
      this.last = now
      return false
    }
  }
}

module.exports = Throttler

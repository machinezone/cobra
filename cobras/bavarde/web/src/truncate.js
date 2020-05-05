
function truncate(s, maxSize) {
  if (s.length < maxSize) return s
  else return s.substring(0, maxSize) + '...'
}

module.exports = truncate

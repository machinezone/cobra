
var getDefaultConfName = require('./default_conf')

let confs = {
  jeanserge: {
    endpoint: 'wss://jeanserge.com',
    appkey: '_pubsub',
    channel: 'lobby',
    rolename: 'pubsub',
    rolesecret: 'ccc02DE4Ed8CAB9aEfC8De3e13BfBE5E',
  },
}

let confName = getDefaultConfName()

function setConfName(name) {
  confName = name
}

function getConfName() {
  return confName
}

function getConf() {
  let confName = getConfName()
  return confs[confName]
}

module.exports = { getConf, setConfName, getConfName }

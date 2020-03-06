#
# Basic stuff
#
export PS1="%c$ "
bindkey -v
ulimit -n 1024

autoload -U compinit
compinit
autoload zmv

# auto stuff ? (does it works ?)
setopt auto_cd

# history
export HISTSIZE=1000000
export SAVEHIST=$HISTSIZE

unset EQUALS

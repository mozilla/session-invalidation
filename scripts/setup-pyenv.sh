#! /usr/bin/env sh

pyenv install --skip-existing 3.8.2
if [ ! -d $HOME/.pyenv/versions/session-invalidation ]; then
  pyenv virtualenv 3.8.2 session-invalidation;
fi
pyenv local session-invalidation

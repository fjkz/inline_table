#!/usr/bin/env bash

set -eux -o pipefail
cd $(dirname ${BASH_SOURCE:-$0})/..

python3 --version >&2
python3 setup.py test
pycodestyle *.py
pydocstyle *.py
pyflakes *.py

rst2html5.py README.rst README.html

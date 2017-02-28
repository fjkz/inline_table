#!/usr/bin/env bash

set -eux
cd $(dirname ${BASH_SOURCE:-$0})/..

python2 --version >&2
python2 setup.py test

python3 --version >&2
python3 setup.py test

pep8 *.py

pep257 *.py

rst2html5.py README.rst README.html

export PYTHONPATH=${PWD}
cd doc
make html

#!/usr/bin/env bash

python3 setup.py install --optimize=1

install -Dm 644 -t "/usr/share/pixmaps" nwg-readme-browser.svg
install -Dm 644 -t "/usr/share/applications" nwg-readme-browser.desktop
install -Dm 644 -t "/usr/share/licenses/nwg-readme-browser" LICENSE
install -Dm 644 -t "/usr/share/doc/nwg-readme-browser" README.md
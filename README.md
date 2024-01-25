# nwg-readme-browser

This program is a part of the [nwg-shell](https://nwg-piotr.github.io/nwg-shell) project.

This program searches the `/usr/share/doc` path for `README.*` files and creates their preview in WebKit2.WebView. 
It supports .md, .rst, .html and plain text. It does not support .pdf format. 

<img src="https://github.com/nwg-piotr/nwg-readme-browser/assets/20579136/084e05aa-5273-41c4-9fbd-c1d8450d11c7" width=600>

Instead of all, it may only display the README.* files associated to packages enumerated in the config file, or the
internally defined set (nwg-shell-related).

```text
$ nwg-readme-browser -h
usage: nwg-readme-browser [-h] [-v] [-i] [-c]

options:
  -h, --help      show this help message and exit
  -v, --version   show program's version number and exit
  -i, --internal  only list Internally defined packages (nwg-shell components)
  -c, --config    only list packages enumerated in the `/home/piotr/.config/nwg-icon-
                  browser/config.json` file
```

# nwg-readme-browser

This program searches the `/usr/share/doc` path for `README.*` files and creates their preview in WebKit2.WebView. 
It supports .md, .rst, .html and plain text. It does not support .pdf format. 

![image](https://github.com/nwg-piotr/nwg-readme-browser/assets/20579136/4fe48b9e-e790-49cc-beeb-0a67bb24fe2c)

Instead of all, it may display only the README.* files associated to packages enumerated in the config file.

```text
❯ nwg-readme-browser -h
usage: nwg-readme-browser [-h] [-v] [-c]

options:
  -h, --help     show this help message and exit
  -v, --version  show program's version number and exit
  -c, --config   list only packages defined in Config file
```

Work in progress. More info coming soon.

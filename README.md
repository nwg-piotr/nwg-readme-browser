# nwg-readme-browser

This program is a part of the [nwg-shell](https://nwg-piotr.github.io/nwg-shell) project.

Nwg-readme-browser was conceived as [rtfm](https://en.wikipedia.org/wiki/RTFM) with a graphical user interface. 
It searches the `/usr/share/doc` path for `README.*` files, and allows to preview in WebKit2.WebView. 
It supports `.md`, `.rst`, `.html` and plain text. It <u>does not support .pdf</u> format. 

<a href="https://github.com/nwg-piotr/nwg-readme-browser/assets/20579136/084e05aa-5273-41c4-9fbd-c1d8450d11c7"><img src="https://github.com/nwg-piotr/nwg-readme-browser/assets/20579136/084e05aa-5273-41c4-9fbd-c1d8450d11c7" width=640></a>

Instead of all README.* files, the program may only display those associated to packages enumerated in the config file, 
or the internally defined set (nwg-shell-related).

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

## Configuration

The config file is placed in `$XDG_CONFIG_HOME/.config/nwg-readme-browser/config.json`. By default, it looks as below:

```json
{
  "doc-dir": "/usr/share/doc",
  "default-zoom": 1.0,
  "packages": [
    "nwg-package-1",
    "nwg-package-2",
    "(...)"
  ]
}
```

- `"doc-dir"`: path where we look for directories with README files
- `"default-zoom"`: default zoom level when the program starts
- `"packages"`: list of packages that the program running with the `--config` argument will look for

You may preinstall your own config file. Otherwise, it will be created on first run, on the basis of `--internal` defaults.   
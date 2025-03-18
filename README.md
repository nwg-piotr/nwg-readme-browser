<img src="https://github.com/nwg-piotr/nwg-readme-browser/assets/20579136/c150586c-1880-4d69-9ab9-2f9136ff6c37" width="90" style="margin-right:10px" align=left alt="nwg-shell logo">
<H1>nwg-readme-browser</H1><br>

This program is a part of the [nwg-shell](https://nwg-piotr.github.io/nwg-shell) project.

**Nwg-readme-browser** was conceived as [rtfm](https://en.wikipedia.org/wiki/RTFM) with a graphical user interface. 
It searches the `/usr/share/doc` path for `README.*` files, and displays them in WebKit2.WebView. 
It supports `.md`, `.rst`, `.html` and plain text. It does not support `.pdf` format. Although the program was written 
with nwg-shell for [sway](https://github.com/swaywm/sway) and [Hyprland](https://github.com/hyprwm/Hyprland) in mind, it may also be used standalone.

<a href="https://github.com/nwg-piotr/nwg-readme-browser/assets/20579136/56d94b95-d765-4e1a-9489-26e1ac4f9a19"><img src="https://github.com/nwg-piotr/nwg-readme-browser/assets/20579136/56d94b95-d765-4e1a-9489-26e1ac4f9a19" width=640></a>

## Usage

Use the side menu to select the README file to preview. Basic navigation is provided by toolbar at the top of the side 
bar. Below it there is a search entry that allows you to filter the file list.

### Arguments

Instead of all README.* files, the program may only display those that belong to packages enumerated in the config file, 
or the internally defined set (nwg-shell-related). Use a command line argument for this.

```text
$ nwg-readme-browser -h
usage: nwg-readme-browser [-h] [-v] [-i] [-c]

options:
  -h, --help      show this help message and exit
  -v, --version   show program's version number and exit
  -i, --internal  only list Internally defined packages (nwg-shell components)
  -c, --config    only list packages enumerated in the `~/.config/nwg-icon-
                  browser/config.json` file
```

## Installation

[![Packaging status](https://repology.org/badge/vertical-allrepos/nwg-readme-browser.svg)](https://repology.org/project/nwg-readme-browser/versions)

Clone the [repository](https://github.com/nwg-piotr/nwg-readme-browser) and run the `install.sh` script.

### Dependencies

- gtk3
- python
- python-docutils
- python-gobject
- python-markdown2
- webkit2gtk
- python-build (make)
- python-installer (make)
- python-wheel (make)
- python-setuptools (make)

## Configuration

The config file is placed in `~/.config/nwg-readme-browser/config.json` (unless you set the `$XDG_CONFIG_HOME` variable
a different way). By default, it looks as below:

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

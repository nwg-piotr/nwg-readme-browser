#!/usr/bin/env python3

"""
nwg-shell README.md browser
Copyright (c) 2024 Piotr Miller
e-mail: nwg.piotr@gmail.com
Project: https://github.com/nwg-piotr/nwg-shell
Repository: https://github.com/nwg-piotr/nwg-readme-browser
License: MIT
"""
import argparse
import json
import os.path

import markdown2 as markdown
import sys

import gi

gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')

from gi.repository import Gtk, Gdk, WebKit2

webview = None
search_entry = None
config = None

try:
    from .__about__ import __version__
except ImportError:
    __version__ = "unknown"

xdg_config_home = os.getenv('XDG_CONFIG_HOME')
config_home = xdg_config_home if xdg_config_home else os.path.join(os.getenv("HOME"), ".config")
config_dir = os.path.join(config_home, "nwg-icon-browser")
if not os.path.isdir(config_dir):
    os.makedirs(config_dir, exist_ok=True)
config_file = os.path.join(config_dir, "config.json")


def load_json(path):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print("Error loading json: {}".format(e))
        return {}


def save_json(src_dict, path):
    try:
        with open(path, 'w') as f:
            json.dump(src_dict, f, indent=2)
        return "ok"
    except Exception as e:
        return e


# load config, create if it doesn't yet exist
config = load_json(config_file)
DEFAULTS = {
    "doc-dir": "/usr/share/doc",
    "packages": [
        "nwg-readme-browser",
        "nwg-shell",
        "nwg-shell-config",
        "nwg-hello",
        "nwg-icon-browser"
    ]
}  # t.b.c.
for key in DEFAULTS:
    if key not in config:
        config[key] = DEFAULTS[key]
if not os.path.isfile(config_file):
    save_json(config, config_file)


def md2html(markdown_text):
    html_content = markdown.markdown(markdown_text, extras=['fenced-code-blocks'])
    return html_content


def handle_keyboard(win, event):
    if event.type == Gdk.EventType.KEY_RELEASE and event.keyval == Gdk.KEY_Escape:
        if search_entry.get_text():
            search_entry.set_text("")
        else:
            win.destroy()


def on_forward_btn(*args):
    if webview.can_go_forward():
        webview.go_forward()


def on_back_btn(*args):
    if webview.can_go_back():
        webview.go_back()


def on_button_release(btn, event):
    if event.button == 9:
        on_forward_btn()
    elif event.button == 8:
        on_back_btn()


class ButtonBar(Gtk.Box):
    def __init__(self):
        Gtk.Box.__init__(self)
        self.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.set_spacing(6)

        btn = Gtk.Button.new_from_icon_name("application-exit", Gtk.IconSize.MENU)
        btn.connect("clicked", Gtk.main_quit)
        self.pack_start(btn, False, False, 0)

        btn = Gtk.Button.new_from_icon_name("go-previous", Gtk.IconSize.MENU)
        btn.connect("clicked", on_back_btn)
        self.pack_start(btn, False, False, 0)

        btn = Gtk.Button.new_from_icon_name("go-next", Gtk.IconSize.MENU)
        btn.connect("clicked", on_forward_btn)
        self.pack_start(btn, False, False, 0)


def on_enter_notify_event(widget, event):
    # highlight item
    widget.set_state_flags(Gtk.StateFlags.DROP_ACTIVE, clear=False)
    widget.set_state_flags(Gtk.StateFlags.SELECTED, clear=False)


def on_leave_notify_event(widget, event):
    # clear highlight
    widget.unset_state_flags(Gtk.StateFlags.DROP_ACTIVE)
    widget.unset_state_flags(Gtk.StateFlags.SELECTED)


class FlowboxItem(Gtk.Box):
    def __init__(self, package_name):
        Gtk.EventBox.__init__(self, orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        eb = Gtk.EventBox()
        self.pack_start(eb, True, True, 0)
        label = Gtk.Label.new(package_name)
        label.set_property("halign", Gtk.Align.START)
        eb.add(label)

        eb.connect('enter-notify-event', on_enter_notify_event)
        eb.connect('leave-notify-event', on_leave_notify_event)


def on_child_activated(fb, child):
    # on flowbox item clicked
    package_name = child.get_name()
    # file_path = f"/usr/share/doc/{package_name}/README.md"
    file_path = readme_path(package_name)
    load_markdown_file(file_path)


class SearchEntry(Gtk.SearchEntry):
    def __init_(self):
        Gtk.SearchEntry.__init__(self)
        self.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, "edit-clear-symbolic")
        self.set_property("hexpand", True)
        self.set_property("margin", 12)
        self.set_size_request(700, 0)
        # self.connect('search_changed', flowbox_filter)


class FileMenu(Gtk.ScrolledWindow):
    def __init__(self, readme_paths):
        Gtk.ScrolledWindow.__init__(self)
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.set_propagate_natural_height(True)

        self.flowbox = Gtk.FlowBox()
        # flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.flowbox.connect("child-activated", on_child_activated)
        self.flowbox.set_valign(Gtk.Align.START)
        self.flowbox.set_max_children_per_line(1)
        self.add(self.flowbox)

        for name in readme_paths:
            item = FlowboxItem(name)
            child = Gtk.FlowBoxChild()
            child.set_name(name)
            child.add(item)
            self.flowbox.add(child)

    def flowbox_filter(self, _search_box):
        # filter flowbox items visibility by search_entry content
        def filter_func(fb_child, _text):
            if _text in fb_child.get_name():
                return True
            else:
                return False

        text = search_entry.get_text()
        self.flowbox.set_filter_func(filter_func, text)


def load_markdown_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            markdown_content = file.read()
            render_markdown(markdown_content)
    except FileNotFoundError:
        print(f"Error: File not found - {file_path}")


def render_markdown(markdown_content, md=True):
    html_content = f"<html><body>{md2html(markdown_content)}</body></html>"
    webview.load_html(html_content, 'file:///')


def readme_path(name):
    if isinstance(name, str) and name:
        if os.path.isfile(f"/usr/share/doc/{name}/README.md"):
            return f"/usr/share/doc/{name}/README.md"
        elif os.path.isfile(f"/usr/share/doc/{name}/README"):
            return f"/usr/share/doc/{name}/README"
        elif os.path.isfile(f"/usr/share/doc/{name}/README.rst"):
            return f"/usr/share/doc/{name}/README.rst"

    return ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--version", action="version",
                        version=f"%(prog)s version {__version__}")
    parser.add_argument("-c", "--config", action="store_true",
                        help="list only packages defined in Config file")
    args = parser.parse_args()

    packages = config["packages"] if args.config else sorted(os.listdir("/usr/share/doc"))

    # find README.md files that actually exist
    readme_package_names = []
    for name in packages:
        if readme_path(name):
            readme_package_names.append(name)

    win = Gtk.Window.new(Gtk.WindowType.TOPLEVEL)
    win.set_title("nwg README")
    # main wrapper
    hbox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, spacing=0)
    hbox.set_property("margin", 6)
    win.add(hbox)

    # Left column
    col_left = Gtk.Box.new(Gtk.Orientation.VERTICAL, spacing=0)
    hbox.pack_start(col_left, False, False, 0)

    # navigation buttons
    btn_bar = ButtonBar()
    col_left.pack_start(btn_bar, False, False, 6)

    global search_entry
    search_entry = SearchEntry()
    col_left.pack_start(search_entry, False, False, 6)

    # package names list
    file_menu = FileMenu(readme_package_names)
    search_entry.connect('search_changed', file_menu.flowbox_filter)
    col_left.pack_start(file_menu, False, False, 6)

    global webview
    webview = WebKit2.WebView()
    webview.connect("button-release-event", on_button_release)
    scrolled = Gtk.ScrolledWindow()
    scrolled.add(webview)

    # Right column
    hbox.pack_start(scrolled, True, True, 6)

    if len(readme_package_names) > 0:
        file_path = readme_path(readme_package_names[0])
        load_markdown_file(file_path)

    win.connect("destroy", Gtk.main_quit)
    win.connect("key-release-event", handle_keyboard)
    win.show_all()

    search_entry.grab_focus()

    Gtk.main()


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3

"""
nwg-shell README.md browser
Copyright (c) 2024-2025 Piotr Miller
e-mail: nwg.piotr@gmail.com
Project: https://github.com/nwg-piotr/nwg-shell
Repository: https://github.com/nwg-piotr/nwg-readme-browser
License: MIT
Supported formats: .md, .rst, html, plain text
Unsupported formats: .pdf
"""
import argparse
import json
import os.path
import subprocess

import markdown2 as markdown
import sys

import gi

gi.require_version('Gtk', '3.0')
try:
    gi.require_version('WebKit2', '4.1')
except ValueError:
    gi.require_version('WebKit2', '4.0')

from gi.repository import Gtk, Gdk, GLib, WebKit2
from docutils.core import publish_string

webview = None
search_entry = None
status_label = None
config = None
readme_package_names = []

try:
    from .__about__ import __version__
except ImportError:
    __version__ = "unknown"

# Config file & dictionary
xdg_config_home = os.getenv('XDG_CONFIG_HOME')
config_home = xdg_config_home if xdg_config_home else os.path.join(os.getenv("HOME"), ".config")
config_dir = os.path.join(config_home, "nwg-readme-browser")
# create config directory if not found
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
    "default-zoom": 1.0,
    "packages": [
        "nwg-shell",
        "nwg-shell-config",
        "nwg-panel",
        "nwg-drawer",
        "nwg-dock",
        "nwg-menu",
        "nwg-look",
        "nwg-displays",
        "azote",
        "nwg-bar",
        "nwg-clipman",
        "nwg-icon-picker",
        "nwg-readme-browser",
        "autotiling",
        "gopsuinfo",
        "nwg-hello",
        "typobuster",
        "sddm-sugar-candy-nwg",
        "swaync",
        "gtklock",
        "swaylock",
        "swayidle",
        "swayimg",
        "nwg-shell-wallpapers"
    ]
}
key_missing = False
for key in DEFAULTS:
    if key not in config:
        config[key] = DEFAULTS[key]
        key_missing = True
# we only create config file, if not found/preinstalled; we also need to save it if some key is missing
if not os.path.isfile(config_file) or key_missing:
    save_json(config, config_file)

last_file_path = home_path = ""


def detect_gtk_theme_preference():
    """
    Detect GTK theme preference (light/dark) from system settings.
    Returns True if dark theme is preferred, False for light theme.
    """
    try:
        # Method 1: Check gsettings for gtk-theme
        result = subprocess.run(['gsettings', 'get', 'org.gnome.desktop.interface', 'gtk-theme'],
                                capture_output=True, text=True, timeout=3)
        if result.returncode == 0:
            theme_name = result.stdout.strip().strip("'\"")
            # Check if theme name suggests dark mode
            if theme_name and ('dark' in theme_name.lower() or '-dark' in theme_name.lower()):
                return True

        # Method 2: Check gsettings for color-scheme (newer GNOME versions)
        result = subprocess.run(['gsettings', 'get', 'org.gnome.desktop.interface', 'color-scheme'],
                                capture_output=True, text=True, timeout=3)
        if result.returncode == 0:
            color_scheme = result.stdout.strip().strip("'\"")
            if color_scheme == 'prefer-dark':
                return True
            elif color_scheme == 'prefer-light':
                return False

        # Method 3: Check GTK Settings for gtk-application-prefer-dark-theme
        settings = Gtk.Settings.get_default()
        if settings:
            prefer_dark = settings.get_property("gtk-application-prefer-dark-theme")
            return prefer_dark

    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError,
            AttributeError, ValueError):
        # Fallback: assume light theme if detection fails
        pass

    return False


# Convert markdown to html
def md2html(markdown_text):
    html_content = markdown.markdown(markdown_text, extras=['fenced-code-blocks'])
    return html_content


# which README to download as start page
def home_file():
    file_path = ""
    if len(readme_package_names) > 0:
        if "nwg-shell" in readme_package_names:
            file_path = readme_path("nwg-shell")
        elif "nwg-readme-browser" in readme_package_names:
            file_path = readme_path("nwg-readme-browser")
        else:
            file_path = readme_path(readme_package_names[0])

    return file_path


def go_home(*args):
    home = home_file()
    if home:
        if load_readme_file(home):
            update_status_label()


# GUI controls
# on Esc clear search entry if not empty, else terminate
def handle_keyboard(win, event):
    if event.type == Gdk.EventType.KEY_RELEASE:
        if event.keyval == Gdk.KEY_Escape:
            if search_entry.get_text():
                search_entry.set_text("")
            else:
                win.destroy()
        elif event.keyval == Gdk.KEY_F5 and webview.get_uri() and webview.get_uri().startswith("http"):
            if event.state & Gdk.ModifierType.CONTROL_MASK:
                webview.reload_bypass_cache()
            else:
                webview.reload()
        elif event.keyval == Gdk.KEY_minus or event.keyval == Gdk.KEY_underscore and event.state & Gdk.ModifierType.CONTROL_MASK:
            on_zoom_btn(None, action="out")
        elif event.keyval == Gdk.KEY_equal or event.keyval == Gdk.KEY_plus and event.state & Gdk.ModifierType.CONTROL_MASK:
            on_zoom_btn(None, action="in")


# on toolbar buttons
def on_forward_btn(*args):
    if webview.can_go_forward():
        webview.go_forward()


def on_back_btn(*args):
    if webview.can_go_back():
        webview.go_back()
    else:
        if load_readme_file(last_file_path):
            update_status_label()


def on_zoom_btn(btn, action=""):
    level = webview.get_zoom_level()
    if action == "in":
        if level < 2.0:
            webview.set_zoom_level(level + 0.1)
        else:
            webview.set_zoom_level(2.0)
    elif action == "original":
        webview.set_zoom_level(1.0)
    elif action == "out":
        if level > 0.2:
            webview.set_zoom_level(level - 0.1)
        else:
            webview.set_zoom_level(0.1)


# go back / forward on mouse side buttons
def on_button_release(btn, event):
    if event.button == 9:
        on_forward_btn()
    elif event.button == 8:
        on_back_btn()


# Toolbar
class ButtonBar(Gtk.Box):
    def __init__(self):
        Gtk.Box.__init__(self)
        self.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.set_spacing(3)

        btn = Gtk.Button.new_from_icon_name("go-home", Gtk.IconSize.MENU)
        btn.connect("clicked", go_home)
        self.pack_start(btn, False, False, 0)

        btn = Gtk.Button.new_from_icon_name("go-previous", Gtk.IconSize.MENU)
        btn.connect("clicked", on_back_btn)
        self.pack_start(btn, False, False, 0)

        btn = Gtk.Button.new_from_icon_name("go-next", Gtk.IconSize.MENU)
        btn.connect("clicked", on_forward_btn)
        self.pack_start(btn, False, False, 0)

        btn = Gtk.Button.new_from_icon_name("zoom-out", Gtk.IconSize.MENU)
        btn.connect("clicked", on_zoom_btn, "out")
        self.pack_start(btn, False, False, 0)

        btn = Gtk.Button.new_from_icon_name("zoom-original", Gtk.IconSize.MENU)
        btn.connect("clicked", on_zoom_btn, "original")
        self.pack_start(btn, False, False, 0)

        btn = Gtk.Button.new_from_icon_name("zoom-in", Gtk.IconSize.MENU)
        btn.connect("clicked", on_zoom_btn, "in")
        self.pack_start(btn, False, False, 0)

        btn = Gtk.Button.new_from_icon_name("application-exit", Gtk.IconSize.MENU)
        btn.connect("clicked", Gtk.main_quit)
        self.pack_start(btn, False, False, 0)


def on_enter_notify_event(widget, event):
    # highlight pointed item
    widget.set_state_flags(Gtk.StateFlags.DROP_ACTIVE, clear=False)
    widget.set_state_flags(Gtk.StateFlags.SELECTED, clear=False)


def on_leave_notify_event(widget, event):
    # clear highlight
    widget.unset_state_flags(Gtk.StateFlags.DROP_ACTIVE)
    widget.unset_state_flags(Gtk.StateFlags.SELECTED)


# Side menu
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
    webview.load_uri("about:blank")  # clear history
    file_path = readme_path(package_name)
    global last_file_path, last_package_name
    last_file_path = file_path
    last_package_name = package_name

    if load_readme_file(file_path):
        update_status_label()


class FileMenu(Gtk.ScrolledWindow):
    def __init__(self, readme_paths):
        Gtk.ScrolledWindow.__init__(self)
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.set_propagate_natural_height(True)

        self.flowbox = Gtk.FlowBox()
        self.flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
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


# Search entry
class SearchEntry(Gtk.SearchEntry):
    def __init_(self):
        Gtk.SearchEntry.__init__(self)
        self.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, "edit-clear-symbolic")
        self.set_property("hexpand", True)
        self.set_property("margin", 12)
        self.set_size_request(700, 0)


# Load and render picked file
def load_readme_file(file_path):
    global last_file_path
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
            content = file.read()
            if file_path.endswith(".rst"):
                render_rst(content)
            elif file_path.endswith(".html"):
                render_html(content)
            else:
                render_markdown(content)
            last_file_path = file_path
            return True

    except FileNotFoundError:
        print(f"Error: File not found - {file_path}")
        return False


def get_gtk_colors():
    """Extract colors from current GTK theme with modern API"""
    # Method 1: Try to get theme name and parse CSS (most reliable)
    try:
        settings = Gtk.Settings.get_default()
        if settings:
            theme_name = settings.get_property("gtk-theme-name")
            if theme_name and theme_name.lower() != "default":
                theme_colors = parse_theme_css(theme_name)
                if theme_colors:
                    return theme_colors
    except:
        pass

    # Method 2: Use gsettings to get theme info
    try:
        result = subprocess.run(['gsettings', 'get', 'org.gnome.desktop.interface', 'gtk-theme'],
                                capture_output=True, text=True, timeout=3)
        if result.returncode == 0:
            theme_name = result.stdout.strip().strip("'\"")
            if theme_name and theme_name.lower() != "default":
                theme_colors = parse_theme_css(theme_name)
                if theme_colors:
                    return theme_colors
    except:
        pass

    # Method 3: Try to extract colors using CSS provider (modern approach)
    try:
        colors = extract_colors_from_css_provider()
        if colors:
            return colors
    except:
        pass

    # Method 4: Final fallback based on dark/light preference
    prefer_dark = detect_gtk_theme_preference()
    if prefer_dark:
        return {
            'bg': "#2d2d2d",
            'fg': "#ffffff",
            'code_bg': "#1e1e1e",
            'code_fg': "#ffffff",
            'link': "#6bb6ff",
            'border': "#444444"
        }
    else:
        return {
            'bg': "#ffffff",
            'fg': "#000000",
            'code_bg': "#f5f5f5",
            'code_fg': "#000000",
            'link': "#0066cc",
            'border': "#cccccc"
        }


def extract_colors_from_css_provider():
    """Extract colors using modern GTK CSS provider API"""
    try:
        # Create a temporary widget to get style context
        widget = Gtk.Label()
        widget.show()

        # Get the style context
        style_context = widget.get_style_context()

        # Try to get background and foreground colors using CSS properties
        # This is the modern replacement for deprecated get_background_color
        try:
            # Create a CSS provider to query colors
            css_provider = Gtk.CssProvider()
            css_data = b"""
                label {
                    background-color: @theme_bg_color;
                    color: @theme_fg_color;
                }
            """
            css_provider.load_from_data(css_data)

            # Apply to style context
            style_context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_THEME)

            # Get the computed style
            style_context.save()
            style_context.set_state(Gtk.StateFlags.NORMAL)

            # Try to extract colors from the style
            # Note: This is a workaround since direct color extraction is complex
            # We'll fall back to theme parsing which is more reliable

            style_context.restore()

        except Exception:
            pass

        return None  # Fall back to theme parsing

    except Exception:
        return None


def generate_theme_colors(bg_hex, fg_hex):
    """Generate theme colors from base background and foreground"""
    code_bg = adjust_brightness(bg_hex, -0.1)
    link_color = "#4a90e2" if is_light_color(bg_hex) else "#6bb6ff"

    return {
        'bg': bg_hex,
        'fg': fg_hex,
        'code_bg': code_bg,
        'code_fg': fg_hex,
        'link': link_color,
        'border': adjust_brightness(bg_hex, -0.2)
    }


def parse_theme_css(theme_name):
    """Try to parse theme CSS file for actual colors"""
    import re

    # Common theme paths
    theme_paths = [
        f"/usr/share/themes/{theme_name}/gtk-3.0/gtk.css",
        f"/usr/share/themes/{theme_name}/gtk-3.20/gtk.css",
        f"/home/{os.getenv('USER')}/.themes/{theme_name}/gtk-3.0/gtk.css",
        f"/home/{os.getenv('USER')}/.themes/{theme_name}/gtk-3.20/gtk.css",
        f"/home/{os.getenv('USER')}/.local/share/themes/{theme_name}/gtk-3.0/gtk.css"
    ]

    for theme_path in theme_paths:
        if os.path.exists(theme_path):
            try:
                with open(theme_path, 'r') as f:
                    css_content = f.read()

                # Look for GTK named colors (better than generic CSS)
                bg_match = re.search(r'@define-color theme_bg_color\s+([#][0-9a-fA-F]{6})', css_content)
                fg_match = re.search(r'@define-color theme_fg_color\s+([#][0-9a-fA-F]{6})', css_content)
                base_match = re.search(r'@define-color theme_base_color\s+([#][0-9a-fA-F]{6})', css_content)
                text_match = re.search(r'@define-color theme_text_color\s+([#][0-9a-fA-F]{6})', css_content)
                borders_match = re.search(r'@define-color borders\s+([#][0-9a-fA-F]{6})', css_content)

                # Use base_color for content background if available, otherwise theme_bg_color
                bg_color = base_match.group(1) if base_match else (bg_match.group(1) if bg_match else "#ffffff")
                # Use text_color for content text if available, otherwise theme_fg_color
                fg_color = text_match.group(1) if text_match else (fg_match.group(1) if fg_match else "#000000")
                border_color = borders_match.group(1) if borders_match else adjust_brightness(bg_color, -0.2)

                # Generate complementary colors
                code_bg = adjust_brightness(bg_color, -0.05)  # Slightly darker for code blocks
                link_color = "#cd7ebf"  # Use theme's selection color for links (from Otis)

                return {
                    'bg': bg_color,
                    'fg': fg_color,
                    'code_bg': code_bg,
                    'code_fg': fg_color,
                    'link': link_color,
                    'border': border_color
                }
            except:
                continue

    return None


def adjust_brightness(hex_color, factor):
    """Adjust brightness of a hex color"""
    rgb = tuple(int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    rgb = tuple(max(0, min(255, int(c * (1 + factor)))) for c in rgb)
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def is_light_color(hex_color):
    """Check if a color is light or dark"""
    rgb = tuple(int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    luminance = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255
    return luminance > 0.5


def render_markdown(markdown_content):
    colors = get_gtk_colors()
    theme_css = f"""
    <style>
    body {{ 
        background-color: {colors['bg']}; 
        color: {colors['fg']}; 
        font-family: system-ui, -apple-system, sans-serif; 
        line-height: 1.6;
        margin: 20px;
    }}
    pre {{ 
        background-color: {colors['code_bg']}; 
        color: {colors['code_fg']}; 
        padding: 10px; 
        border-radius: 4px; 
        overflow-x: auto;
        border: 1px solid {colors['border']};
    }}
    code {{ 
        background-color: {colors['code_bg']}; 
        color: {colors['code_fg']}; 
        padding: 2px 4px; 
        border-radius: 3px;
    }}
    blockquote {{ 
        border-left: 4px solid {colors['border']}; 
        margin: 0; 
        padding-left: 16px; 
        color: {adjust_brightness(colors['fg'], 0.3)};
    }}
    a {{ color: {colors['link']}; }}
    h1, h2, h3, h4, h5, h6 {{ color: {colors['fg']}; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid {colors['border']}; padding: 8px; }}
    th {{ background-color: {colors['code_bg']}; }}
    </style>
    """

    html_content = f"<html><head>{theme_css}</head><body>{md2html(markdown_content)}</body></html>"
    webview.load_html(html_content, 'file:///')


def render_rst(content):
    colors = get_gtk_colors()
    theme_css = f"""
    <style>
    body {{ 
        background-color: {colors['bg']}; 
        color: {colors['fg']}; 
        font-family: system-ui, -apple-system, sans-serif; 
        line-height: 1.6;
        margin: 20px;
    }}
    pre {{ 
        background-color: {colors['code_bg']}; 
        color: {colors['code_fg']}; 
        padding: 10px; 
        border-radius: 4px; 
        overflow-x: auto;
        border: 1px solid {colors['border']};
    }}
    code {{ 
        background-color: {colors['code_bg']}; 
        color: {colors['code_fg']}; 
        padding: 2px 4px; 
        border-radius: 3px;
    }}
    blockquote {{ 
        border-left: 4px solid {colors['border']}; 
        margin: 0; 
        padding-left: 16px; 
        color: {adjust_brightness(colors['fg'], 0.3)};
    }}
    a {{ color: {colors['link']}; }}
    h1, h2, h3, h4, h5, h6 {{ color: {colors['fg']}; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid {colors['border']}; padding: 8px; }}
    th {{ background-color: {colors['code_bg']}; }}
    </style>
    """

    html_content = publish_string(source=content, writer_name='html').decode('utf-8')
    # Insert theme CSS into the HTML
    html_content = html_content.replace('<head>', '<head>' + theme_css)
    webview.load_html(html_content, 'file:///')


def render_html(content):
    colors = get_gtk_colors()
    theme_css = f"""
    <style>
    body {{ 
        background-color: {colors['bg']}; 
        color: {colors['fg']}; 
        font-family: system-ui, -apple-system, sans-serif; 
        line-height: 1.6;
        margin: 20px;
    }}
    pre {{ 
        background-color: {colors['code_bg']}; 
        color: {colors['code_fg']}; 
        padding: 10px; 
        border-radius: 4px; 
        overflow-x: auto;
        border: 1px solid {colors['border']};
    }}
    code {{ 
        background-color: {colors['code_bg']}; 
        color: {colors['code_fg']}; 
        padding: 2px 4px; 
        border-radius: 3px;
    }}
    blockquote {{ 
        border-left: 4px solid {colors['border']}; 
        margin: 0; 
        padding-left: 16px; 
        color: {adjust_brightness(colors['fg'], 0.3)};
    }}
    a {{ color: {colors['link']}; }}
    h1, h2, h3, h4, h5, h6 {{ color: {colors['fg']}; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid {colors['border']}; padding: 8px; }}
    th {{ background-color: {colors['code_bg']}; }}
    </style>
    """

    # Insert theme CSS into the HTML
    if '<head>' in content:
        content = content.replace('<head>', '<head>' + theme_css)
    else:
        content = f"<html><head>{theme_css}</head><body>{content}</body></html>"
    webview.load_html(content, 'file:///')


# Supported file names & supported extensions (in this order)
def readme_path(name):
    if isinstance(name, str) and name:
        if os.path.isfile(f"{config['doc-dir']}/{name}/README.md"):
            return f"{config['doc-dir']}/{name}/README.md"
        if os.path.isfile(f"{config['doc-dir']}/{name}/readme.md"):
            return f"{config['doc-dir']}/{name}/readme.md"

        elif os.path.isfile(f"{config['doc-dir']}/{name}/README.rst"):
            return f"{config['doc-dir']}/{name}/README.rst"
        elif os.path.isfile(f"{config['doc-dir']}/{name}/readme.rst"):
            return f"{config['doc-dir']}/{name}/readme.rst"

        elif os.path.isfile(f"{config['doc-dir']}/{name}/README.html"):
            return f"{config['doc-dir']}/{name}/README.html"
        elif os.path.isfile(f"{config['doc-dir']}/{name}/readme.html"):
            return f"{config['doc-dir']}/{name}/readme.html"

        elif os.path.isfile(f"{config['doc-dir']}/{name}/README"):
            return f"{config['doc-dir']}/{name}/README"
        elif os.path.isfile(f"{config['doc-dir']}/{name}/readme"):
            return f"{config['doc-dir']}/{name}/readme"

        elif os.path.isfile(f"{config['doc-dir']}/{name}/README.txt"):
            return f"{config['doc-dir']}/{name}/README.txt"
        elif os.path.isfile(f"{config['doc-dir']}/{name}/readme.txt"):
            return f"{config['doc-dir']}/{name}/readme.txt"

    return ""


# Status label formatting shows the file path in monospaced text, except for the package name, which is bold
def update_status_label():
    parts = last_file_path.split("/")
    status_label.set_markup(f'<tt>{"/".join(parts[:-2])}/</tt><b>{parts[-2]}</b><tt>/{parts[-1]}</tt>')


def fits_filter(name, filter_list):
    for item in filter_list:
        if name.startswith(item):
            return True

    return False


def main():
    GLib.set_prgname('nwg-readme-browser')

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--version", action="version",
                        version=f"%(prog)s version {__version__}")

    parser.add_argument("-i", "--internal", action="store_true",
                        help="only list Internally defined packages (nwg-shell components)")

    parser.add_argument("-c", "--config", action="store_true",
                        help=f"only list packages enumerated in the `{config_file}` file")

    args = parser.parse_args()

    global last_file_path, home_path
    last_file_path = home_path = home_file()

    all_dirs = os.listdir(config["doc-dir"])
    packages = []
    # filter doc dir names by internal package list of the list defined in config
    if args.internal:
        f_list = DEFAULTS["packages"]
        for _dir in all_dirs:
            if fits_filter(_dir, f_list):
                packages.append(_dir)
    elif args.config:
        f_list = config["packages"]
        for _dir in all_dirs:
            if fits_filter(_dir, f_list):
                packages.append(_dir)
    else:
        packages = all_dirs

    packages = sorted(packages, key=str.casefold)

    # verify which README.md files actually exist
    global readme_package_names
    readme_package_names = []
    for name in packages:
        if readme_path(name):
            readme_package_names.append(name)

    # print(readme_package_names)

    # Program window
    win = Gtk.Window.new(Gtk.WindowType.TOPLEVEL)
    win.set_title("nwg README browser")
    # floating window dimensions (expected to fit in HD resolution screen)
    win.set_default_size(1200, 680)

    # main vertical wrapper
    v_wrapper = Gtk.Box.new(Gtk.Orientation.VERTICAL, spacing=0)
    win.add(v_wrapper)

    # horizontal wrapper inside main
    h_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, spacing=0)
    h_box.set_property("margin", 0)
    v_wrapper.pack_start(h_box, True, True, 0)

    # Left column
    col_left = Gtk.Box.new(Gtk.Orientation.VERTICAL, spacing=0)
    h_box.pack_start(col_left, False, False, 6)

    # navigation buttons
    btn_bar = ButtonBar()
    col_left.pack_start(btn_bar, False, False, 6)

    global search_entry
    search_entry = SearchEntry()
    col_left.pack_start(search_entry, False, False, 6)

    # package names list (Gtk.FlowBox in Gtk.ScrolledWindow)
    file_menu = FileMenu(readme_package_names)
    search_entry.connect('search_changed', file_menu.flowbox_filter)
    col_left.pack_start(file_menu, False, False, 6)

    # footer
    footer_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
    footer_box.set_property("margin", 6)
    v_wrapper.pack_end(footer_box, False, False, 0)
    img = Gtk.Image.new_from_icon_name("nwg-readme-browser", Gtk.IconSize.DND)
    footer_box.pack_start(img, False, False, 0)
    lbl = Gtk.Label()
    lbl.set_markup(f"<b>nwg-readme-browser</b> v{__version__}")
    footer_box.pack_start(lbl, False, False, 6)

    # Right column: file preview
    global webview
    webview = WebKit2.WebView()
    webview.connect("button-release-event", on_button_release)
    scrolled = Gtk.ScrolledWindow()
    scrolled.set_propagate_natural_height(True)
    scrolled.add(webview)
    webview.set_zoom_level(config["default-zoom"])

    col_right = Gtk.Box.new(Gtk.Orientation.VERTICAL, spacing=0)
    h_box.pack_start(col_right, True, True, 6)
    col_right.pack_start(scrolled, True, True, 6)

    global status_label
    status_label = Gtk.Label()
    footer_box.pack_end(status_label, True, True, 6)

    win.connect("destroy", Gtk.main_quit)
    win.connect("key-release-event", handle_keyboard)

    # customize styling and apply theme preference
    screen = Gdk.Screen.get_default()
    provider = Gtk.CssProvider()
    style_context = Gtk.StyleContext()
    style_context.add_provider_for_screen(screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    # Apply automatic theme detection
    prefer_dark = detect_gtk_theme_preference()
    settings = Gtk.Settings.get_default()
    if settings:
        settings.set_property("gtk-application-prefer-dark-theme", prefer_dark)

    css = b"""button { padding: 0 }"""
    provider.load_from_data(css)

    # open start page
    go_home()

    win.show_all()

    search_entry.grab_focus()

    Gtk.main()


if __name__ == "__main__":
    sys.exit(main())

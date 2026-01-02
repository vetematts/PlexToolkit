import json
import os
import re
import sys
from colorama import Fore


class UserAbort(Exception):
    """Exception raised when user aborts an action."""

    pass


def is_escape(value):
    if not value:
        return False
    val = value.strip().lower()
    return val == "esc" or val == "escape" or val == "\x1b"


def clear_screen():
    """Clears the terminal screen in a cross-platform way."""
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


def get_single_keypress():
    """Waits for a single keypress and returns it (Cross-platform)."""
    if os.name == "nt":
        import msvcrt

        raw = msvcrt.getch()
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            return str(raw)
    else:
        import tty
        import termios

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


def read_line(prompt, allow_escape=True):
    print(prompt, end="", flush=True)
    buffer = []
    while True:
        key = get_single_keypress()

        # Handle ESC (ASCII 27) or Ctrl+C (ASCII 3)
        if key == "\x03" or (allow_escape and key == "\x1b"):
            print()
            return None

        # Handle Enter
        if key in ("\r", "\n"):
            print()
            return "".join(buffer)

        # Handle Backspace (ASCII 8 or 127)
        if key in ("\x08", "\x7f"):
            if buffer:
                buffer.pop()
                print("\b \b", end="", flush=True)
            continue

        # Handle regular characters
        if len(key) == 1 and key.isprintable():
            buffer.append(key)
            print(key, end="", flush=True)


def read_menu_choice(prompt, valid_choices):
    print(prompt, end="", flush=True)
    while True:
        key = get_single_keypress()
        # Handle ESC (ASCII 27) or Ctrl+C (ASCII 3)
        if key == "\x1b" or key == "\x03":
            print()
            return "ESC"
        if key in valid_choices:
            print(key)
            return key


def get_config_path():
    return os.path.join(os.path.dirname(__file__), "..", "config.json")


def load_config():
    config_path = get_config_path()
    if not os.path.exists(config_path):
        return {}
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_config(config):
    config_path = get_config_path()
    try:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=4)
    except IOError as e:
        print(Fore.RED + f"Error saving config: {e}" + Fore.RESET)


def print_grid(items, columns=1, padding=20, title=None, sort=True):
    if title:
        print(title)

    if not items:
        return

    item_list = list(items)
    if sort:
        item_list.sort(key=lambda x: str(x).lower())

    # Row-major printing
    for i in range(0, len(item_list), columns):
        row_items = item_list[i : i + columns]
        line = ""
        for item in row_items:
            line += f"{str(item):<{padding}}"
        print(line)


def pick_from_list_case_insensitive(prompt, options):
    # options is a list of strings
    # returns the matching string from options, or None if cancelled
    while True:
        user_input = read_line(prompt)
        if user_input is None:
            return None
        user_input = user_input.strip()

        # Exact match check
        for opt in options:
            if opt.lower() == user_input.lower():
                return opt

        print(Fore.RED + "Item not found in list. Please try again." + Fore.RESET)


def extract_title_and_year(text):
    # Returns (title, year_int_or_None)
    text = text.strip()
    match = re.search(r"^(.*?)\s*\((\d{4})\)$", text)
    if match:
        return match.group(1).strip(), int(match.group(2))
    return text, None


def normalize_title(title):
    # Remove punctuation and lowercase
    if not title:
        return ""
    cleaned = re.sub(r"[^\w\s]", "", title).lower()
    return " ".join(cleaned.split())


def read_index_or_skip(max_index, prompt):
    # Returns integer index (1-based) or None if skipped/cancelled
    while True:
        val = read_line(prompt)
        if val is None:
            return None
        val = val.strip()
        if is_escape(val) or val.lower() == "s":
            return None

        if val.isdigit():
            idx = int(val)
            if 1 <= idx <= max_index:
                return idx

        print(Fore.RED + "Invalid number." + Fore.RESET)


def load_fallback_data(section):
    # Load fallback data for a given section from fallback_collections.json.
    fallback_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "fallback_collections.json"
    )
    with open(fallback_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get(section, {})

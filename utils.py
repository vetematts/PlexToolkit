import json
import os
import re
from colorama import Fore

class UserAbort(Exception):
    """Exception raised when user aborts an action."""
    pass

def is_escape(value):
    if not value:
        return False
    return value.strip().lower() == 'esc'

def read_line(prompt, allow_escape=True):
    try:
        user_input = input(prompt)
        if allow_escape and is_escape(user_input):
            return None
        return user_input
    except KeyboardInterrupt:
        print()
        return None

def read_menu_choice(prompt, valid_choices):
    while True:
        choice = input(prompt).strip()
        if is_escape(choice):
            return "ESC"
        if choice in valid_choices:
            return choice
        print(Fore.RED + "Invalid selection. Please try again." + Fore.RESET)

def get_config_path():
    return os.path.join(os.path.dirname(__file__), "config.json")

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
        row_items = item_list[i:i+columns]
        line = ""
        for item in row_items:
            line += f"{str(item):<{padding}}"
        print(line)

def pick_from_list_case_insensitive(prompt, options):
    # options is a list of strings
    # returns the matching string from options, or None if cancelled
    while True:
        user_input = input(prompt).strip()
        if is_escape(user_input):
            return None

        # Exact match check
        for opt in options:
            if opt.lower() == user_input.lower():
                return opt

        print(Fore.RED + "Item not found in list. Please try again." + Fore.RESET)

def extract_title_and_year(text):
    # Returns (title, year_int_or_None)
    match = re.search(r'^(.*?)\s*\((\d{4})\)$', text)
    if match:
        return match.group(1).strip(), int(match.group(2))
    return text.strip(), None

def normalize_title(title):
    # Remove punctuation and lowercase
    if not title: return ""
    return re.sub(r'[^\w\s]', '', title).lower().strip()

def read_index_or_skip(max_index, prompt):
    # Returns integer index (1-based) or None if skipped/cancelled
    while True:
        val = input(prompt).strip()
        if is_escape(val) or val.lower() == 's':
            return None

        if val.isdigit():
            idx = int(val)
            if 1 <= idx <= max_index:
                return idx

        print(Fore.RED + "Invalid number." + Fore.RESET)

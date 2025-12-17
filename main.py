"""
This script uses:
- The TMDb API (via TMDbSearch) to fetch movie titles by keyword or collection.
- The PlexAPI to search for movies and create collections in the user's Plex library.
"""

import os
import json
import re
import sys
import contextlib
from typing import Optional

from colorama import init, Fore
import emojis
from plex_manager import PlexManager
from tmdb_search import TMDbSearch
from styling import print_plex_logo_ascii

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

def is_escape(value: str) -> bool:
    if value is None:
        return False
    value = value.strip()
    return value == "\x1b" or value.lower() in ("esc", "escape")

@contextlib.contextmanager
def _raw_input_mode():
    """
    Temporarily switch stdin into a mode where we can read single keypresses.
    Falls back to normal behavior when stdin isn't a TTY.
    """
    if not sys.stdin.isatty():
        yield
        return
    if os.name == "nt":
        yield
        return
    import termios
    import tty

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        yield
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def read_keypress() -> Optional[str]:
    """
    Reads a single keypress and returns:
    - "ESC" for Escape
    - "ENTER" for Enter/Return
    - "BACKSPACE" for Backspace/Delete
    - otherwise the literal character (e.g., "1", "y", "a")
    Returns None if stdin isn't a TTY (caller should fall back to input()).
    """
    if not sys.stdin.isatty():
        return None

    if os.name == "nt":
        import msvcrt

        ch = msvcrt.getwch()
        if ch == "\x1b":
            return "ESC"
        if ch in ("\r", "\n"):
            return "ENTER"
        if ch in ("\b", "\x7f"):
            return "BACKSPACE"
        return ch

    with _raw_input_mode():
        ch = sys.stdin.read(1)
    if ch == "\x1b":
        return "ESC"
    if ch in ("\r", "\n"):
        return "ENTER"
    if ch in ("\b", "\x7f"):
        return "BACKSPACE"
    return ch


def read_menu_choice(prompt: str, valid: set[str]) -> str:
    """
    Reads a single-key choice (no Enter) when possible; falls back to input().
    """
    if not sys.stdin.isatty():
        return input(prompt).strip()

    print(prompt, end="", flush=True)
    while True:
        key = read_keypress()
        if key is None:
            return input().strip()
        if key == "ESC":
            print("Esc")
            return "ESC"
        if key == "ENTER":
            continue
        if len(key) == 1:
            candidate = key.strip()
            if candidate in valid:
                print(candidate)
                return candidate

def read_number(max_value: int, prompt: str) -> Optional[int]:
    """
    Reads a number up to max_value, with real Escape support (no Enter required for Esc).
    Returns None if user presses Esc.
    Uses raw key input when possible; otherwise falls back to input().
    """
    if not sys.stdin.isatty():
        while True:
            raw = input(prompt).strip()
            if is_escape(raw):
                return None
            if raw.isdigit():
                value = int(raw)
                if 1 <= value <= max_value:
                    return value
            print("Invalid selection.")

    print(prompt, end="", flush=True)
    buf = []
    while True:
        key = read_keypress()
        if key is None:
            raw = input().strip()
            if is_escape(raw):
                return None
            if raw.isdigit():
                value = int(raw)
                if 1 <= value <= max_value:
                    return value
            print("Invalid selection.")
            print(prompt, end="", flush=True)
            buf = []
            continue

        if key == "ESC":
            print()
            return None
        if key == "ENTER":
            if not buf:
                continue
            raw = "".join(buf)
            if raw.isdigit():
                value = int(raw)
                if 1 <= value <= max_value:
                    print()
                    return value
            print("\nInvalid selection.")
            print(prompt, end="", flush=True)
            buf = []
            continue
        if key == "BACKSPACE":
            if buf:
                buf.pop()
                sys.stdout.write("\b \b")
                sys.stdout.flush()
            continue

        if len(key) == 1 and key.isdigit():
            buf.append(key)
            sys.stdout.write(key)
            sys.stdout.flush()


def read_line(prompt: str, allow_escape: bool = True) -> Optional[str]:
    """
    Reads a full line of text, but supports true Escape (no Enter) when stdin is a TTY.
    Returns None when Esc is pressed (and allow_escape is True).
    """
    if not sys.stdin.isatty():
        text = input(prompt)
        if allow_escape and is_escape(text):
            return None
        return text

    print(prompt, end="", flush=True)
    buf = []
    while True:
        key = read_keypress()
        if key is None:
            text = input().strip()
            if allow_escape and is_escape(text):
                return None
            return text

        if key == "ESC" and allow_escape:
            print()
            return None
        if key == "ENTER":
            print()
            return "".join(buf)
        if key == "BACKSPACE":
            if buf:
                buf.pop()
                sys.stdout.write("\b \b")
                sys.stdout.flush()
            continue
        if len(key) == 1 and key.isprintable():
            buf.append(key)
            sys.stdout.write(key)
            sys.stdout.flush()


def load_config():
    # Load credentials from config.json, or return empty defaults if it doesn't exist
    if not os.path.exists(CONFIG_FILE):
        return {"PLEX_TOKEN": "", "PLEX_URL": "", "TMDB_API_KEY": ""}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(cfg):
    # Save the current credentials to config.json for future use
    # Accepts a dictionary of credentials.
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4)


init(autoreset=True)

config = load_config()
PLEX_TOKEN = config.get("PLEX_TOKEN")
PLEX_URL = config.get("PLEX_URL")
TMDB_API_KEY = config.get("TMDB_API_KEY")
MOCK_MODE = False  # Set to True to simulate Plex actions without making changes


def welcome():
    """Display welcome message and Plex logo, clearing the screen first."""
    # Clear terminal screen for cleanliness in a cross-platform way.
    if os.name == "nt":  # For Windows
        os.system("cls")
    else:  # For macOS and Linux
        os.system("clear")
    print_plex_logo_ascii()
    print(Fore.CYAN + f"\n{emojis.MOVIE} Welcome to the Plex Collection Creator!")
    print(Fore.YELLOW + "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")


def check_credentials():
    # Check and display the status of the loaded credentials.
    # Shows which credentials are set using color and emoji indicators.
    current_config = load_config()
    print(Fore.GREEN + f"{emojis.KEY} Loaded Credentials:")
    print(
        f"Plex Token: {emojis.CHECK if current_config.get('PLEX_TOKEN', '').strip() else emojis.CROSS}"
    )
    print(
        f"Plex URL: {emojis.CHECK if current_config.get('PLEX_URL', '').strip() else emojis.CROSS}"
    )
    print(
        f"TMDb API Key: {emojis.CHECK if current_config.get('TMDB_API_KEY', '').strip() else emojis.CROSS}\n"
    )


def run_collection_builder():
    # Main interactive loop. Stays in a single while-loop and avoids repeating run_collection_builder().
    # Returns to main menu with `continue`.

    def pause(msg: str = "Press Enter to return to the menu..."):
        input(msg)

    class UserAbort(Exception):
        pass

    def read_index_or_skip(max_value: int, prompt: str) -> Optional[int]:
        """
        Reads either:
        - a numeric selection (1..max_value) + Enter
        - 's' to skip (returns None)
        - Esc to cancel (raises UserAbort)
        """
        if not sys.stdin.isatty():
            while True:
                raw = input(prompt).strip()
                if is_escape(raw) or raw.lower() in ("q", "quit"):
                    raise UserAbort()
                if raw.lower() in ("s", "skip"):
                    return None
                if raw.isdigit():
                    idx = int(raw)
                    if 1 <= idx <= max_value:
                        return idx
                print("Invalid selection.")

        print(prompt, end="", flush=True)
        buf = []
        while True:
            key = read_keypress()
            if key is None:
                raw = input().strip()
                if is_escape(raw) or raw.lower() in ("q", "quit"):
                    raise UserAbort()
                if raw.lower() in ("s", "skip"):
                    return None
                if raw.isdigit():
                    idx = int(raw)
                    if 1 <= idx <= max_value:
                        return idx
                print("Invalid selection.")
                print(prompt, end="", flush=True)
                buf = []
                continue

            if key == "ESC":
                print()
                raise UserAbort()
            if key == "ENTER":
                if not buf:
                    continue
                raw = "".join(buf)
                if raw.isdigit():
                    idx = int(raw)
                    if 1 <= idx <= max_value:
                        print()
                        return idx
                print("\nInvalid selection.")
                print(prompt, end="", flush=True)
                buf = []
                continue
            if key == "BACKSPACE":
                if buf:
                    buf.pop()
                    sys.stdout.write("\b \b")
                    sys.stdout.flush()
                continue
            if len(key) == 1 and key.lower() == "s":
                print()
                return None
            if len(key) == 1 and key.isdigit():
                buf.append(key)
                sys.stdout.write(key)
                sys.stdout.flush()

    def format_plex_item(item) -> str:
        title = getattr(item, "title", str(item))
        year = getattr(item, "year", None)
        return f"{title} ({year})" if year else title

    def pick_plex_match(raw_title: str, results):
        if not results:
            return None
        if len(results) == 1:
            return results[0]

        print(f"\nMultiple Plex matches for '{raw_title}':")
        for i, item in enumerate(results, 1):
            print(f"{i}. {format_plex_item(item)}")

        idx = read_index_or_skip(
            len(results),
            "Pick a number + Enter, 's' to skip, or Esc to cancel: ",
        )
        if idx is None:
            return None
        return results[idx - 1]

    dry_run = False
    while True:
        welcome()
        check_credentials()
        print(
            Fore.LIGHTBLACK_EX
            + f"{emojis.INFO}  Dry run: {'ON' if dry_run else 'OFF'} (no Plex changes when ON)\n"
        )

        # Main menu
        print(Fore.BLUE + f"{emojis.CLAPPER} MAIN MENU:\n")
        print(Fore.GREEN + "1." + Fore.RESET + f" {emojis.MANUAL} Manual Entry\n")
        print(
            Fore.GREEN
            + "2."
            + Fore.RESET
            + f" {emojis.FRANCHISE}  Known Franchise (e.g. Star Wars, Harry Potter)\n"
        )
        print(
            Fore.GREEN
            + "3."
            + Fore.RESET
            + f" {emojis.STUDIO}  Studio / Keyword (e.g. A24, Pixar)\n"
        )
        print(
            Fore.YELLOW
            + "4."
            + Fore.RESET
            + f" {emojis.SETTINGS}  Configure Credentials (Plex / TMDb)\n"
        )
        print(
            Fore.CYAN
            + "5."
            + Fore.RESET
            + f" {emojis.REPEAT} Toggle Dry Run (currently {'ON' if dry_run else 'OFF'})\n"
        )
        print(Fore.RED + "6." + Fore.RESET + f" {emojis.EXIT} Exit\n")
        print(
            Fore.LIGHTBLACK_EX
            + f"{emojis.INFO}  You can return to this menu after each collection is created.\n"
        )
        mode = read_menu_choice("Select an option (Esc to exit): ", set("123456"))
        if mode == "ESC":
            mode = "6"

        if mode not in ("1", "2", "3", "4", "5", "6"):
            print("Invalid selection. Please choose a valid menu option (1-6).")
            pause()
            continue

        if mode == "6":
            print(f"{emojis.WAVE} Goodbye!")
            return

        if mode == "5":
            dry_run = not dry_run
            print(
                Fore.GREEN
                + f"{emojis.CHECK} Dry run is now {'ON' if dry_run else 'OFF'}."
            )
            pause()
            continue

        # Credentials settings
        if mode == "4":

            def configure_credentials():
                # Submenu for credentials
                while True:
                    # Clear terminal screen for cleanliness in a cross-platform way.
                    if os.name == "nt":  # For Windows
                        os.system("cls")
                    else:  # For macOS and Linux
                        os.system("clear")
                    print(Fore.CYAN + f"{emojis.CONFIGURE} CONFIGURE CREDENTIALS")
                    print(Fore.GREEN + "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
                    print(
                        Fore.YELLOW
                        + "1."
                        + Fore.RESET
                        + f" {emojis.KEY} Set Plex Token\n"
                    )
                    print(
                        Fore.YELLOW
                        + "2."
                        + Fore.RESET
                        + f" {emojis.URL} Set Plex URL\n"
                    )
                    print(
                        Fore.BLUE
                        + "3."
                        + Fore.RESET
                        + f" {emojis.CLAPPER} Set TMDb API Key\n"
                    )
                    print(
                        Fore.GREEN
                        + "4."
                        + Fore.RESET
                        + f" {emojis.BOOK} Show current values\n"
                    )
                    print(
                        Fore.RED
                        + "5."
                        + Fore.RESET
                        + f" {emojis.BACK} Return to main menu\n"
                    )
                    choice = read_menu_choice(
                        "Select an option (Esc to go back): ", set("12345")
                    )
                    if choice == "ESC":
                        break
                    if choice == "1":
                        config["PLEX_TOKEN"] = input("Enter new Plex Token: ").strip()
                        save_config(config)
                        print(
                            Fore.GREEN
                            + f"{emojis.CHECK} Plex Token saved successfully!\n"
                        )
                        pause()
                    elif choice == "2":
                        config["PLEX_URL"] = input("Enter new Plex URL: ").strip()
                        save_config(config)
                        print(
                            Fore.GREEN
                            + f"{emojis.CHECK} Plex URL saved successfully!\n"
                        )
                        pause()
                    elif choice == "3":
                        config["TMDB_API_KEY"] = input(
                            "Enter new TMDb API Key: "
                        ).strip()
                        save_config(config)
                        print(
                            Fore.GREEN
                            + f"{emojis.CHECK} TMDb API Key saved successfully!\n"
                        )
                        pause()
                    elif choice == "4":
                        # Clear terminal screen for cleanliness in a cross-platform way.
                        if os.name == "nt":  # For Windows
                            os.system("cls")
                        else:  # For macOS and Linux
                            os.system("clear")
                        print(Fore.CYAN + f"{emojis.BOOK} Current Configuration:\n")
                        print(json.dumps(config, indent=4))
                        pause("\nPress Enter to return to the credentials menu...")
                    elif choice == "5":
                        break
                    else:
                        print("Invalid choice. Try again.")
                        pause()

            configure_credentials()
            continue  # back to main loop

        # Collection Creation (modes 1-3)
        titles = []
        collection_name = None

        # Prepare TMDb helper if key present
        tmdb = (
            TMDbSearch(config.get("TMDB_API_KEY"))
            if config.get("TMDB_API_KEY")
            else None
        )

        # Hardcoded TMDB collection IDs and studios
        known_collections = {
            "Alien": 8091,
            "Back to the Future": 264,
            "Despicable Me": 86066,
            "Evil Dead": 1960,
            "Fast & Furious": 9485,
            "Harry Potter": 1241,
            "The Hunger Games": 131635,
            "Indiana Jones": 84,
            "James Bond": 645,
            "John Wick": 404609,
            "Jurassic Park": 328,
            "The Lord of the Rings": 119,
            "The Matrix": 2344,
            "Mission: Impossible": 87359,
            "Ocean's": 304,
            "Pirates of the Caribbean": 295,
            "Planet of the Apes": 173710,
            "Scream": 2602,
            "Shrek": 2150,
            "Sonic the Hedgehog": 720879,
            "Star Trek": 115575,
            "Star Wars": 10,
            "The Dark Knight": 263,
            "The Twilight Saga": 33514,
        }
        studio_map = {
            "a24": {"company": 41077},
            "pixar": {"company": 3},
            "studio ghibli": {"company": 10342},
            "mcu": {"keyword": 180547},
            "dceu": {"keyword": 229266},
        }

        if mode == "1":
            print("Type 'back' or 'Esc' to return to the main menu.")
            collection_name = read_line(
                "Enter a name for your new collection (Esc to cancel): "
            )
            if collection_name is None or collection_name.strip().lower() == "back":
                continue
            collection_name = collection_name.strip()
            plex_token = config.get("PLEX_TOKEN")
            plex_url = config.get("PLEX_URL")
            if not plex_token or not plex_url:
                print(
                    Fore.RED + f"{emojis.CROSS} Missing or invalid Plex Token or URL."
                )
                pause()
                continue
            print("\nEnter movie titles one per line. Leave a blank line to finish:")
            while True:
                title = read_line("", allow_escape=True)
                if title is None:
                    print("Canceled. Returning to main menu.")
                    pause()
                    titles = []
                    collection_name = None
                    break
                if not title.strip():
                    break
                titles.append(title.strip())

        elif mode == "2":
            # Franchises/ Series Selection
            franchises_data = load_fallback_data("Franchises")
            if not tmdb:
                print(
                    Fore.RED
                    + f"{emojis.CROSS} TMDb API key not provided. Using fallback hardcoded titles.\n"
                )
                print_grid(
                    franchises_data.keys(),
                    columns=3,
                    padding=28,
                    title=f"{emojis.FRANCHISE}  Available Franchises:",
                )
                choice = pick_from_list_case_insensitive(
                    "\n"
                    + Fore.LIGHTBLACK_EX
                    + f"{emojis.REPEAT} Type the franchise name (or 'back' to return): ",
                    franchises_data.keys(),
                )
                if choice is None:
                    continue
                titles = franchises_data[choice]
            else:
                print_grid(
                    known_collections.keys(),
                    columns=3,
                    padding=28,
                    title=f"{emojis.FRANCHISE}  Available Collections (TMDb):",
                )
                choice = pick_from_list_case_insensitive(
                    "\n"
                    + Fore.LIGHTBLACK_EX
                    + f"{emojis.REPEAT} Type the collection name (or 'back' to return): ",
                    known_collections.keys(),
                )
                if choice is None:
                    continue
                collection_id = known_collections[choice]
                try:
                    titles = tmdb.get_movies_from_collection(collection_id)
                except Exception as e:
                    print(
                        Fore.RED
                        + f"{emojis.CROSS} Error retrieving movies from TMDb collection. Please check your TMDb API key."
                    )
                    print(f"Exception: {e}")
                    pause()
                    continue
            collection_name = input("Enter a name for your new collection: ").strip()

        elif mode == "3":
            # Studios selection
            studios_data = load_fallback_data("Studios")
            if not tmdb:
                print(
                    Fore.RED
                    + f"{emojis.CROSS} TMDb API key not provided. Using fallback hardcoded titles.\n"
                )
                print_grid(
                    studios_data.keys(),
                    columns=3,
                    padding=24,
                    title=f"{emojis.STUDIO}  Available Studios:",
                )
                choice = pick_from_list_case_insensitive(
                    "\n"
                    + Fore.LIGHTBLACK_EX
                    + f"{emojis.REPEAT} Type the studio name (or 'back' to return): ",
                    studios_data.keys(),
                )
                if choice is None:
                    continue
                titles = studios_data.get(choice, [])
            else:
                pretty_names = []
                pretty_to_key = {}
                for key in studio_map.keys():
                    pretty = key.upper() if key in ("mcu", "dceu") else key.title()
                    pretty_names.append(pretty)
                    pretty_to_key[pretty.lower()] = key
                print_grid(
                    pretty_names,
                    columns=3,
                    padding=24,
                    title=f"{emojis.STUDIO}  Available Studios:",
                )
                choice_pretty = pick_from_list_case_insensitive(
                    "\n"
                    + Fore.LIGHTBLACK_EX
                    + f"{emojis.REPEAT} Type the studio name (or 'back' to return): ",
                    pretty_names,
                )
                if choice_pretty is None:
                    continue
                norm_key = pretty_to_key[choice_pretty.lower()]
                studio_info = studio_map[norm_key]
                import requests

                def fetch_movies_by_company_or_keyword(
                    api_key, company_id=None, keyword_id=None
                ):
                    # Fetches movie titles from TMDb Discover using a company or keyword.
                    # Raises a clear exception on HTTP errors (e.g., invalid/expired API key).
                    url = "https://api.themoviedb.org/3/discover/movie"
                    params = {
                        "api_key": api_key,
                        "language": "en-US",
                        "sort_by": "popularity.desc",
                        "page": 1,
                    }
                    if company_id:
                        params["with_companies"] = company_id
                    if keyword_id:
                        params["with_keywords"] = keyword_id
                    titles_out = []
                    while True:
                        resp = requests.get(url, params=params, timeout=10)
                        # Surface auth and other HTTP errors explicitly
                        if resp.status_code == 401:
                            raise ValueError(
                                "TMDb authentication failed (invalid API key)."
                            )
                        if resp.status_code != 200:
                            # Include a short snippet of the response for debugging
                            snippet = ""
                            try:
                                snippet = resp.json().get("status_message", "")
                            except Exception:
                                snippet = resp.text[:200]
                            raise RuntimeError(
                                f"TMDb error {resp.status_code}: {snippet}"
                            )
                        data = resp.json()
                        titles_out.extend(
                            [
                                m.get("title")
                                for m in data.get("results", [])
                                if m.get("title")
                            ]
                        )
                        if data.get("page", 1) >= data.get("total_pages", 1):
                            break
                        params["page"] += 1
                    return titles_out

                try:
                    titles = fetch_movies_by_company_or_keyword(
                        config.get("TMDB_API_KEY"),
                        company_id=studio_info.get("company"),
                        keyword_id=studio_info.get("keyword"),
                    )
                except Exception as e:
                    print(
                        Fore.RED
                        + f"{emojis.CROSS} Error retrieving movies from TMDb collection. Please check your TMDb API key."
                    )
                    print(f"Exception: {e}")
                    pause()
                    continue
            collection_name = input("Enter a name for your new collection: ").strip()

        # If no title found go back to menu
        if not titles:
            print("No movies found for that input.")
            pause()
            continue

        # MOCK mode short-circuit
        if MOCK_MODE:
            print("[MOCK MODE ENABLED]")
            print(f"Simulating search in Plex for {len(titles)} titles...")
            for t in titles:
                print(f"- Would add '{t}' to collection.")
            print(f"Finished. Would create collection with {len(titles)} movies.")
            pause()
            continue

        # Ensure Plex credential entered
        plex_token = config.get("PLEX_TOKEN")
        plex_url = config.get("PLEX_URL")
        if not plex_token or not plex_url:
            print(Fore.RED + f"{emojis.CROSS} Missing or invalid Plex Token or URL.")
            pause()
            continue

        # Try connecting to Plex
        try:
            plex = PlexManager(plex_token, plex_url)
            library = plex.plex.library.section("Movies")
        except Exception:
            print(Fore.RED + f"{emojis.CROSS} Could not connect to Plex.")
            print("Please make sure your Plex Token and URL are correct.\n")
            pause()
            continue

        # Search movie title and optional year from user input.
        # Example: "Inception (2010)" -> ("Inception", 2010)
        def extract_title_and_year(raw_title):
            match = re.match(r"^(.*?)(?:\s+\((\d{4})\))?$", raw_title.strip())
            return (
                match.group(1).strip(),
                int(match.group(2)) if match.group(2) else None,
            )

        found_movies, not_found = [], []
        matched_pairs = []
        seen_rating_keys = set()
        try:
            for raw in titles:
                title, year = extract_title_and_year(raw)
                try:
                    results = (
                        library.search(title, year=year)
                        if year
                        else library.search(title)
                    )
                    if not results and year:
                        results = library.search(title)

                    chosen = pick_plex_match(raw, results)
                    if chosen is None:
                        not_found.append(raw)
                        continue

                    rating_key = str(getattr(chosen, "ratingKey", ""))
                    if rating_key and rating_key in seen_rating_keys:
                        continue
                    if rating_key:
                        seen_rating_keys.add(rating_key)
                    found_movies.append(chosen)
                    matched_pairs.append((raw, chosen))
                except (AttributeError, TypeError, ValueError) as e:
                    print(f"Error searching for '{raw}': {e}")
                    not_found.append(raw)
        except UserAbort:
            print("Canceled. Returning to main menu.")
            pause()
            continue

        print(f"\nFound {len(found_movies)} movies in Plex.")
        if not_found:
            print(f"Couldn’t find {len(not_found)}:")
            for nf in not_found:
                print(f"- {nf}")

        if not found_movies:
            print(f"{emojis.CROSS} No valid matches found — collection not created.")
            pause()
            continue

        print("\nMovies to add to collection:")
        for i, mv in enumerate(found_movies, 1):
            print(f"{i}. {format_plex_item(mv)}")

        print("\nSelections:")
        for raw, mv in matched_pairs:
            print(f"- {raw} -> {format_plex_item(mv)}")

        confirm = (
            input("Proceed to create collection with these movies? (y/n): ")
            .strip()
            .lower()
        )
        if confirm != "y":
            print("Aborted by user.")
            pause()
            continue

        if dry_run:
            print(f"\n[DRY RUN] Would create collection '{collection_name}'.")
            print(f"[DRY RUN] Would include {len(found_movies)} movies.")
            pause()
            continue

        library.createCollection(collection_name, items=found_movies)
        print(
            f"\n{emojis.CHECK} Created collection '{collection_name}' with {len(found_movies)} movies."
        )
        pause()
        # loop continues to main menu


def load_fallback_data(section):
    # Load fallback data for a given section from fallback_collections.json.
    fallback_path = os.path.join(os.path.dirname(__file__), "fallback_collections.json")
    with open(fallback_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get(section, {})


def print_grid(names, columns=3, padding=28, title=None, title_emoji=None):
    # Prints the list of titles in columns for readability
    if title:
        print((title_emoji or "") + " " + title)
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    sorted_names = sorted(names)
    rows = [sorted_names[i : i + columns] for i in range(0, len(sorted_names), columns)]
    for row in rows:
        print("".join(name.ljust(padding) for name in row))


def pick_from_list_case_insensitive(prompt, choices, back_allowed=True):
    # Ask the user to pick an option from list of choices
    # Returns the matched canonical item or None if user typed 'back' and back_allowed is True.
    # Keeps prompting until a valid choice is entered.
    lowered = {c.lower(): c for c in choices}
    while True:
        choice = read_line(prompt, allow_escape=True)
        if choice is None:
            return None if back_allowed else None
        choice = choice.strip()
        if back_allowed and (choice.lower() == "back" or is_escape(choice)):
            return None
        if choice.lower() in lowered:
            return lowered[choice.lower()]
        print("Unknown option. Please type one of the listed items, or 'back'/'Esc'.")


def print_list(items, columns=3, padding=28):
    # Prints the list of items in columns.
    names = sorted(items)
    rows = [names[i : i + columns] for i in range(0, len(names), columns)]
    for row in rows:
        print("".join(name.ljust(padding) for name in row))


if __name__ == "__main__":
    run_collection_builder()

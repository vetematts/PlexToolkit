"""
This script uses:
- The TMDb API (via TMDbSearch) to fetch movie titles by keyword or collection.
- The PlexAPI to search for movies and create collections in the user's Plex library.
"""

import os
import sys
import time

# Explicitly add the current directory to sys.path to ensure 'toolkit' is found
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timezone

from colorama import init, Fore
from toolkit import emojis
from toolkit.services.plex_manager import PlexManager
from toolkit.services.tmdb_search import TMDbSearch
from toolkit.styling import print_plex_logo_ascii, PLEX_YELLOW
from toolkit import features
from toolkit import ops
from toolkit.utils import (
    load_config,
    save_config,
    print_grid,
    pick_from_list_case_insensitive,
    clear_screen,
)
from toolkit.input_handler import InputHandler

# Try to import plexapi for version checking
try:
    import plexapi
except ImportError:
    plexapi = None

# Use the robust input handler that supports Arrow keys and Esc
read_line = InputHandler.read_line
read_menu_choice = InputHandler.read_menu_choice


def _now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def test_plex_connection(cfg):
    """
    Attempts to connect to Plex and access the configured movie library.
    Returns True on success, False otherwise.
    """
    plex_token = cfg.get("PLEX_TOKEN", "").strip()
    plex_url = cfg.get("PLEX_URL", "").strip()
    library_name = (cfg.get("PLEX_LIBRARY") or "Movies").strip() or "Movies"

    if not plex_token or not plex_url:
        print(
            Fore.YELLOW
            + f"{emojis.INFO} Skipping Plex connection test (token or URL missing).\n"
        )
        return False

    try:
        plex_manager = PlexManager(plex_token, plex_url)
        library = plex_manager.get_movie_library(library_name)
        if not library:
            print(
                Fore.RED
                + f"{emojis.CROSS} Connected to Plex, but library '{library_name}' was not found.\n"
            )
            return False
        print(
            Fore.GREEN
            + f"{emojis.CHECK} Plex connection successful. Library '{library_name}' is available.\n"
        )
        cfg["PLEX_LAST_TESTED"] = _now_iso()
        save_config(cfg)
        return True
    except Exception as e:
        print(Fore.RED + f"{emojis.CROSS} Plex connection test failed: {e}\n")
        return False


def test_tmdb_connection(cfg):
    """
    Attempts a lightweight TMDb call to validate the API key.
    Returns True on success, False otherwise.
    """
    api_key = cfg.get("TMDB_API_KEY", "").strip()
    if not api_key:
        print(
            Fore.YELLOW
            + f"{emojis.INFO} Skipping TMDb connection test (API key missing).\n"
        )
        return False

    try:
        tmdb = TMDbSearch(api_key)
        # Perform a minimal search to validate the key.
        tmdb.search_movies("test", limit=1)
        print(Fore.GREEN + f"{emojis.CHECK} TMDb connection successful.\n")
        cfg["TMDB_LAST_TESTED"] = _now_iso()
        save_config(cfg)
        return True
    except Exception as e:
        print(Fore.RED + f"{emojis.CROSS} TMDb connection test failed: {e}\n")
        return False


init(autoreset=True)

config = load_config()

# Allow Environment Variables to override config file (useful for Docker/CI)
PLEX_TOKEN = os.getenv("PLEX_TOKEN", config.get("PLEX_TOKEN"))
PLEX_URL = os.getenv("PLEX_URL", config.get("PLEX_URL"))
TMDB_API_KEY = os.getenv("TMDB_API_KEY", config.get("TMDB_API_KEY"))

# Update config object so the rest of the app uses the active credentials
if PLEX_TOKEN:
    config["PLEX_TOKEN"] = PLEX_TOKEN
if PLEX_URL:
    config["PLEX_URL"] = PLEX_URL
if TMDB_API_KEY:
    config["TMDB_API_KEY"] = TMDB_API_KEY


def welcome():
    """Display welcome message and Plex logo, clearing the screen first."""
    clear_screen()
    print()
    print_plex_logo_ascii()
    print(PLEX_YELLOW + f"\n{emojis.MOVIE} Welcome to the Plex Toolkit!\n")


def check_system_requirements():
    """Checks for dependency versions and warns if outdated."""
    if not plexapi:
        return

    try:
        # Check plexapi for Smart Collection support (Requires >= 4.15.0)
        parts = plexapi.__version__.split(".")
        if len(parts) >= 2:
            major, minor = int(parts[0]), int(parts[1])
            if major < 4 or (major == 4 and minor < 15):
                print(
                    Fore.YELLOW
                    + f"{emojis.INFO} Warning: 'plexapi' is outdated ({plexapi.__version__})."
                )
                print(
                    "   Smart Collections require v4.15.0+. Run 'pip install --upgrade plexapi' to update.\n"
                    + Fore.RESET
                )
                time.sleep(2)
    except Exception:
        pass


def check_credentials():
    # Check and display the status of the loaded credentials.
    # Shows which credentials are set using colour and emoji indicators.
    current_config = load_config()
    print(Fore.GREEN + f"{emojis.KEY} Loaded Credentials:")
    print(
        f"Plex Token: {emojis.CHECK if current_config.get('PLEX_TOKEN', '').strip() else emojis.CROSS}"
    )
    print(
        f"Plex URL: {emojis.CHECK if current_config.get('PLEX_URL', '').strip() else emojis.CROSS}"
    )
    print(
        f"TMDb API Key: {emojis.CHECK if current_config.get('TMDB_API_KEY', '').strip() else emojis.CROSS}"
    )
    plex_library = current_config.get("PLEX_LIBRARY", "").strip() or "Movies"
    print(f"Plex Library: {emojis.CHECK} {plex_library}\n")


def handle_main_menu() -> str:
    """Displays the main menu and returns the user's selection."""
    print(PLEX_YELLOW + f"{emojis.CLAPPER} MAIN MENU:\n")
    print(
        Fore.GREEN
        + "1."
        + Fore.RESET
        + f" {emojis.FRANCHISE} Franchise / Series (e.g. Star Wars, Harry Potter)\n"
    )
    print(
        Fore.GREEN
        + "2."
        + Fore.RESET
        + f" {emojis.STUDIO}  Studio / Collections (e.g. A24, Pixar)\n"
    )
    print(Fore.GREEN + "3." + Fore.RESET + f" {emojis.MANUAL} Manual Entry\n")
    print(
        Fore.GREEN + "4." + Fore.RESET + f" {emojis.FRANCHISE} Missing Movies Scanner\n"
    )
    print(
        Fore.YELLOW + "5." + Fore.RESET + f" {emojis.ART} Fix Posters & Backgrounds\n"
    )
    print(
        Fore.YELLOW
        + "6."
        + Fore.RESET
        + f" {emojis.CONFIGURE} Settings & Credentials\n"
    )
    print(Fore.RED + "7." + Fore.RESET + f" {emojis.EXIT} Exit\n")
    print(
        Fore.LIGHTBLACK_EX
        + f"{emojis.INFO}  You can return to this menu after each collection is created.\n"
    )
    mode = read_menu_choice("Select an option (Esc to exit): ", set("1234567"))
    if mode == "ESC":
        return "7"
    return mode


def handle_credentials_menu():
    """Displays and manages the credentials configuration submenu."""

    def pause(msg: str = "Press Enter or Esc to return to the menu..."):
        read_line(msg)

    def validate_url(url):
        if not url:
            print(Fore.RED + f"{emojis.CROSS} Plex URL cannot be empty.\n")
            return None
        # Sanitize: remove spaces (common when copying from Plex UI: "IP : Port")
        url = url.replace(" ", "")
        # Auto-add http:// if missing
        if not url.lower().startswith("http://") and not url.lower().startswith(
            "https://"
        ):
            url = "http://" + url
            print(Fore.YELLOW + f"{emojis.INFO} Auto-formatted URL to: {url}")
        return url

    def _prompt_update_config(
        key, prompt, header_text, info_text, validator=None, tester=None
    ):
        """Helper to handle the UI flow for updating a config value."""
        clear_screen()
        print(header_text + "\n")
        if info_text:
            print(Fore.LIGHTBLACK_EX + info_text + Fore.RESET + "\n")

        new_val = read_line(prompt)
        if new_val is None:
            return

        new_val = new_val.strip()
        if validator:
            new_val = validator(new_val)
            if new_val is None:  # Validator handles error printing
                pause()
                return
        elif not new_val:
            print(Fore.RED + f"{emojis.CROSS} Value cannot be empty.\n")
            pause()
            return

        config[key] = new_val
        save_config(config)
        print(Fore.GREEN + f"{emojis.CHECK} Saved successfully!\n")
        if tester:
            tester(config)
        pause()

    while True:
        clear_screen()
        print()
        print(PLEX_YELLOW + f"{emojis.CONFIGURE} CONFIGURE CREDENTIALS\n")
        print(Fore.YELLOW + "1." + Fore.RESET + f" {emojis.KEY} Set Plex Token\n")
        print(Fore.YELLOW + "2." + Fore.RESET + f" {emojis.URL} Set Plex URL\n")
        print(Fore.BLUE + "3." + Fore.RESET + f" {emojis.CLAPPER} Set TMDb API Key\n")
        print(
            Fore.CYAN + "4." + Fore.RESET + f" {emojis.MOVIE} Set Plex Library Name\n"
        )
        print(
            Fore.GREEN
            + "5."
            + Fore.RESET
            + f" {emojis.INFO}  Test Connections (Plex + TMDb)\n"
        )
        print(Fore.GREEN + "6." + Fore.RESET + f" {emojis.BOOK} Show current values\n")
        print(Fore.RED + "7." + Fore.RESET + f" {emojis.BACK} Return to main menu\n")
        choice = read_menu_choice("Select an option (Esc to go back): ", set("1234567"))

        if choice == "ESC" or choice == "7":
            break
        if choice == "1":
            _prompt_update_config(
                "PLEX_TOKEN",
                "Enter new Plex Token (Esc to cancel): ",
                Fore.YELLOW + "1." + Fore.RESET + f" {emojis.KEY} Set Plex Token",
                "To find your token, view the XML of any item on Plex Web:\n"
                + Fore.BLUE
                + "https://app.plex.tv",
                tester=test_plex_connection,
            )
        elif choice == "2":

            _prompt_update_config(
                "PLEX_URL",
                "Enter new Plex URL (Esc to cancel): ",
                Fore.YELLOW + "2." + Fore.RESET + f" {emojis.URL} Set Plex URL",
                "You can find your Plex URL under Settings > Remote Access here:\n"
                + Fore.BLUE
                + "https://app.plex.tv/desktop/#!/settings/server",
                validator=validate_url,
                tester=test_plex_connection,
            )
        elif choice == "3":
            _prompt_update_config(
                "TMDB_API_KEY",
                "Enter new TMDb API Key (Esc to cancel): ",
                Fore.BLUE + "3." + Fore.RESET + f" {emojis.CLAPPER} Set TMDb API Key",
                "You can generate an API Key in your account settings:\n"
                + Fore.BLUE
                + "https://www.themoviedb.org/settings/api",
                tester=test_tmdb_connection,
            )
        elif choice == "4":
            clear_screen()
            print(
                Fore.CYAN
                + "4."
                + Fore.RESET
                + f" {emojis.MOVIE} Set Plex Library Name\n"
            )
            print(
                Fore.LIGHTBLACK_EX
                + "Select the library containing your movies."
                + Fore.RESET
                + "\n"
            )

            # Try to fetch libraries from Plex to allow selection
            plex_token = config.get("PLEX_TOKEN")
            plex_url = config.get("PLEX_URL")
            available_libs = []

            if plex_token and plex_url:
                try:
                    pm = PlexManager(plex_token, plex_url)
                    libs = pm.get_all_libraries()
                    available_libs = [lib.title for lib in libs]
                except Exception:
                    pass

            current_library = config.get("PLEX_LIBRARY", "Movies")
            if available_libs:
                print_grid(
                    available_libs,
                    columns=2,
                    padding=30,
                    title=Fore.GREEN + "Available Libraries:",
                )
                new_library = pick_from_list_case_insensitive(
                    f"\nSelect a library (current: {current_library}) (Esc to cancel): ",
                    available_libs,
                )
            else:
                new_library = read_line(
                    f"Enter Plex library name (current: {current_library}) (Esc to cancel): "
                )

            if new_library is None:
                continue
            new_library = new_library.strip()
            if not new_library:
                print(
                    Fore.RED
                    + f"{emojis.CROSS} Plex library name cannot be empty. Not saved.\n"
                )
                pause()
                continue
            config["PLEX_LIBRARY"] = new_library
            save_config(config)
            print()
            test_plex_connection(config)
            pause()
        elif choice == "5":
            print(Fore.CYAN + f"{emojis.INFO} Running connection tests...\n")
            test_plex_connection(config)
            test_tmdb_connection(config)
            pause()
        elif choice == "6":
            clear_screen()
            print(Fore.CYAN + f"{emojis.BOOK} Current Configuration:\n")

            def _print_kv(emoji, label, value):
                val_str = (
                    str(value)
                    if value
                    else Fore.LIGHTBLACK_EX + "(Not Set)" + Fore.RESET
                )
                print(f"{emoji} {Fore.WHITE}{label:<18}{Fore.RESET} : {val_str}")

            _print_kv(emojis.KEY, "Plex Token", config.get("PLEX_TOKEN"))
            _print_kv(emojis.URL, "Plex URL", config.get("PLEX_URL"))
            _print_kv(emojis.CLAPPER, "TMDb API Key", config.get("TMDB_API_KEY"))
            _print_kv(
                emojis.MOVIE, "Plex Library", config.get("PLEX_LIBRARY") or "Movies"
            )

            print(Fore.LIGHTBLACK_EX + "\n--- Connection Status ---" + Fore.RESET)
            last_plex = config.get("PLEX_LAST_TESTED", "")
            last_tmdb = config.get("TMDB_LAST_TESTED", "")

            _print_kv(
                emojis.INFO,
                " Plex Last Tested",
                (
                    (Fore.GREEN + last_plex + Fore.RESET)
                    if last_plex
                    else (Fore.RED + "Never" + Fore.RESET)
                ),
            )
            _print_kv(
                emojis.INFO,
                " TMDb Last Tested",
                (
                    (Fore.GREEN + last_tmdb + Fore.RESET)
                    if last_tmdb
                    else (Fore.RED + "Never" + Fore.RESET)
                ),
            )

            pause("\nPress Enter or Esc to return to the credentials menu...")
        else:
            print("Invalid choice. Try again.")
            pause()


def run_collection_builder():
    # Main interactive loop. Stays in a single while-loop and avoids repeating run_collection_builder().
    # Returns to main menu with `continue`.

    def pause(msg: str = "Press Enter or Esc to return to the menu..."):
        read_line(msg)

    while True:
        welcome()
        check_credentials()

        # Initialize TMDb helper early so it's available for tools
        tmdb = (
            TMDbSearch(config.get("TMDB_API_KEY"))
            if config.get("TMDB_API_KEY")
            else None
        )

        mode = handle_main_menu()

        if mode not in ("1", "2", "3", "4", "5", "6", "7"):
            print("Invalid selection. Please choose a valid menu option (1-7).")
            pause()
            continue

        if mode == "7":
            print(f"{emojis.WAVE} Goodbye!")
            return

        # Tools
        if mode == "4":
            features.run_missing_movies_tool(tmdb, config, pause)
            continue

        if mode == "5":
            features.run_poster_tool(config, pause)
            continue

        # Credentials settings
        if mode == "6":
            handle_credentials_menu()
            continue  # back to main loop

        # Collection Creation (modes 1-3)
        titles = []
        collection_name = None
        is_pre_matched = False
        smart_filter = None

        if mode == "1":
            collection_name, titles = features.run_franchise_mode(tmdb, pause)

        elif mode == "2":
            collection_name, titles, is_pre_matched, smart_filter = (
                features.run_studio_mode(tmdb, config, pause)
            )

        elif mode == "3":
            collection_name, titles = features.run_manual_mode(pause)

        # If user cancelled or no titles were found, go back to main menu
        if not collection_name or not titles:
            if collection_name is not None:  # Only show message if not a direct cancel
                print("No movies found for that input.")
                pause()
            continue

        ops.process_and_create_collection(
            collection_name,
            titles,
            config,
            pause,
            is_pre_matched=is_pre_matched,
            smart_filter=smart_filter,
        )


if __name__ == "__main__":
    check_system_requirements()
    run_collection_builder()

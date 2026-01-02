"""
This script uses:
- The TMDb API (via TMDbSearch) to fetch movie titles by keyword or collection.
- The PlexAPI to search for movies and create collections in the user's Plex library.
"""

import os
import json
import re
import sys
from datetime import datetime, timezone
import difflib
import requests

# Try to import scraping libraries
try:
    from bs4 import BeautifulSou5p
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

from colorama import init, Fore
import emojis
from plex_manager import PlexManager
from tmdb_search import TMDbSearch
from styling import print_plex_logo_ascii, PLEX_YELLOW
import constants
import scraper
from utils import (
    read_line,
    read_menu_choice,
    load_config,
    save_config,
    print_grid,
    pick_from_list_case_insensitive,
    extract_title_and_year,
    normalize_title,
    read_index_or_skip,
    UserAbort,
    is_escape
)


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
PLEX_TOKEN = config.get("PLEX_TOKEN")
PLEX_URL = config.get("PLEX_URL")
TMDB_API_KEY = config.get("TMDB_API_KEY")
MOCK_MODE = False  # Set to True to simulate Plex actions without making changes


def clear_screen():
    """Clears the terminal screen in a cross-platform way."""
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


def welcome():
    """Display welcome message and Plex logo, clearing the screen first."""
    clear_screen()
    print_plex_logo_ascii()
    print(PLEX_YELLOW + f"\n{emojis.MOVIE} Welcome to the Plex Toolkit!\n")


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
        Fore.YELLOW
        + "4."
        + Fore.RESET
        + f" {emojis.ART} Fix Posters & Backgrounds\n"
    )
    print(Fore.YELLOW + "5." + Fore.RESET + f" {emojis.CONFIGURE} Settings & Credentials\n")
    print(Fore.RED + "6." + Fore.RESET + f" {emojis.EXIT} Exit\n")
    print(
        Fore.LIGHTBLACK_EX
        + f"{emojis.INFO}  You can return to this menu after each collection is created.\n"
    )
    mode = read_menu_choice("Select an option (Esc to exit): ", set("123456"))
    if mode == "ESC":
        return "6"
    return mode


def handle_credentials_menu():
    """Displays and manages the credentials configuration submenu."""
    while True:
        clear_screen()
        print(PLEX_YELLOW + f"{emojis.CONFIGURE} CONFIGURE CREDENTIALS")
        print(Fore.YELLOW + "1." + Fore.RESET + f" {emojis.KEY} Set Plex Token\n")
        print(Fore.YELLOW + "2." + Fore.RESET + f" {emojis.URL} Set Plex URL\n")
        print(Fore.BLUE + "3." + Fore.RESET + f" {emojis.CLAPPER} Set TMDb API Key\n")
        print(Fore.CYAN + "4." + Fore.RESET + f" {emojis.MOVIE} Set Plex Library Name\n")
        print(Fore.GREEN + "5." + Fore.RESET + f" {emojis.INFO}  Test Connections (Plex + TMDb)\n")
        print(Fore.GREEN + "6." + Fore.RESET + f" {emojis.BOOK} Show current values\n")
        print(Fore.RED + "7." + Fore.RESET + f" {emojis.BACK} Return to main menu\n")
        choice = read_menu_choice("Select an option (Esc to go back): ", set("1234567"))

        def pause(msg: str = "Press Enter or Esc to return to the menu..."):
            read_line(msg)

        if choice == "ESC" or choice == "7":
            break
        if choice == "1":
            clear_screen()
            new_token = read_line("Enter new Plex Token (Esc to cancel): ")
            if new_token is None:
                continue
            new_token = new_token.strip()
            if not new_token:
                print(Fore.RED + f"{emojis.CROSS} Plex Token cannot be empty. Not saved.\n")
                pause()
                continue
            config["PLEX_TOKEN"] = new_token
            save_config(config)
            print(Fore.GREEN + f"{emojis.CHECK} Plex Token saved successfully!\n")
            test_plex_connection(config)
            pause()
        elif choice == "2":
            clear_screen()
            new_url = read_line("Enter new Plex URL (Esc to cancel): ")
            if new_url is None:
                continue
            new_url = new_url.strip()
            if not new_url:
                print(Fore.RED + f"{emojis.CROSS} Plex URL cannot be empty. Not saved.\n")
                pause()
                continue

            # Sanitize: remove spaces (common when copying from Plex UI: "IP : Port")
            new_url = new_url.replace(" ", "")
            # Auto-add http:// if missing
            if not new_url.lower().startswith("http://") and not new_url.lower().startswith("https://"):
                new_url = "http://" + new_url
                print(Fore.YELLOW + f"{emojis.INFO} Auto-formatted URL to: {new_url}")

            config["PLEX_URL"] = new_url
            save_config(config)
            print(Fore.GREEN + f"{emojis.CHECK} Plex URL saved successfully!\n")
            test_plex_connection(config)
            pause()
        elif choice == "3":
            clear_screen()
            new_key = read_line("Enter new TMDb API Key (Esc to cancel): ")
            if new_key is None:
                continue
            config["TMDB_API_KEY"] = new_key.strip()
            save_config(config)
            print(Fore.GREEN + f"{emojis.CHECK} TMDb API Key saved successfully!\n")
            test_tmdb_connection(config)
            pause()
        elif choice == "4":
            clear_screen()

            # Try to fetch libraries from Plex to allow selection
            plex_token = config.get("PLEX_TOKEN")
            plex_url = config.get("PLEX_URL")
            available_libs = []

            if plex_token and plex_url:
                try:
                    pm = PlexManager(plex_token, plex_url)
                    libs = pm.get_all_libraries()
                    available_libs = [l.title for l in libs]
                except Exception:
                    pass

            current_library = config.get("PLEX_LIBRARY", "Movies")
            if available_libs:
                print_grid(available_libs, columns=2, padding=30, title=Fore.GREEN + "Available Libraries:")
                new_library = pick_from_list_case_insensitive(f"\nSelect a library (current: {current_library}) (Esc to cancel): ", available_libs)
            else:
                new_library = read_line(f"Enter Plex library name (current: {current_library}) (Esc to cancel): ")

            if new_library is None:
                continue
            new_library = new_library.strip()
            if not new_library:
                print(Fore.RED + f"{emojis.CROSS} Plex library name cannot be empty. Not saved.\n")
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
            print(json.dumps(config, indent=4))
            last_plex = config.get("PLEX_LAST_TESTED", "")
            last_tmdb = config.get("TMDB_LAST_TESTED", "")
            print("\nConnection status:")
            print(f"- Plex last tested: {last_plex or 'never'}")
            print(f"- TMDb last tested: {last_tmdb or 'never'}")
            pause("\nPress Enter or Esc to return to the credentials menu...")
        else:
            print("Invalid choice. Try again.")
            pause()


def run_manual_mode(pause_fn):
    """Handles the manual movie entry mode. Returns (collection_name, titles) or (None, None)."""
    clear_screen()
    print(PLEX_YELLOW + f"{emojis.MANUAL} Manual Entry\n")
    collection_name = read_line(
        Fore.LIGHTBLACK_EX + "Enter a name for your new collection (Esc to cancel): " + Fore.RESET
    )
    if collection_name is None:
        return None, None
    collection_name = collection_name.strip()

    titles = []
    print("\nEnter movie titles one per line. Leave a blank line to finish:")
    while True:
        title = read_line("", allow_escape=True)
        if title is None:  # User pressed Esc
            print("Canceled. Returning to main menu.")
            pause_fn()
            return None, None
        if not title.strip():  # User entered a blank line
            break
        titles.append(title.strip())

    return collection_name, titles


def run_franchise_mode(tmdb, pause_fn):
    """Handles the franchise/series mode. Returns (collection_name, titles) or (None, None)."""
    clear_screen()
    print(PLEX_YELLOW + f"{emojis.FRANCHISE}  Franchise / Series Mode")
    titles = []

    if not tmdb:
        print(Fore.RED + f"\n{emojis.CROSS} TMDb API key not provided. Using fallback hardcoded titles.\n")
        franchises_data = load_fallback_data("Franchises")
        print_grid(franchises_data.keys(), columns=3, padding=28, title=Fore.GREEN + "Available Franchises:")
        choice = pick_from_list_case_insensitive("\n" + Fore.LIGHTBLACK_EX + "Select a franchise by name (Esc to cancel): ", franchises_data.keys())
        if choice is None:
            return None, None
        titles = franchises_data[choice]
    else:
        print_grid(constants.KNOWN_FRANCHISES.keys(), columns=3, padding=28, title=Fore.GREEN + "\nAvailable Collections (TMDb):")
        choice = pick_from_list_case_insensitive("\n" + Fore.LIGHTBLACK_EX + "Select a franchise by name (Esc to cancel): ", constants.KNOWN_FRANCHISES.keys())
        if choice is None:
            return None, None
        collection_id = constants.KNOWN_FRANCHISES[choice]
        try:
            titles = tmdb.get_movies_from_collection(collection_id)
        except Exception as e:
            print(Fore.RED + f"{emojis.CROSS} Error retrieving movies from TMDb collection. Please check your TMDb API key.")
            print(f"Exception: {e}")
            pause_fn()
            return None, None

    collection_name = read_line("Enter a name for your new collection (Esc to cancel): ")
    if collection_name is None:
        return None, None

    return collection_name.strip(), titles


def run_studio_mode(tmdb, config, pause_fn):
    """
    Handles the studio/keyword mode.
    Returns (collection_name, items, is_pre_matched)
    - items: list of titles (str) OR list of Plex objects
    - is_pre_matched: True if items are already Plex objects
    """
    clear_screen()
    print(PLEX_YELLOW + f"{emojis.STUDIO}  Studio / Collection Mode")

    print(Fore.GREEN + "1." + Fore.RESET + " Search Local Plex Library (Uses Plex API to find existing movies)")
    print(Fore.GREEN + "2." + Fore.RESET + " Discover via TMDb API (Standard search, may miss regional distribution titles)")
    if BS4_AVAILABLE:
        print(Fore.GREEN + "3." + Fore.RESET + " Import from Web List (Wikipedia/Official) (Best for complete lists like A24)")
    else:
        print(Fore.LIGHTBLACK_EX + "3. Import from Web List (Install 'beautifulsoup4' to enable)")

    valid_choices = set("123") if BS4_AVAILABLE else set("12")
    mode = read_menu_choice("\nSelect a method (Esc to cancel): ", valid_choices)
    if mode == "ESC":
        return None, None, False

    if mode == "1":
        # Plex Native Search
        plex_token = config.get("PLEX_TOKEN")
        plex_url = config.get("PLEX_URL")
        library_name = config.get("PLEX_LIBRARY", "Movies")

        try:
            pm = PlexManager(plex_token, plex_url)
            library = pm.get_movie_library(library_name)
            if not library: return None, None, False

            print(f"\n{emojis.INFO} Scanning Plex library for studios... (this may take a moment)")
            all_items = library.all()

            studio_counts = {}
            for item in all_items:
                if getattr(item, 'studio', None):
                    s = item.studio.strip()
                    if s:
                        studio_counts[s] = studio_counts.get(s, 0) + 1

            if studio_counts:
                sorted_studios = sorted(studio_counts.items(), key=lambda x: x[1], reverse=True)
                top_studios = [f"{s[0]} ({s[1]})" for s in sorted_studios[:45]]
                print(f"\n{Fore.GREEN}Top Studios in your Library:{Fore.RESET}")
                print_grid(top_studios, columns=3, padding=30, sort=False)
                print(f"{Fore.LIGHTBLACK_EX}(Found {len(studio_counts)} unique studios)")

            studio_query = read_line(f"\nEnter Studio Name (partial match allowed) (Esc to cancel): ")
            if not studio_query: return None, None, False
            studio_query = studio_query.strip()

            print(f"\nFiltering movies for studio '{studio_query}'...")
            query = studio_query.lower()
            items = [item for item in all_items if getattr(item, 'studio', None) and query in item.studio.lower()]

            return studio_query, items, True # True = these are objects, not titles
        except Exception as e:
            print(Fore.RED + f"Error searching Plex: {e}")
            pause_fn()
            return None, None, False

    if mode == "3":
        # Wikipedia Scraping
        print_grid(constants.WIKIPEDIA_URLS.keys(), columns=2, padding=40, title=Fore.GREEN + "\nSupported Studios:")
        choice = pick_from_list_case_insensitive("\n" + Fore.LIGHTBLACK_EX + "Select a studio (Esc to cancel): ", constants.WIKIPEDIA_URLS.keys())
        if choice is None:
            return None, None, False

        url = constants.WIKIPEDIA_URLS[choice]
        titles = scraper.scrape_wikipedia_film_list(url)

        if not titles:
            pause_fn()
            return None, None, False

        collection_name = read_line(f"Enter a name for your new collection (Default: {choice}): ")
        if collection_name is None: return None, None, False
        if not collection_name.strip(): collection_name = choice

        return collection_name.strip(), titles, False

    titles = []

    if not tmdb:
        print(Fore.RED + f"\n{emojis.CROSS} TMDb API key not provided. Using fallback hardcoded titles.\n")
        studios_data = load_fallback_data("Studios")
        print_grid(studios_data.keys(), columns=3, padding=24, title=Fore.GREEN + "Available Studios:")
        choice = pick_from_list_case_insensitive("\n" + Fore.LIGHTBLACK_EX + "Select a studio by name (Esc to cancel): ", studios_data.keys())
        if choice is None:
            return None, None, False
        titles = studios_data.get(choice, [])
    else:
        pretty_names = []
        pretty_to_key = {}
        for key in constants.STUDIO_MAP.keys():
            pretty = key.upper() if key in ("mcu", "dceu") else key.title()
            pretty_names.append(pretty)
            pretty_to_key[pretty.lower()] = key
        print_grid(pretty_names, columns=3, padding=24, title=Fore.GREEN + "\nAvailable Studios:")
        choice_pretty = pick_from_list_case_insensitive("\n" + Fore.LIGHTBLACK_EX + "Select a studio by name (Esc to cancel): ", pretty_names)
        if choice_pretty is None:
            return None, None, False
        norm_key = pretty_to_key[choice_pretty.lower()]
        studio_info = constants.STUDIO_MAP[norm_key]

        def fetch_movies_by_company_or_keyword(api_key, company_id=None, keyword_id=None):
            url = "https://api.themoviedb.org/3/discover/movie"
            params = {"api_key": api_key, "language": "en-US", "sort_by": "popularity.desc", "page": 1}

            # We will fetch two lists if both IDs are present to simulate an OR search
            queries = []
            if company_id:
                queries.append({"with_companies": company_id})
            if keyword_id:
                queries.append({"with_keywords": keyword_id})

            all_titles = set()

            for query_params in queries:
                # Merge base params with specific query params
                current_params = params.copy()
                current_params.update(query_params)
                current_params["page"] = 1

                while True:
                    print(f"Fetching page {current_params['page']}...", end='\r', flush=True)
                    resp = requests.get(url, params=current_params, timeout=10)
                    if resp.status_code == 401:
                        raise ValueError("TMDb authentication failed (invalid API key).")
                    if resp.status_code != 200:
                        snippet = ""
                        try:
                            snippet = resp.json().get("status_message", "")
                        except Exception:
                            snippet = resp.text[:200]
                        raise RuntimeError(f"TMDb error {resp.status_code}: {snippet}")
                    data = resp.json()
                    for m in data.get("results", []):
                        title = m.get("title")
                        date = m.get("release_date")
                        if title:
                            if date and len(date) >= 4:
                                all_titles.add(f"{title} ({date[:4]})")
                            else:
                                all_titles.add(title)
                    if data.get("page", 1) >= data.get("total_pages", 1):
                        break
                    current_params["page"] += 1

            print(" " * 40, end='\r', flush=True)
            return sorted(list(all_titles))

        try:
            api_key = config.get("TMDB_API_KEY")
            titles = fetch_movies_by_company_or_keyword(
                api_key,
                company_id=studio_info.get("company"),
                keyword_id=studio_info.get("keyword"),
            )
        except Exception as e:
            print(Fore.RED + f"{emojis.CROSS} Error retrieving movies from TMDb. Please check your TMDb API key.")
            print(f"Exception: {e}")
            pause_fn()
            return None, None, False

    collection_name = read_line("Enter a name for your new collection (Esc to cancel): ")
    if collection_name is None:
        return None, None, False

    return collection_name.strip(), titles, False


def format_plex_item(item) -> str:
    """Formats a Plex media item into 'Title (Year)'."""
    title = getattr(item, "title", str(item))
    year = getattr(item, "year", None)
    return f"{title} ({year})" if year else title


def pick_plex_match(raw_title: str, results):
    """Handles user selection when multiple Plex matches are found."""
    if not results:
        return None

    # Parse the search term
    search_title, search_year = extract_title_and_year(raw_title)
    search_norm = normalize_title(search_title)

    good_matches = []

    for item in results:
        item_title = item.title
        item_year = getattr(item, "year", None)
        item_norm = normalize_title(item_title)

        # 1. Year Check
        years_match = False
        if search_year and item_year:
            if abs(search_year - item_year) <= 1:
                years_match = True
            else:
                continue # Strict year mismatch

        # 2. Title Matching Logic
        is_match = False

        # A. Exact Normalized Match (High Confidence)
        if search_norm == item_norm:
            is_match = True

        # B. Subtitle Match (Item starts with Search)
        # e.g. Search: "Precious", Item: "Precious: Based on..."
        elif item_norm.startswith(search_norm) and (len(item_norm) == len(search_norm) or item_norm[len(search_norm)] == " "):
             is_match = True

        # C. Long Source Title (Search starts with Item)
        # e.g. Search: "The French Dispatch of...", Item: "The French Dispatch"
        elif search_norm.startswith(item_norm) and (len(search_norm) == len(item_norm) or search_norm[len(item_norm)] == " "):
             is_match = True

        # D. Fuzzy Fallback (only if years match exactly or very close)
        if not is_match and years_match:
            ratio = difflib.SequenceMatcher(None, search_norm, item_norm).ratio()
            # High threshold for fuzzy matches to avoid "Time" vs "No Time to Die"
            if ratio > 0.85:
                is_match = True

        if is_match:
            good_matches.append(item)

    if not good_matches:
        return None

    # Sort matches by title similarity so exact matches appear at the top
    good_matches.sort(key=lambda x: difflib.SequenceMatcher(None, search_norm, normalize_title(x.title)).ratio(), reverse=True)

    # Auto-select perfect matches
    if len(good_matches) > 0:
        best = good_matches[0]
        best_norm = normalize_title(best.title)

        # If we have a normalized exact match, take it.
        if best_norm == search_norm:
            return best

        # If we have a clear subtitle match (and it's the only good one, or significantly better)
        if best_norm.startswith(search_norm) and len(good_matches) == 1:
            return best

        # If we have a clear reverse subtitle match (French Dispatch)
        if search_norm.startswith(best_norm) and len(good_matches) == 1:
            return best

    if len(good_matches) == 1:
        # If we only found one candidate that passed our strict filters, accept it.
        return good_matches[0]
    else:
        print(f"\nMultiple Plex matches for '{raw_title}':")

    for i, item in enumerate(good_matches, 1):
        print(f"{i}. {format_plex_item(item)}")

    idx = read_index_or_skip(
        len(good_matches), "Pick a number + Enter, 's' to skip, or Esc to cancel: "
    )
    if idx is None:
        return None
    return good_matches[idx - 1]

def process_and_create_collection(collection_name, items, config, pause_fn, is_pre_matched=False):
    """Connects to Plex, finds movies, and creates the collection."""
    # MOCK mode short-circuit
    if MOCK_MODE:
        print("\n[MOCK MODE ENABLED] (Simulated)")
        pause_fn()
        return

    plex_token = config.get("PLEX_TOKEN")
    plex_url = config.get("PLEX_URL")
    if not plex_token or not plex_url:
        print(Fore.RED + f"\n{emojis.CROSS} Missing or invalid Plex Token or URL.")
        pause_fn()
        return

    try:
        plex_manager = PlexManager(plex_token, plex_url)
        library_name = (config.get("PLEX_LIBRARY") or "Movies").strip() or "Movies"
        library = plex_manager.get_movie_library(library_name)
        if not library:
            raise ConnectionError(f"Movie library '{library_name}' not found.")
    except Exception as e:
        print(Fore.RED + f"\n{emojis.CROSS} Could not connect to Plex: {e}")
        print("Please make sure your Plex Token and URL are correct.\n")
        pause_fn()
        return

    found_movies, not_found, matched_pairs = [], [], []
    seen_rating_keys = set()

    if is_pre_matched:
        # Items are already Plex objects
        found_movies = items
    else:
        # Items are titles (strings), need to search
        titles = items
        try:
            for raw in titles:
                title, year = extract_title_and_year(raw)
                try:
                    # Search by title only to allow for year discrepancies (handled in pick_plex_match)
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
            pause_fn()
            return

    print(f"\nFound {len(found_movies)} movies in Plex.")
    if not is_pre_matched and not_found:
        print(f"Couldn’t find {len(not_found)}:")
        for nf in not_found:
            print(f"- {nf}")

    if not found_movies:
        print(f"{emojis.CROSS} No valid matches found — collection not created.")
        pause_fn()
        return

    print("\nMovies to add to collection:")
    for i, mv in enumerate(found_movies, 1):
        print(f"{i}. {format_plex_item(mv)}")

    if not is_pre_matched:
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
        pause_fn()
        return

    try:
        library.createCollection(collection_name, items=found_movies)
        print(f"\n{emojis.CHECK} Created collection '{collection_name}' with {len(found_movies)} movies.")
    except Exception as e:
        print(Fore.RED + f"\n{emojis.CROSS} Failed to create collection in Plex: {e}")

    pause_fn()

def run_poster_tool(config, pause_fn):
    """Sub-menu for fixing posters using TMDb."""
    clear_screen()

    print(PLEX_YELLOW + f"{emojis.ART}  Fix Posters & Backgrounds")
    print("This tool uses the Plex API to automatically select TMDb-sourced artwork for your items.\n")

    print(Fore.YELLOW + "1." + Fore.RESET + " Fix Posters & Backgrounds for a specific Collection")
    print(Fore.YELLOW + "2." + Fore.RESET + " Fix Posters & Backgrounds for the ENTIRE Library (Slow)")
    print(Fore.RED + "3." + Fore.RESET + f" {emojis.BACK} Return to main menu\n")

    choice = read_menu_choice("Select an option: ", set("123"))

    if choice == "3" or choice == "ESC":
        return

    # Connect to Plex
    plex_token = config.get("PLEX_TOKEN")
    plex_url = config.get("PLEX_URL")

    try:
        pm = PlexManager(plex_token, plex_url)

        # Select Library
        print("\nFetching libraries from Plex...")
        libraries = pm.get_all_libraries()
        if not libraries:
            print(Fore.RED + "No libraries found.")
            pause_fn()
            return

        lib_names = [lib.title for lib in libraries]
        print_grid(lib_names, columns=3, padding=28, title=Fore.GREEN + "Available Libraries:")

        choice_name = pick_from_list_case_insensitive("\n" + Fore.LIGHTBLACK_EX + "Select a library (Esc to cancel): ", lib_names)
        if not choice_name: return

        library = next(l for l in libraries if l.title == choice_name)

    except Exception as e:
        print(Fore.RED + f"Error connecting to Plex: {e}")
        pause_fn()
        return

    items_to_process = []

    if choice == "1":
        print("\nFetching collections from Plex... (this may take a moment)")
        collections = library.collections()

        if not collections:
            print(Fore.YELLOW + "No collections found in this library.")
            pause_fn()
            return

        col_names = [c.title for c in collections]
        print_grid(col_names, columns=3, padding=28, title=Fore.GREEN + "Available Collections:")

        col_name = pick_from_list_case_insensitive("\n" + Fore.LIGHTBLACK_EX + "Select a collection by name (Esc to cancel): ", col_names)
        if not col_name: return

        try:
            # Find the collection object matching the selected name
            target_col = next((c for c in collections if c.title == col_name), None)
            if target_col:
                items_to_process = target_col.items()
                print(f"\nFound {len(items_to_process)} movies in collection '{target_col.title}'.")
        except Exception as e:
            print(Fore.RED + f"\nError accessing collection: {e}")
            pause_fn()
            return
    elif choice == "2":
        print("\nFetching all items from library... this may take a moment.")
        items_to_process = library.all()

    if items_to_process:
        total = len(items_to_process)
        print(f"Processing {total} items...\n")
        for i, item in enumerate(items_to_process, 1):
            print(f"[{i}/{total}] Checking '{item.title}'...")
            pm.set_tmdb_poster(item)
            pm.set_tmdb_art(item)
        print(f"\n{emojis.CHECK} Finished processing artwork.")

    pause_fn()

def run_collection_builder():
    # Main interactive loop. Stays in a single while-loop and avoids repeating run_collection_builder().
    # Returns to main menu with `continue`.

    def pause(msg: str = "Press Enter or Esc to return to the menu..."):
        read_line(msg)

    while True:
        welcome()
        check_credentials()

        mode = handle_main_menu()

        if mode not in ("1", "2", "3", "4", "5", "6"):
            print("Invalid selection. Please choose a valid menu option (1-6).")
            pause()
            continue

        if mode == "6":
            print(f"{emojis.WAVE} Goodbye!")
            return

        # Tools
        if mode == "4":
            run_poster_tool(config, pause)
            continue

        # Credentials settings
        if mode == "5":
            handle_credentials_menu()
            continue  # back to main loop

        # Collection Creation (modes 1-3)
        titles = []
        collection_name = None
        is_pre_matched = False

        # Prepare TMDb helper if key present
        tmdb = (
            TMDbSearch(config.get("TMDB_API_KEY"))
            if config.get("TMDB_API_KEY")
            else None
        )

        if mode == "1":
            collection_name, titles = run_franchise_mode(tmdb, pause)

        elif mode == "2":
            collection_name, titles, is_pre_matched = run_studio_mode(tmdb, config, pause)

        elif mode == "3":
            collection_name, titles = run_manual_mode(pause)


        # If user cancelled or no titles were found, go back to main menu
        if not collection_name or not titles:
            if collection_name is not None:  # Only show message if not a direct cancel
                print("No movies found for that input.")
                pause()
            continue


        process_and_create_collection(collection_name, titles, config, pause, is_pre_matched=is_pre_matched)


def load_fallback_data(section):
    # Load fallback data for a given section from fallback_collections.json.
    fallback_path = os.path.join(os.path.dirname(__file__), "fallback_collections.json")
    with open(fallback_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get(section, {})


if __name__ == "__main__":
    run_collection_builder()

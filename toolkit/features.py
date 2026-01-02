from colorama import Fore
from toolkit import emojis
from toolkit import constants
from toolkit.services import scraper
from toolkit.services.plex_manager import PlexManager
from toolkit.utils import (
    read_line,
    read_menu_choice,
    print_grid,
    pick_from_list_case_insensitive,
    load_fallback_data,
)


def run_manual_mode(pause_fn):
    """Handles the manual movie entry mode."""
    print(Fore.YELLOW + f"{emojis.MANUAL} Manual Entry\n")
    collection_name = read_line(
        Fore.LIGHTBLACK_EX
        + "Enter a name for your new collection (Esc to cancel): "
        + Fore.RESET
    )
    if collection_name is None:
        return None, None
    collection_name = collection_name.strip()

    titles = []
    print("\nEnter movie titles one per line. Leave a blank line to finish:")
    while True:
        title = read_line("", allow_escape=True)
        if title is None:
            print("Canceled.")
            pause_fn()
            return None, None
        if not title.strip():
            break
        titles.append(title.strip())

    return collection_name, titles


def run_franchise_mode(tmdb, pause_fn):
    """Handles the franchise/series mode."""
    print(Fore.YELLOW + f"{emojis.FRANCHISE}  Franchise / Series Mode")
    titles = []

    if not tmdb:
        print(
            Fore.RED
            + f"\n{emojis.CROSS} TMDb API key not provided. Using fallback data.\n"
        )
        franchises_data = load_fallback_data("Franchises")
        print_grid(
            franchises_data.keys(),
            columns=3,
            padding=28,
            title=Fore.GREEN + "Available Franchises:",
        )
        choice = pick_from_list_case_insensitive(
            "\n" + Fore.LIGHTBLACK_EX + "Select a franchise (Esc to cancel): ",
            franchises_data.keys(),
        )
        if choice is None:
            return None, None
        titles = franchises_data[choice]
    else:
        print_grid(
            constants.KNOWN_FRANCHISES.keys(),
            columns=3,
            padding=28,
            title=Fore.GREEN + "\nAvailable Collections (TMDb):",
        )
        choice = pick_from_list_case_insensitive(
            "\n" + Fore.LIGHTBLACK_EX + "Select a franchise (Esc to cancel): ",
            constants.KNOWN_FRANCHISES.keys(),
        )
        if choice is None:
            return None, None
        try:
            titles = tmdb.get_movies_from_collection(constants.KNOWN_FRANCHISES[choice])
        except Exception as e:
            print(Fore.RED + f"{emojis.CROSS} Error retrieving movies: {e}")
            pause_fn()
            return None, None

    collection_name = read_line(
        "Enter a name for your new collection (Esc to cancel): "
    )
    if collection_name is None:
        return None, None

    return collection_name.strip(), titles


def run_studio_mode(tmdb, config, pause_fn):
    """Handles the studio/keyword mode."""
    print(Fore.YELLOW + f"{emojis.STUDIO}  Studio / Collection Mode")
    print(Fore.GREEN + "1." + Fore.RESET + " Search Local Plex Library")
    print(Fore.GREEN + "2." + Fore.RESET + " Discover via TMDb API")

    bs4_avail = scraper.BeautifulSoup is not None
    if bs4_avail:
        print(Fore.GREEN + "3." + Fore.RESET + " Import from Web List (Wikipedia)")
    else:
        print(
            Fore.LIGHTBLACK_EX
            + "3. Import from Web List (Install 'beautifulsoup4' to enable)"
        )

    mode = read_menu_choice(
        "\nSelect a method (Esc to cancel): ", set("123") if bs4_avail else set("12")
    )
    if mode == "ESC":
        return None, None, False

    if mode == "1":
        # Plex Native Search
        try:
            pm = PlexManager(config.get("PLEX_TOKEN"), config.get("PLEX_URL"))
            library = pm.get_movie_library(config.get("PLEX_LIBRARY", "Movies"))
            if not library:
                return None, None, False

            print(f"\n{emojis.INFO} Scanning Plex library for studios...")
            all_items = library.all()
            studio_query = read_line(
                "\nEnter Studio Name (partial match allowed) (Esc to cancel): "
            )
            if not studio_query:
                return None, None, False

            print(f"\nFiltering movies for studio '{studio_query}'...")
            items = [
                item
                for item in all_items
                if getattr(item, "studio", None)
                and studio_query.lower() in item.studio.lower()
            ]
            return studio_query.strip(), items, True
        except Exception as e:
            print(Fore.RED + f"Error searching Plex: {e}")
            pause_fn()
            return None, None, False

    if mode == "3":
        # Wikipedia
        print_grid(
            constants.WIKIPEDIA_URLS.keys(),
            columns=2,
            padding=40,
            title=Fore.GREEN + "\nSupported Studios:",
        )
        choice = pick_from_list_case_insensitive(
            "\n" + Fore.LIGHTBLACK_EX + "Select a studio (Esc to cancel): ",
            constants.WIKIPEDIA_URLS.keys(),
        )
        if choice is None:
            return None, None, False

        titles = scraper.scrape_wikipedia_film_list(constants.WIKIPEDIA_URLS[choice])
        if not titles:
            pause_fn()
            return None, None, False

        collection_name = read_line(
            f"Enter a name for your new collection (Default: {choice}): "
        )
        if not collection_name or not collection_name.strip():
            collection_name = choice
        return collection_name.strip(), titles, False

    # Mode 2: TMDb
    titles = []
    if not tmdb:
        print(
            Fore.RED
            + f"\n{emojis.CROSS} TMDb API key not provided. Using fallback data.\n"
        )
        studios_data = load_fallback_data("Studios")
        choice = pick_from_list_case_insensitive(
            "\n" + Fore.LIGHTBLACK_EX + "Select a studio (Esc to cancel): ",
            studios_data.keys(),
        )
        if choice is None:
            return None, None, False
        titles = studios_data.get(choice, [])
    else:
        pretty_names = [
            k.upper() if k in ("mcu", "dceu") else k.title()
            for k in constants.STUDIO_MAP.keys()
        ]
        print_grid(
            pretty_names,
            columns=3,
            padding=24,
            title=Fore.GREEN + "\nAvailable Studios:",
        )
        choice_pretty = pick_from_list_case_insensitive(
            "\n" + Fore.LIGHTBLACK_EX + "Select a studio (Esc to cancel): ",
            pretty_names,
        )
        if choice_pretty is None:
            return None, None, False

        studio_info = constants.STUDIO_MAP[choice_pretty.lower()]
        try:
            titles = tmdb.discover_movies(
                company_id=studio_info.get("company"),
                keyword_id=studio_info.get("keyword"),
            )
        except Exception as e:
            print(Fore.RED + f"{emojis.CROSS} Error retrieving movies from TMDb: {e}")
            pause_fn()
            return None, None, False

    collection_name = read_line(
        "Enter a name for your new collection (Esc to cancel): "
    )
    if collection_name is None:
        return None, None, False
    return collection_name.strip(), titles, False


def run_poster_tool(config, pause_fn):
    """Sub-menu for fixing posters."""
    print(Fore.YELLOW + f"{emojis.ART}  Fix Posters & Backgrounds")
    print(Fore.YELLOW + "1." + Fore.RESET + " Fix Posters for a specific Collection")
    print(
        Fore.YELLOW + "2." + Fore.RESET + " Fix Posters for the ENTIRE Library (Slow)"
    )
    print(Fore.RED + "3." + Fore.RESET + f" {emojis.BACK} Return to main menu\n")

    choice = read_menu_choice("Select an option: ", set("123"))
    if choice == "3" or choice == "ESC":
        return

    try:
        pm = PlexManager(config.get("PLEX_TOKEN"), config.get("PLEX_URL"))
        library = pm.get_movie_library(config.get("PLEX_LIBRARY", "Movies"))
        if not library:
            return

        items_to_process = []
        if choice == "1":
            col_names = [c.title for c in library.collections()]
            col_name = pick_from_list_case_insensitive(
                "\n" + Fore.LIGHTBLACK_EX + "Select a collection (Esc to cancel): ",
                col_names,
            )
            if not col_name:
                return
            items_to_process = library.collection(col_name).items()
        elif choice == "2":
            items_to_process = library.all()

        for i, item in enumerate(items_to_process, 1):
            print(f"[{i}/{len(items_to_process)}] Checking '{item.title}'...")
            pm.set_tmdb_poster(item)
            pm.set_tmdb_art(item)
    except Exception as e:
        print(Fore.RED + f"Error: {e}")
    pause_fn()

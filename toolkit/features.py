from collections import Counter
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
    clear_screen,
)


def run_manual_mode(pause_fn):
    """Handles the manual movie entry mode."""
    clear_screen()
    print()
    print(Fore.YELLOW + f"{emojis.MANUAL} Manual Entry\n")
    print(
        Fore.LIGHTBLACK_EX
        + "Create a custom collection by manually typing a list of movie titles."
        + Fore.RESET
        + "\n"
    )
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
    clear_screen()
    print()
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
    clear_screen()
    print()
    print(Fore.YELLOW + f"{emojis.STUDIO}  Studio / Collection Mode\n")
    print(
        Fore.LIGHTBLACK_EX
        + "Create collections by Studio (e.g. A24, Pixar), Network (e.g. HBO, Netflix), or Universe (e.g. MCU, DCEU)."
        + Fore.RESET
        + "\n"
    )
    print(Fore.GREEN + "1." + Fore.RESET + f" {emojis.URL} Discover via TMDb API\n")

    bs4_avail = scraper.BeautifulSoup is not None
    if bs4_avail:
        print(
            Fore.GREEN
            + "2."
            + Fore.RESET
            + f" {emojis.BOOK} Import from Online Lists (Wikipedia/Criterion)\n"
        )
    else:
        print(
            Fore.LIGHTBLACK_EX
            + f"2. {emojis.BOOK} Import from Online Lists (Install 'beautifulsoup4' to enable)\n"
        )
    print(
        Fore.GREEN + "3." + Fore.RESET + f" {emojis.MOVIE} Search Local Plex Library\n"
    )
    print(
        Fore.GREEN
        + "4."
        + Fore.RESET
        + f" {emojis.FRANCHISE} Use Built-in Lists (Offline)\n"
    )

    mode = read_menu_choice(
        "Select a method (Esc to cancel): ", set("1234") if bs4_avail else set("134")
    )
    if mode == "ESC" or mode is None:
        return None, None, False, None

    # Option 1: TMDb (Moved from end of function)
    if mode == "1":
        clear_screen()
        print(Fore.GREEN + "1." + Fore.RESET + f" {emojis.URL} Discover via TMDb API\n")
        print(
            Fore.LIGHTBLACK_EX
            + "Best for official Studios (Ghibli), Networks (HBO), and Universes (MCU)."
            + Fore.RESET
            + "\n"
        )
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
                return None, None, False, None
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
                return None, None, False, None

            studio_info = constants.STUDIO_MAP[choice_pretty.lower()]
            try:
                titles = tmdb.discover_movies(
                    company_id=studio_info.get("company"),
                    keyword_id=studio_info.get("keyword"),
                )
            except Exception as e:
                print(
                    Fore.RED + f"{emojis.CROSS} Error retrieving movies from TMDb: {e}"
                )
                pause_fn()
                return None, None, False, None

        collection_name = read_line(
            "Enter a name for your new collection (Esc to cancel): "
        )
        if collection_name is None:
            return None, None, False, None
        return collection_name.strip(), titles, False, None

    # Option 2: Wikipedia (Moved from mode 3)
    if mode == "2":
        clear_screen()
        print(
            Fore.GREEN
            + "2."
            + Fore.RESET
            + f" {emojis.BOOK} Import from Online Lists (Wikipedia/Criterion)\n"
        )
        print(
            Fore.LIGHTBLACK_EX
            + "Best for frequently updated lists (e.g. Criterion, Academy Award Winners)."
            + Fore.RESET
            + "\n"
        )
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
            return None, None, False, None

        titles = scraper.scrape_wikipedia_film_list(constants.WIKIPEDIA_URLS[choice])
        if not titles:
            pause_fn()
            return None, None, False, None

        collection_name = read_line(
            f"Enter a name for your new collection (Default: {choice}): "
        )
        if not collection_name or not collection_name.strip():
            collection_name = choice
        return collection_name.strip(), titles, False, None

    # Option 3: Plex Native (Moved from mode 1)
    if mode == "3":
        clear_screen()
        print(
            Fore.GREEN
            + "3."
            + Fore.RESET
            + f" {emojis.MOVIE} Search Local Plex Library\n"
        )
        try:
            pm = PlexManager(config.get("PLEX_TOKEN"), config.get("PLEX_URL"))
            library = pm.get_movie_library(config.get("PLEX_LIBRARY", "Movies"))
            if not library:
                return None, None, False, None

            print(f"\n{emojis.INFO} Scanning Plex library for studios...")
            all_items = library.all()

            # Count studios to show popular ones
            studio_counts = Counter()
            for item in all_items:
                if getattr(item, "studio", None):
                    studio_counts[item.studio] += 1

            top_studios = [f"{s} ({c})" for s, c in studio_counts.most_common(20)]
            if top_studios:
                print_grid(
                    top_studios,
                    columns=2,
                    padding=35,
                    title=Fore.GREEN + "\nTop Studios in Library:",
                )

            print(
                Fore.LIGHTBLACK_EX
                + "\nEnter a name from above or any other studio to search."
                + Fore.RESET
            )
            studio_query = read_line(
                "\nEnter Studio Name (partial match allowed) (Esc to cancel): "
            )
            if not studio_query:
                return None, None, False, None

            print(f"\nFiltering movies for studio '{studio_query}'...")
            items = [
                item
                for item in all_items
                if getattr(item, "studio", None)
                and studio_query.lower() in item.studio.lower()
            ]

            # Ask for Smart Collection
            print(f"\nFound {len(items)} movies matching '{studio_query}'.")
            smart_choice = read_line(
                f"Create as a {Fore.CYAN}Smart Collection{Fore.RESET} (auto-updates)? (y/n): "
            )
            smart_filter = None
            if smart_choice and smart_choice.lower() == "y":
                # Try to resolve Studio ID for better compatibility
                try:
                    studio_choices = library.listFilterChoices("studio")
                    clean_query = studio_query.strip().lower()
                    # Try exact match first
                    matched = next(
                        (c for c in studio_choices if c.title.lower() == clean_query),
                        None,
                    )
                    # Try partial match if exact fails
                    if not matched:
                        matched = next(
                            (
                                c
                                for c in studio_choices
                                if clean_query in c.title.lower()
                            ),
                            None,
                        )
                        if matched:
                            smart_filter = {"studio": matched.key}
                            # Update name to the official one
                            studio_query = matched.title
                    else:
                        smart_filter = {"studio": studio_query.strip()}
                except Exception:
                    smart_filter = {"studio": studio_query.strip()}

            return studio_query.strip(), items, True, smart_filter
        except Exception as e:
            print(Fore.RED + f"Error searching Plex: {e}")
            pause_fn()
            return None, None, False, None

    # Option 4: Fallback / Offline
    if mode == "4":
        clear_screen()
        print(
            Fore.GREEN
            + "4."
            + Fore.RESET
            + f" {emojis.FRANCHISE} Use Built-in Lists (Offline)\n"
        )
        studios_data = load_fallback_data("Studios")
        print_grid(
            studios_data.keys(),
            columns=3,
            padding=24,
            title=Fore.GREEN + "Available Studios:",
        )
        choice = pick_from_list_case_insensitive(
            "\n" + Fore.LIGHTBLACK_EX + "Select a studio (Esc to cancel): ",
            studios_data.keys(),
        )
        if choice is None:
            return None, None, False, None
        titles = studios_data.get(choice, [])

        collection_name = read_line(
            f"Enter a name for your new collection (Default: {choice}): "
        )
        if not collection_name or not collection_name.strip():
            collection_name = choice
        return collection_name.strip(), titles, False, None


def run_poster_tool(config, pause_fn):
    """Sub-menu for fixing posters."""
    clear_screen()
    print()
    print(Fore.YELLOW + f"{emojis.ART}  Fix Posters & Backgrounds\n")
    print(
        Fore.LIGHTBLACK_EX
        + "This tool scans your library and applies the official TMDb artwork.\n"
        + "Items with locked (custom) posters or backgrounds will be skipped."
        + Fore.RESET
        + "\n"
    )
    print(Fore.YELLOW + "1." + Fore.RESET + " Fix Posters for a specific Collection\n")
    print(
        Fore.YELLOW + "2." + Fore.RESET + " Fix Posters for the ENTIRE Library (Slow)\n"
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
            print(f"\n{emojis.INFO} Fetching collections from Plex...")
            col_names = sorted([c.title for c in library.collections()])
            if not col_names:
                print(Fore.YELLOW + "No collections found.")
                pause_fn()
                return

            print_grid(
                col_names,
                columns=2,
                padding=30,
                title=Fore.GREEN + "Available Collections:",
            )
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

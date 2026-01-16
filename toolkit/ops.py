import difflib
import requests
from urllib.parse import urlencode
from colorama import Fore
from toolkit import emojis
from toolkit import constants
from toolkit.progress import ProgressBar
from toolkit.services.plex_manager import get_plex_manager
from toolkit.utils import (
    extract_title_and_year,
    normalize_title,
    read_index_or_skip,
    print_grid,
    read_line,
    read_menu_choice,
    UserAbort,
)


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
                continue  # Strict year mismatch

        # 2. Title Matching Logic
        # Exact match, or one is a prefix of the other (e.g. "Alien" vs "Alien 3")
        is_match = (
            search_norm == item_norm
            or item_norm.startswith(f"{search_norm} ")
            or search_norm.startswith(f"{item_norm} ")
        )

        if not is_match and years_match:
            ratio = difflib.SequenceMatcher(None, search_norm, item_norm).ratio()
            if ratio > 0.85:
                is_match = True

        if is_match:
            good_matches.append(item)

    if not good_matches:
        return None

    # Sort by title similarity
    good_matches.sort(
        key=lambda x: difflib.SequenceMatcher(
            None, search_norm, normalize_title(x.title)
        ).ratio(),
        reverse=True,
    )

    # If only one match, or the best match is an exact title match, return it automatically.
    if len(good_matches) == 1 or normalize_title(good_matches[0].title) == search_norm:
        return good_matches[0]

    print(f"\nMultiple Plex matches for '{raw_title}':")
    for i, item in enumerate(good_matches, 1):
        print(f"{i}. {format_plex_item(item)}")

    idx = read_index_or_skip(
        len(good_matches), "Pick a number + Enter, 's' to skip, or Esc to cancel: "
    )
    if idx is None:
        return None
    return good_matches[idx - 1]


def _create_smart_collection_fallback(library, collection_name, smart_filter):
    """Fallback to create a smart collection via direct API call for older plexapi versions."""
    server = library._server
    section_id = library.key

    # Prepare filter params (ensure type=1 for movies)
    filter_params = {"type": constants.PLEX_MEDIA_TYPE_MOVIE}
    filter_params.update(smart_filter)

    # Construct the internal URI for the filter
    path = f"/library/sections/{section_id}/all"
    query = urlencode(filter_params)
    uri_path = f"{path}?{query}"

    # Full server:// URI
    server_uri = (
        f"server://{server.machineIdentifier}/com.plexapp.plugins.library{uri_path}"
    )

    # Create collection params
    create_params = {
        "title": collection_name,
        "smart": 1,
        "sectionId": section_id,
        "type": constants.PLEX_MEDIA_TYPE_MOVIE,
        "uri": server_uri,
    }

    url = server.url("/library/collections")
    res = requests.post(url, headers=server._headers(), params=create_params)

    if res.status_code >= 400:
        raise Exception(f"HTTP {res.status_code}: {res.text}")

    print(
        f"\n{emojis.CHECK} Smart Collection '{collection_name}' created successfully (Fallback)!"
    )


def _process_smart_collection(library, collection_name, smart_filter, pause_fn):
    """Handles the creation logic for a smart collection."""
    print(f"\n{emojis.INFO} Creating Smart Collection with filter: {smart_filter}")

    # Check if it exists
    existing = library.search(
        title=collection_name, libtype=constants.PLEX_LIBTYPE_COLLECTION
    )
    if existing:
        print(
            Fore.YELLOW
            + f"\n{emojis.INFO} Collection '{collection_name}' already exists."
            + Fore.RESET
        )
        is_smart = getattr(existing[0], constants.COLLECTION_ATTR_SMART, False)
        type_label = "Smart" if is_smart else "Static"
        print(
            Fore.LIGHTBLACK_EX
            + f"The existing collection is {type_label}. You cannot append a Smart rule to it."
            + Fore.RESET
        )

        confirm = read_line("Overwrite existing collection? (y/n): ")
        if confirm and confirm.lower() == "y":
            print(Fore.YELLOW + f"Deleting '{collection_name}'..." + Fore.RESET)
            existing[0].delete()
        else:
            print("Canceled.")
            return

    try:
        library.createSmartCollection(collection_name, **smart_filter)
        print(
            f"\n{emojis.CHECK} Smart Collection '{collection_name}' created successfully!"
        )
    except AttributeError as e:
        if "createSmartCollection" in str(e):
            print(
                Fore.YELLOW
                + f"\n{emojis.INFO} 'plexapi' is outdated. Attempting fallback method..."
                + Fore.RESET
            )
            try:
                _create_smart_collection_fallback(
                    library, collection_name, smart_filter
                )
            except Exception as fallback_error:
                print(Fore.RED + f"\n{emojis.CROSS} Fallback failed: {fallback_error}")
                print(Fore.RED + "Please run: pip install --upgrade plexapi")
                fallback = read_line(
                    Fore.YELLOW
                    + "\nCreate a standard (static) collection instead? (y/n): "
                    + Fore.RESET
                )
                if not fallback or fallback.lower() != "y":
                    return
                # Let the main function proceed to static creation
                print(f"\n{emojis.INFO} Proceeding with static collection...")
                return False  # Indicates smart creation failed, static is fallback
        else:
            print(Fore.RED + f"\n{emojis.CROSS} Failed to create Smart Collection: {e}")
    except Exception as e:
        print(Fore.RED + f"\n{emojis.CROSS} Failed to create Smart Collection: {e}")

    return True  # Indicates smart collection was handled (created or failed with no fallback)


def _handle_existing_collection(library, collection_name, found_movies, pause_fn):
    """
    Checks if a collection exists and handles user interaction (Append/Overwrite).
    Returns 'proceed' if the caller should create a new collection (or overwrite).
    Returns 'stop' if the action is complete (appended) or cancelled.
    """
    existing_collections = library.search(
        title=collection_name, libtype=constants.PLEX_LIBTYPE_COLLECTION
    )
    existing_collection = next(
        (c for c in existing_collections if c.title.lower() == collection_name.lower()),
        None,
    )

    if not existing_collection:
        return "proceed"

    is_smart = getattr(existing_collection, constants.COLLECTION_ATTR_SMART, False)
    type_label = "Smart" if is_smart else "Static"
    print(
        Fore.YELLOW
        + f"\n{emojis.INFO} Collection '{existing_collection.title}' already exists (Type: {type_label})."
        + Fore.RESET
    )

    if is_smart:
        print(
            Fore.LIGHTBLACK_EX
            + "You cannot append items to a Smart Collection. You can only overwrite it with a new static collection."
            + Fore.RESET
        )
        choice = read_menu_choice(
            "Do you want to (O)verwrite, or (C)ancel? ", set("oOcC")
        )
    else:
        choice = read_menu_choice(
            "Do you want to (A)ppend, (O)verwrite, or (C)ancel? ", set("aAoOcC")
        )

    if choice in ("c", "C", "ESC"):
        print("Canceled.")
        pause_fn()
        return "stop"

    if choice in ("a", "A"):
        try:
            current_items = existing_collection.items()
            current_keys = {str(x.ratingKey) for x in current_items}

            to_add = []
            skipped = 0
            for movie in found_movies:
                if str(movie.ratingKey) not in current_keys:
                    to_add.append(movie)
                else:
                    skipped += 1

            if to_add:
                existing_collection.addItems(to_add)
                print(
                    f"\n{emojis.CHECK} Added {len(to_add)} new movies to '{existing_collection.title}'."
                )
            else:
                print(
                    f"\n{emojis.CHECK} No new movies to add. All items were already in '{existing_collection.title}'."
                )

            if skipped > 0:
                print(
                    Fore.LIGHTBLACK_EX
                    + f"{skipped} movies were already in the collection."
                    + Fore.RESET
                )
        except Exception as e:
            print(Fore.RED + f"\n{emojis.CROSS} Failed to append items: {e}")

        pause_fn()
        return "stop"

    if choice in ("o", "O"):
        print(
            Fore.YELLOW
            + f"\n{emojis.INFO} Deleting existing collection '{existing_collection.title}'..."
            + Fore.RESET
        )
        existing_collection.delete()
        return "proceed"

    return "stop"


def _match_movies_in_plex(library, items):
    """Finds Plex items corresponding to a list of titles."""
    found_movies = []
    not_found = []
    seen_rating_keys = set()

    total = len(items)
    print(f"\n{emojis.INFO} Searching Plex for {total} items...")

    with ProgressBar(
        total,
        prefix=f"{emojis.INFO} Matching movies",
        suffix="items processed",
    ) as progress:
        for raw in items:
            title, _ = extract_title_and_year(raw)
            progress.update(custom_message=f"Searching: {title[:35]}")
            try:
                results = library.search(title)
                chosen = pick_plex_match(raw, results)
                if chosen is None:
                    not_found.append(raw)
                    continue
                rating_key = str(getattr(chosen, "ratingKey", ""))
                if rating_key and rating_key not in seen_rating_keys:
                    seen_rating_keys.add(rating_key)
                    found_movies.append(chosen)
            except Exception as e:
                print(f"\nError searching for '{raw}': {e}")
                not_found.append(raw)

    return found_movies, not_found


def process_and_create_collection(
    collection_name, items, config, pause_fn, is_pre_matched=False, smart_filter=None
):
    """Connects to Plex, finds movies, and creates the collection."""
    plex_token = config.get(constants.CONFIG_PLEX_TOKEN)
    plex_url = config.get(constants.CONFIG_PLEX_URL)
    if not plex_token or not plex_url:
        print(Fore.RED + f"\n{emojis.CROSS} Missing or invalid Plex Token or URL.")
        pause_fn()
        return

    try:
        plex_manager = get_plex_manager(plex_token, plex_url)
        library_name = (
            config.get(constants.CONFIG_PLEX_LIBRARY) or constants.DEFAULT_LIBRARY_NAME
        ).strip() or constants.DEFAULT_LIBRARY_NAME
        library = plex_manager.get_movie_library(library_name)
        if not library:
            raise ConnectionError(f"Movie library '{library_name}' not found.")
    except Exception as e:
        print(Fore.RED + f"\n{emojis.CROSS} Could not connect to Plex: {e}")
        pause_fn()
        return

    # --- Smart Collection Logic ---
    if smart_filter:
        was_handled = _process_smart_collection(
            library, collection_name, smart_filter, pause_fn
        )
        if was_handled:
            pause_fn()
            return
        # If not handled, it means user wants to fallback to a static collection

    # --- Static Collection Logic ---
    found_movies, not_found = [], []

    if is_pre_matched:
        found_movies = items
    else:
        try:
            found_movies, not_found = _match_movies_in_plex(library, items)
        except UserAbort:
            print("Canceled.")
            pause_fn()
            return

    print(f"\nFound {len(found_movies)} movies in Plex.")

    if not_found:
        print(
            Fore.YELLOW
            + f"\n{emojis.INFO} Missing {len(not_found)} movies from the list:"
            + Fore.RESET
        )
        # Show the missing movies in a grid
        print_grid(not_found, columns=2, padding=35)

    if not found_movies:
        print(f"{emojis.CROSS} No valid matches found.")
        pause_fn()
        return

    # Handle existing collections (Append/Overwrite/Cancel)
    action = _handle_existing_collection(
        library, collection_name, found_movies, pause_fn
    )
    if action == "stop":
        return
    elif action == "proceed":
        # If proceeding (and not overwriting), ask for final confirmation
        confirm = read_line("Proceed to create collection with these movies? (y/n): ")
        if not confirm or confirm.strip().lower() != "y":
            print(Fore.RED + f"\n{emojis.CROSS} Aborted.")
            pause_fn()
            return

    try:
        library.createCollection(collection_name, items=found_movies)
        print(
            f"\n{emojis.CHECK} Created collection '{collection_name}' with {len(found_movies)} movies."
        )
    except Exception as e:
        print(Fore.RED + f"\n{emojis.CROSS} Failed to create collection: {e}")
    pause_fn()

import difflib
from colorama import Fore
from toolkit import emojis
from toolkit.services.plex_manager import PlexManager
from toolkit.utils import (
    extract_title_and_year,
    normalize_title,
    read_index_or_skip,
    read_line,
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
        is_match = False
        if search_norm == item_norm:
            is_match = True
        elif item_norm.startswith(search_norm) and (
            len(item_norm) == len(search_norm) or item_norm[len(search_norm)] == " "
        ):
            is_match = True
        elif search_norm.startswith(item_norm) and (
            len(search_norm) == len(item_norm) or search_norm[len(item_norm)] == " "
        ):
            is_match = True

        if not is_match and years_match:
            ratio = difflib.SequenceMatcher(None, search_norm, item_norm).ratio()
            if ratio > 0.85:
                is_match = True

        if is_match:
            good_matches.append(item)

    if not good_matches:
        return None

    good_matches.sort(
        key=lambda x: difflib.SequenceMatcher(
            None, search_norm, normalize_title(x.title)
        ).ratio(),
        reverse=True,
    )

    if len(good_matches) > 0:
        best = good_matches[0]
        best_norm = normalize_title(best.title)
        if best_norm == search_norm:
            return best
        if best_norm.startswith(search_norm) and len(good_matches) == 1:
            return best
        if search_norm.startswith(best_norm) and len(good_matches) == 1:
            return best

    if len(good_matches) == 1:
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


def process_and_create_collection(
    collection_name, items, config, pause_fn, is_pre_matched=False
):
    """Connects to Plex, finds movies, and creates the collection."""
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
        pause_fn()
        return

    found_movies, not_found, matched_pairs = [], [], []
    seen_rating_keys = set()

    if is_pre_matched:
        found_movies = items
    else:
        try:
            for raw in items:
                title, _ = extract_title_and_year(raw)
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
                        matched_pairs.append((raw, chosen))
                except Exception as e:
                    print(f"Error searching for '{raw}': {e}")
                    not_found.append(raw)
        except UserAbort:
            print("Canceled.")
            pause_fn()
            return

    print(f"\nFound {len(found_movies)} movies in Plex.")
    if not found_movies:
        print(f"{emojis.CROSS} No valid matches found.")
        pause_fn()
        return

    confirm = read_line("Proceed to create collection with these movies? (y/n): ")
    if not confirm or confirm.strip().lower() != "y":
        print("Aborted.")
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

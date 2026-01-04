from plexapi.server import PlexServer
from plexapi.exceptions import NotFound, Unauthorized
import requests
import concurrent.futures
import re
import emojis

# Pre-compile regex for efficiency
YEAR_PATTERN = re.compile(r"^(.*?) \((\d{4})\)$")


class PlexManager:
    def __init__(self, token, base_url):
        try:
            # Set a timeout to avoid long hangs on bad connections
            self.plex = PlexServer(base_url, token, timeout=5)
            # Accessing an attribute like friendlyName forces a connection test.
            # This will raise an exception if the URL is wrong or the token is invalid.
            self.plex.friendlyName
        except (requests.exceptions.RequestException, Unauthorized) as e:
            # Re-raise as a standard ConnectionError for the main script to handle.
            raise ConnectionError(
                "Failed to connect to Plex. Please check the URL and Token."
            ) from e

    def get_movie_library(self, library_name):
        try:
            return self.plex.library.section(library_name)
        except NotFound:
            print(f"{emojis.CROSS} Error: Could not find library '{library_name}'")
            return None

    def get_all_libraries(self):
        return self.plex.library.sections()

    def get_items_by_studio(self, library, studio_name):
        # Optimization: Get list of studios first, then search specific ones.
        # This avoids fetching metadata for the entire library (library.all()).
        query = studio_name.lower()
        matched_items = []

        # Get all studio names available in the library
        # filterChoices returns objects with 'title' (the studio name)
        studio_choices = library.listFilterChoices("studio")

        # Find studios that match the query (partial match)
        matching_studios = [
            choice.title for choice in studio_choices if query in choice.title.lower()
        ]

        # Search for movies belonging to these specific studios
        for studio in matching_studios:
            # library.search(studio=...) performs a server-side filter
            results = library.search(studio=studio)
            matched_items.extend(results)

        # Deduplicate items by ratingKey (in case of weird overlaps)
        unique_items = {item.ratingKey: item for item in matched_items}
        return list(unique_items.values())

    def find_movies(self, library, titles):
        matched = []

        def search_and_match(title_query):
            # Parse "Title (Year)" format for accurate matching
            year = None
            clean_title = title_query
            match = YEAR_PATTERN.match(title_query)
            if match:
                clean_title = match.group(1)
                year = int(match.group(2))

            try:
                results = library.search(clean_title)
            except Exception as e:
                print(f"{emojis.CROSS} Error searching for '{clean_title}': {e}")
                return None

            if results:
                # If we have a year, filter results with a +/- 1 year tolerance
                if year:
                    for res in results:
                        if res.year and abs(res.year - year) <= 1:
                            return (title_query, res)
                else:
                    # No year provided. Prioritize an exact title match.
                    target = clean_title.lower().strip()
                    for res in results:
                        if res.title.lower().strip() == target:
                            return (title_query, res)

                    # Fallback to first result if no exact match found
                    return (title_query, results[0])
            return None

        # Use a thread pool to search in parallel (preserves order via map)
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            for result in executor.map(search_and_match, titles):
                if result:
                    matched.append(result)

        return matched

    def add_to_collection(self, items, collection_name):
        if not items:
            return

        # Extract just the media objects from the list of tuples
        media_items = [media for _, media in items]

        # Check if collection exists
        collections = self.plex.library.search(
            title=collection_name, libtype="collection"
        )

        if collections:
            collections[0].addItems(media_items)
            print(
                f"{emojis.CHECK} Added {len(media_items)} items to existing collection: '{collection_name}'"
            )
        else:
            # Create new collection with all items at once
            media_items[0].section().createCollection(
                title=collection_name, items=media_items
            )
            print(
                f"{emojis.CHECK} Created collection '{collection_name}' with {len(media_items)} items."
            )

    def _set_tmdb_image(self, item, image_type, include_locked=False):
        """
        Helper to set TMDb artwork.
        image_type: 'poster' (internal 'thumb') or 'background' (internal 'art')
        """
        field_map = {"poster": "thumb", "background": "art"}
        field = field_map.get(image_type)

        if not field:
            return

        try:
            if item.isLocked(field) and not include_locked:
                print(
                    f"  - {emojis.KEY} Locked {image_type} for '{item.title}'. Skipping."
                )
                return

            # Fetch assets dynamically
            assets = item.posters() if image_type == "poster" else item.arts()

            if not assets:
                print(f"  - {emojis.CROSS} No {image_type}s found for '{item.title}'.")
                return

            tmdb_asset = next((a for a in assets if a.provider == "tmdb"), None)

            if tmdb_asset:
                tmdb_asset.select()
                print(
                    f"  - {emojis.CHECK} Selected TMDb {image_type} for '{item.title}'."
                )
            else:
                print(
                    f"  - {emojis.INFO} No TMDb {image_type} found for '{item.title}'."
                )

        except Exception as e:
            print(
                f"  - {emojis.CROSS} Error setting {image_type} for '{item.title}': {e}"
            )

    def set_tmdb_poster(self, item, include_locked=False):
        self._set_tmdb_image(item, "poster", include_locked)
        # If it's a TV Show, also process the seasons
        if item.type == "show":
            for season in item.seasons():
                self._set_tmdb_image(season, "poster", include_locked)

    def set_tmdb_art(self, item, include_locked=False):
        self._set_tmdb_image(item, "background", include_locked)

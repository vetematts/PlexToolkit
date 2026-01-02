from plexapi.server import PlexServer
from plexapi.exceptions import NotFound, Unauthorized
import requests
from toolkit import emojis


class PlexManager:
    def __init__(self, token, base_url):
        try:
            # Set a timeout to avoid long hangs on bad connections
            self.plex = PlexServer(base_url, token, timeout=5)
            # Accessing an attribute like friendlyName forces a connection test.
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
        # Fetch all items and filter locally for better partial matching
        # This catches "A24", "A24 Films", "A24 Productions", etc.
        all_items = library.all()
        query = studio_name.lower()
        return [
            item for item in all_items if item.studio and query in item.studio.lower()
        ]

    def find_movies(self, library, titles):
        matched = []
        for title in titles:
            results = library.search(title)
            if results:
                matched.append((title, results[0]))
        return matched

    def add_to_collection(self, items, collection_name):
        for title, media in items:
            media.addCollection(collection_name)
            media.reload()
            print(f"{emojis.CHECK} Added '{title}' to collection: {collection_name}")

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

from plexapi.server import PlexServer
from plexapi.exceptions import NotFound, Unauthorized
import requests
import emojis


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
            raise ConnectionError("Failed to connect to Plex. Please check the URL and Token.") from e

    def get_movie_library(self, library_name):
        try:
            return self.plex.library.section(library_name)
        except NotFound:
            print(f"{emojis.CROSS} Error: Could not find library '{library_name}'")
            return None

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

    def set_tmdb_poster(self, item, include_locked=False):
        """
        Checks the available posters for an item and selects the TMDb one if available.
        """
        # Providers we want to replace if currently selected
        REPLACE_PROVIDERS = ['gracenote', 'plex', 'local', None]
        PREFERRED_PROVIDER = 'tmdb'

        try:
            # 'thumb' is the internal field name for posters in Plex
            if item.isLocked('thumb') and not include_locked:
                print(f"  - {emojis.KEY} Locked poster for '{item.title}'. Skipping.")
                return

            posters = item.posters()
            if not posters:
                print(f"  - {emojis.CROSS} No posters found for '{item.title}'.")
                return

            # Find the poster provided by TMDb
            tmdb_poster = next((p for p in posters if p.provider == PREFERRED_PROVIDER), None)

            if tmdb_poster:
                tmdb_poster.select()
                print(f"  - {emojis.CHECK} Selected TMDb poster for '{item.title}'.")
            else:
                print(f"  - {emojis.INFO} No TMDb poster found for '{item.title}'.")

        except Exception as e:
            print(f"  - {emojis.CROSS} Error setting poster for '{item.title}': {e}")

    def set_tmdb_art(self, item, include_locked=False):
        """
        Checks the available background art for an item and selects the TMDb one if available.
        """
        PREFERRED_PROVIDER = 'tmdb'

        try:
            # 'art' is the internal field name for background art in Plex
            if item.isLocked('art') and not include_locked:
                print(f"  - {emojis.KEY} Locked background for '{item.title}'. Skipping.")
                return

            arts = item.arts()
            if not arts:
                print(f"  - {emojis.CROSS} No background art found for '{item.title}'.")
                return

            # Find the art provided by TMDb
            tmdb_art = next((a for a in arts if a.provider == PREFERRED_PROVIDER), None)

            if tmdb_art:
                tmdb_art.select()
                print(f"  - {emojis.CHECK} Selected TMDb background for '{item.title}'.")
            else:
                print(f"  - {emojis.INFO} No TMDb background found for '{item.title}'.")

        except Exception as e:
            print(f"  - {emojis.CROSS} Error setting background for '{item.title}': {e}")

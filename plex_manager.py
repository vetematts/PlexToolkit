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
            raise ConnectionError(f"Failed to connect to Plex. Please check the URL and Token.") from e

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

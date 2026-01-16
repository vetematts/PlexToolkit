"""
CollectionManager class to centralize all collection-related operations.
"""

import requests
from urllib.parse import urlencode
from colorama import Fore
from toolkit import emojis
from toolkit import constants
from toolkit.utils import read_line, read_menu_choice, pause


class CollectionManager:
    """Manages collection operations for a Plex library."""

    def __init__(self, library):
        """
        Initialize CollectionManager with a Plex library.

        Args:
            library: Plex library section (e.g., from get_movie_library())
        """
        self.library = library

    def find_collection(self, collection_name):
        """
        Find a collection by name (case-insensitive).

        Args:
            collection_name: Name of the collection to find

        Returns:
            Collection object if found, None otherwise
        """
        existing_collections = self.library.search(
            title=collection_name, libtype=constants.PLEX_LIBTYPE_COLLECTION
        )
        return next(
            (
                c
                for c in existing_collections
                if c.title.lower() == collection_name.lower()
            ),
            None,
        )

    def collection_exists(self, collection_name):
        """
        Check if a collection exists.

        Args:
            collection_name: Name of the collection to check

        Returns:
            True if collection exists, False otherwise
        """
        return self.find_collection(collection_name) is not None

    def is_smart_collection(self, collection):
        """
        Check if a collection is a smart collection.

        Args:
            collection: Collection object

        Returns:
            True if smart collection, False otherwise
        """
        return getattr(collection, constants.COLLECTION_ATTR_SMART, False)

    def get_all_collections(self):
        """
        Get all collections in the library.

        Returns:
            List of collection objects
        """
        return self.library.collections()

    def get_collection_items(self, collection_name):
        """
        Get items in a collection.

        Args:
            collection_name: Name of the collection

        Returns:
            List of items in the collection, or None if collection doesn't exist
        """
        collection = self.find_collection(collection_name)
        if collection:
            return collection.items()
        return None

    def create_static_collection(self, collection_name, items):
        """
        Create a static collection with items.

        Args:
            collection_name: Name for the new collection
            items: List of Plex media items to add

        Returns:
            Created collection object, or None on failure
        """
        try:
            collection = self.library.createCollection(collection_name, items=items)
            print(
                f"\n{emojis.CHECK} Created collection '{collection_name}' with {len(items)} items."
            )
            return collection
        except Exception as e:
            print(Fore.RED + f"\n{emojis.CROSS} Failed to create collection: {e}")
            return None

    def _create_smart_collection_fallback(self, collection_name, smart_filter):
        """
        Fallback method to create smart collection via direct API call.
        Used when plexapi version doesn't support createSmartCollection.

        Args:
            collection_name: Name for the new collection
            smart_filter: Dictionary of filter parameters

        Returns:
            True on success, False on failure
        """
        server = self.library._server
        section_id = self.library.key

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
        return True

    def create_smart_collection(self, collection_name, smart_filter):
        """
        Create a smart collection with filter criteria.

        Args:
            collection_name: Name for the new collection
            smart_filter: Dictionary of filter parameters (e.g., {"studio": "A24"})

        Returns:
            True on success, False on failure
        """
        print(f"\n{emojis.INFO} Creating Smart Collection with filter: {smart_filter}")

        # Check if it exists
        existing = self.find_collection(collection_name)
        if existing:
            print(
                Fore.YELLOW
                + f"\n{emojis.INFO} Collection '{collection_name}' already exists."
                + Fore.RESET
            )
            is_smart = self.is_smart_collection(existing)
            type_label = "Smart" if is_smart else "Static"
            print(
                Fore.LIGHTBLACK_EX
                + f"The existing collection is {type_label}. You cannot append a Smart rule to it."
                + Fore.RESET
            )

            confirm = read_line("Overwrite existing collection? (y/n): ")
            if confirm and confirm.lower() == "y":
                print(Fore.YELLOW + f"Deleting '{collection_name}'..." + Fore.RESET)
                existing.delete()
            else:
                print("Canceled.")
                return False

        try:
            self.library.createSmartCollection(collection_name, **smart_filter)
            print(
                f"\n{emojis.CHECK} Smart Collection '{collection_name}' created successfully!"
            )
            return True
        except AttributeError as e:
            if "createSmartCollection" in str(e):
                print(
                    Fore.YELLOW
                    + f"\n{emojis.INFO} 'plexapi' is outdated. Attempting fallback method..."
                    + Fore.RESET
                )
                try:
                    self._create_smart_collection_fallback(collection_name, smart_filter)
                    return True
                except Exception as fallback_error:
                    print(
                        Fore.RED
                        + f"\n{emojis.CROSS} Fallback failed: {fallback_error}"
                    )
                    print(Fore.RED + "Please run: pip install --upgrade plexapi")
                    return False
            else:
                print(
                    Fore.RED
                    + f"\n{emojis.CROSS} Failed to create Smart Collection: {e}"
                )
                return False
        except Exception as e:
            print(Fore.RED + f"\n{emojis.CROSS} Failed to create Smart Collection: {e}")
            return False

    def append_items(self, collection_name, items):
        """
        Append items to an existing collection.

        Args:
            collection_name: Name of the collection
            items: List of Plex media items to add

        Returns:
            Tuple of (added_count, skipped_count) or None if collection doesn't exist
        """
        collection = self.find_collection(collection_name)
        if not collection:
            return None

        if self.is_smart_collection(collection):
            print(
                Fore.RED
                + f"\n{emojis.CROSS} Cannot append items to a Smart Collection."
                + Fore.RESET
            )
            return None

        try:
            current_items = collection.items()
            current_keys = {str(x.ratingKey) for x in current_items}

            to_add = []
            skipped = 0
            for item in items:
                if str(item.ratingKey) not in current_keys:
                    to_add.append(item)
                else:
                    skipped += 1

            if to_add:
                collection.addItems(to_add)
                print(
                    f"\n{emojis.CHECK} Added {len(to_add)} new items to '{collection_name}'."
                )
            else:
                print(
                    f"\n{emojis.CHECK} No new items to add. All items were already in '{collection_name}'."
                )

            if skipped > 0:
                print(
                    Fore.LIGHTBLACK_EX
                    + f"{skipped} items were already in the collection."
                    + Fore.RESET
                )

            return (len(to_add), skipped)
        except Exception as e:
            print(Fore.RED + f"\n{emojis.CROSS} Failed to append items: {e}")
            return None

    def delete_collection(self, collection_name):
        """
        Delete a collection.

        Args:
            collection_name: Name of the collection to delete

        Returns:
            True on success, False if collection doesn't exist
        """
        collection = self.find_collection(collection_name)
        if not collection:
            return False

        try:
            collection.delete()
            print(f"\n{emojis.CHECK} Deleted collection '{collection_name}'.")
            return True
        except Exception as e:
            print(Fore.RED + f"\n{emojis.CROSS} Failed to delete collection: {e}")
            return False

    def handle_existing_collection(
        self, collection_name, items, pause_fn=pause
    ):
        """
        Handle interaction when a collection already exists.
        Prompts user for Append/Overwrite/Cancel.

        Args:
            collection_name: Name of the collection
            items: List of items to potentially add
            pause_fn: Function to call for pausing (default: pause from utils)

        Returns:
            'append' - Items were appended
            'overwrite' - Collection should be overwritten (caller should delete and recreate)
            'cancel' - User cancelled
            'proceed' - Collection doesn't exist, proceed with creation
        """
        existing_collection = self.find_collection(collection_name)

        if not existing_collection:
            return "proceed"

        is_smart = self.is_smart_collection(existing_collection)
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
                "Do you want to (A)ppend, (O)verwrite, or (C)ancel? ",
                set("aAoOcC"),
            )

        if choice in ("c", "C", "ESC"):
            print("Canceled.")
            pause_fn()
            return "cancel"

        if choice in ("a", "A"):
            result = self.append_items(collection_name, items)
            pause_fn()
            return "append" if result else "cancel"

        if choice in ("o", "O"):
            print(
                Fore.YELLOW
                + f"\n{emojis.INFO} Deleting existing collection '{existing_collection.title}'..."
                + Fore.RESET
            )
            self.delete_collection(collection_name)
            return "overwrite"

        return "cancel"

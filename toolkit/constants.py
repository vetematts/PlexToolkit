# Configuration keys
CONFIG_PLEX_TOKEN = "PLEX_TOKEN"
CONFIG_PLEX_URL = "PLEX_URL"
CONFIG_PLEX_LIBRARY = "PLEX_LIBRARY"
CONFIG_TMDB_API_KEY = "TMDB_API_KEY"
CONFIG_PLEX_LAST_TESTED = "PLEX_LAST_TESTED"
CONFIG_TMDB_LAST_TESTED = "TMDB_LAST_TESTED"

# Default values
DEFAULT_LIBRARY_NAME = "Movies"

# Plex library types
PLEX_LIBTYPE_COLLECTION = "collection"
PLEX_MEDIA_TYPE_MOVIE = 1

# Plex image field mappings
PLEX_IMAGE_POSTER = "poster"
PLEX_IMAGE_BACKGROUND = "background"
PLEX_FIELD_THUMB = "thumb"
PLEX_FIELD_ART = "art"

# Collection attributes
COLLECTION_ATTR_SMART = "smart"

WIKIPEDIA_URLS = {
    "A24": "https://en.wikipedia.org/wiki/List_of_A24_films",
    "Academy Award Best Picture Winners": "https://en.wikipedia.org/wiki/Academy_Award_for_Best_Picture",
    "Cannes Palme d'Or Winners": "https://en.wikipedia.org/wiki/Palme_d%27Or",
    "Pixar": "https://en.wikipedia.org/wiki/List_of_Pixar_films",
    "Studio Ghibli": "https://en.wikipedia.org/wiki/List_of_Studio_Ghibli_works",
    "MCU": "https://en.wikipedia.org/wiki/List_of_Marvel_Cinematic_Universe_films",
    "DCEU": "https://en.wikipedia.org/wiki/List_of_DC_Extended_Universe_films",
    "Disney Animation": "https://en.wikipedia.org/wiki/List_of_Walt_Disney_Animation_Studios_films",
    "DreamWorks Animation": "https://en.wikipedia.org/wiki/List_of_DreamWorks_Animation_productions",
    "Neon": "https://en.wikipedia.org/wiki/List_of_Neon_films",
    "The Criterion Collection": "https://www.criterion.com/shop/browse/list?sort=spine_number",
}

KNOWN_FRANCHISES = {
    "Alien": 8091,
    "Back to the Future": 264,
    "Despicable Me": 86066,
    "Evil Dead": 1960,
    "Fast & Furious": 9485,
    "Harry Potter": 1241,
    "The Hunger Games": 131635,
    "Indiana Jones": 84,
    "James Bond": 645,
    "John Wick": 404609,
    "Jurassic Park": 328,
    "The Lord of the Rings": 119,
    "The Matrix": 2344,
    "Mission: Impossible": 87359,
    "Ocean's": 304,
    "Pirates of the Caribbean": 295,
    "Planet of the Apes": 173710,
    "Scream": 2602,
    "Shrek": 2150,
    "Sonic the Hedgehog": 720879,
    "Star Trek": 115575,
    "Star Wars": 10,
    "The Dark Knight": 263,
    "The Twilight Saga": 33514,
}

STUDIO_MAP = {
    "a24": {"company": 41077},
    "pixar": {"company": 3},
    "studio ghibli": {"company": 10342},
    "mcu": {"keyword": 180547},
    "dceu": {"keyword": 229266},
    "neon": {"company": 93920},
    "dreamworks animation": {"company": 521},
    "searchlight pictures": {"company": 43},
    "disney animation": {"company": 2},
    "the criterion collection": {"company": 10994},
    "netflix": {"company": 20580},
    "HBO": {"company": 3268},
}

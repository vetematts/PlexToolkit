from tmdbv3api import TMDb, Search, Collection

class TMDbSearch:
    def __init__(self, api_key):
        self.tmdb = TMDb()
        self.tmdb.api_key = api_key
        self.tmdb.language = "en"
        self.tmdb.debug = True
        self.search = Search()

    def search_movies(self, keyword, limit=10):
        results = self.search.movies(keyword)
        movie_titles = []

        count = 0
        for movie in results:
            if hasattr(movie, "title"):
                movie_titles.append(movie.title)
                count += 1
            if count >= limit:
                break

        return movie_titles

    def get_movies_from_collection(self, collection_id):
        collection = Collection()
        result = collection.details(collection_id)
        movies = []
        for movie in result.get("parts", []):
            title = movie.get("title")
            date = movie.get("release_date")
            if title:
                if date and len(date) >= 4:
                    movies.append(f"{title} ({date[:4]})")
                else:
                    movies.append(title)
        return movies

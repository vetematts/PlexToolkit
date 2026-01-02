from tmdbv3api import TMDb, Search, Collection
import requests


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

    def discover_movies(self, company_id=None, keyword_id=None):
        """
        Fetches movies by company or keyword, handling pagination automatically.
        """
        url = "https://api.themoviedb.org/3/discover/movie"
        params = {
            "api_key": self.tmdb.api_key,
            "language": "en-US",
            "sort_by": "popularity.desc",
            "page": 1,
        }

        # We will fetch two lists if both IDs are present to simulate an OR search
        queries = []
        if company_id:
            queries.append({"with_companies": company_id})
        if keyword_id:
            queries.append({"with_keywords": keyword_id})

        all_titles = set()

        for query_params in queries:
            # Merge base params with specific query params
            current_params = params.copy()
            current_params.update(query_params)
            current_params["page"] = 1

            while True:
                print(
                    f"Fetching page {current_params['page']}...", end="\r", flush=True
                )
                resp = requests.get(url, params=current_params, timeout=10)
                if resp.status_code == 401:
                    raise ValueError("TMDb authentication failed (invalid API key).")
                if resp.status_code != 200:
                    snippet = ""
                    try:
                        snippet = resp.json().get("status_message", "")
                    except Exception:
                        snippet = resp.text[:200]
                        raise RuntimeError(f"TMDb error {resp.status_code}: {snippet}")
                data = resp.json()
                for m in data.get("results", []):
                    title = m.get("title")
                    date = m.get("release_date")
                    if title:
                        if date and len(date) >= 4:
                            all_titles.add(f"{title} ({date[:4]})")
                        else:
                            all_titles.add(title)
                if data.get("page", 1) >= data.get("total_pages", 1):
                    break
                current_params["page"] += 1

        print(" " * 40, end="\r", flush=True)
        return sorted(list(all_titles))

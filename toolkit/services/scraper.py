import requests
import re
from colorama import Fore
from toolkit import emojis

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


def scrape_wikipedia_film_list(url: str) -> list[str]:
    """
    Scrapes a Wikipedia 'List of X films' page for titles and years.
    Returns a list of strings in the format 'Title (Year)'.
    """
    if not BeautifulSoup:
        print(Fore.RED + "BeautifulSoup is not installed. Cannot scrape web lists.")
        return []

    print(f"\n{emojis.URL} Fetching data from web source...")
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(Fore.RED + f"{emojis.CROSS} Error fetching page: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    titles = []

    # Special handling for Criterion.com official list
    if "criterion.com" in url:
        print("Parsing Criterion.com official list...")
        rows = soup.find_all("tr")
        for row in rows:
            title_cell = row.find("td", class_="g-title")
            year_cell = row.find("td", class_="g-year")
            if title_cell and year_cell:
                t = title_cell.get_text(strip=True)
                y = year_cell.get_text(strip=True)
                if t and y and y.isdigit():
                    titles.append(f"{t} ({y})")
        unique_titles = sorted(list(set(titles)))
        print(
            Fore.GREEN
            + f"{emojis.CHECK} Found {len(unique_titles)} unique movies from Criterion.com."
        )
        return unique_titles

    # Find all tables with class 'wikitable' (standard for film lists)
    tables = soup.find_all("table", {"class": "wikitable"})

    if not tables:
        print(Fore.RED + "No tables found on the Wikipedia page.")
        return []

    print(f"Scanning {len(tables)} tables for film data...")

    for table in tables:
        # Attempt to identify columns by header text
        headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]

        # Identify all potential columns
        title_indices = []
        date_indices = []

        for i, h in enumerate(headers):
            if "title" in h or "film" in h or "winner" in h:
                title_indices.append(i)
            if "release" in h or "date" in h or "year" in h:
                date_indices.append(i)

        # Select best columns
        # Prefer a title column that isn't also a date column (e.g. avoid "Year of Film")
        clean_title_indices = [i for i in title_indices if i not in date_indices]

        title_idx = -1
        date_idx = -1

        if clean_title_indices:
            title_idx = clean_title_indices[0]
        elif title_indices:
            title_idx = title_indices[0]

        if date_indices:
            date_idx = date_indices[0]

        # If headers aren't clear, skip this table (avoids scraping random data)
        if title_idx == -1 or date_idx == -1:
            continue

        rows = table.find_all("tr")
        for row in rows:
            cols = row.find_all(["td", "th"])
            # Ensure row has enough columns
            if not cols or len(cols) <= max(title_idx, date_idx):
                continue

            # Extract Title (often in <i> tags, but get_text handles it)
            title_text = cols[title_idx].get_text(strip=True)

            # Extract Year from date column
            date_text = cols[date_idx].get_text(strip=True)
            # Regex to find the first 4-digit year
            year_match = re.search(r"\d{4}", date_text)

            if title_text and year_match:
                # Clean title (remove footnotes like [1])
                title_clean = re.sub(r"\[.*?\]", "", title_text).strip().strip('"“”')
                titles.append(f"{title_clean} ({year_match.group(0)})")

    unique_titles = sorted(list(set(titles)))
    print(
        Fore.GREEN
        + f"{emojis.CHECK} Found {len(unique_titles)} unique movies from Wikipedia."
    )
    return unique_titles

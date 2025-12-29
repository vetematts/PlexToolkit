# Plex Toolkit

Plex Toolkit is a Python application designed to help manage Plex movie libraries. It automates the creation of collections based on franchises or studios and includes tools to standardize movie artwork using metadata from The Movie Database (TMDb).

## Features

### Collection Management
*   **Manual Creation**: Create collections by typing or pasting a list of movie titles.
*   **Franchises**: Quickly generate collections for popular series (e.g., *Star Wars*, *Harry Potter*, *James Bond*) using TMDb data.
*   **Studios & Keywords**: Build collections based on production studios (e.g., *A24*, *Pixar*) or cinematic universes.
*   **Smart Matching**: Automatically searches your Plex library for matches and handles year disambiguation.

### Artwork Tools
*   **Fix Artwork**: Scans your media to apply the official TMDb poster and background.
    *   **Collection Mode**: Fix artwork for movies within a specific collection.
    *   **Library Mode**: Scan and fix the entire movie library.
*   **Safety Locks**: Respects your manual edits by skipping items where the poster or background fields are locked in Plex.

## Prerequisites

*   **Python 3.6+**
*   **Plex Media Server**: You need the URL and an X-Plex-Token.
*   **TMDb API Key**: (Optional) Required for dynamic franchise searching and the Artwork Fixer tool.

## Installation

1.  **Clone or Download** the repository.
2.  **Install Dependencies**:
    ```bash
    pip install PlexAPI tmdbv3api colorama requests
    ```
3.  **Run the App**:
    ```bash
    python main.py
    ```

## Configuration

On the first run, the tool will create a `config.json` file. You can configure these settings via the **Settings** menu inside the application.

*   **Plex Token**: Found in the XML of any media item in Plex Web.
*   **Plex URL**: The address of your server (e.g., `http://192.168.1.10:32400`).
*   **TMDb API Key**: Get a free API key from themoviedb.org (required for artwork features).
*   **Plex Library**: The name of your movie library (default is "Movies").

## Usage

1.  **Manual Entry**: Type movie names manually.
2.  **Known Franchise**: Select from a list of major film franchises.
3.  **Studio / Keyword**: Find movies by production company.
4.  **Settings**: Manage your API keys and connection settings.
5.  **Tools / Fix Artwork**: Run the artwork fixer on a collection or the whole library.

## Disclaimer

This tool is not affiliated with Plex Inc. or The Movie Database. Use at your own risk.

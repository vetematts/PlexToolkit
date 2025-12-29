# Plex Toolkit 🎬

Plex Toolkit is a Python application designed to help manage Plex movie libraries. It automates the creation of collections based on franchises or studios and includes tools to standardise movie artwork using metadata from The Movie Database (TMDb).

## Features ✨

### 🎬 Collection Management
*   **Manual Creation**: Create collections by typing or pasting a list of movie titles.
*   **Franchises**: Quickly generate collections for popular series (e.g., *Star Wars*, *Harry Potter*, *James Bond*) using TMDb data.
*   **Studios & Keywords**: Build collections based on production studios (e.g., *A24*, *Pixar*) or cinematic universes.
*   **Smart Matching**: Automatically searches your Plex library for matches and handles year disambiguation.

### 🖼️ Artwork Tools
*   **Fix Posters & Backgrounds**: Scans your media to apply the official TMDb poster and background.
    *   **Collection Mode**: Fix posters & backgrounds for movies within a specific collection.
    *   **Library Mode**: Scan and fix the entire movie library.
*   **Safety Locks**: Respects your manual edits by skipping items where the poster or background fields are locked in Plex.

## Prerequisites 📋

*   **Python 3.6+**
*   **Plex Media Server**: You need the URL and an X-Plex-Token.
*   **TMDb API Key**: (Optional) Required for dynamic franchise searching and the Fix Posters & Backgrounds tool.

## Installation 🚀

1.  **Clone or Download** the repository.
2.  **Create a Virtual Environment** (Recommended):
    Using a virtual environment keeps dependencies isolated from your system.
    ```bash
    python -m venv .venv  # Use 'python3' on macOS/Linux

    # Windows:
    .venv\Scripts\activate

    # macOS / Linux:
    source .venv/bin/activate
    ```
3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Run the App**:
    ```bash
    python main.py       # Use 'python3' on macOS/Linux
    ```

## Configuration ⚙️

On the first run, the tool will create a `config.json` file. You can configure these settings via the **Settings** menu inside the application.

*   **Plex Token**: Found in the XML of any media item in Plex Web.
*   **Plex URL**: The address of your server (e.g., `http://192.168.1.10:32400`).
*   **TMDb API Key**: Get a free API key from themoviedb.org (required for artwork features).
*   **Plex Library**: The name of your movie library (default is "Movies").

### 📎 Finding Your Credentials

**Plex Token:**
1.  Sign in at [app.plex.tv](https://app.plex.tv).
2.  Click on any Movie/Show → **⋮** (Three Dots) → **Get Info**.
3.  Click **View XML** at the bottom.
4.  Look at the URL in your browser's address bar. Copy the token string found after `X-Plex-Token=` (it is usually at the very end of the URL).

**Plex URL:**
1.  Open Plex in your browser.
2.  Go to **Settings** (wrench icon) → **Remote Access**.
3.  Copy the IP address shown under "Private" (e.g., `http://192.168.1.10:32400`).
    *   Use the **Private** IP if you are on the same network (home Wi-Fi).
    *   Use the **Public** IP if you are outside your network.

## Usage 🎮

1.  **Manual Entry**: Type movie names manually.
2.  **Known Franchise**: Select from a list of major film franchises.
3.  **Studio / Keyword**: Find movies by production company.
4.  **Settings**: Manage your API keys and connection settings.
5.  **Tools / Fix Posters & Backgrounds**: Run the tool on a collection or the whole library.

## Disclaimer ⚠️

This tool is not affiliated with Plex Inc. or The Movie Database. Use at your own risk.

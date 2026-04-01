# Plex Toolkit 🎬

Plex Toolkit is a Python application designed to help manage Plex movie libraries. It automates the creation of collections based on franchises or studios and includes tools to standardise movie artwork using metadata from The Movie Database (TMDb).

<img width="1282" height="1608" alt="CleanShot 2026-01-02 at 00 33 15@2x" src="https://github.com/user-attachments/assets/d26d728e-c077-4037-82ef-ddfcb7b4eb43" />

## Features ✨

### 🎬 Collection Management
*   **Manual Creation**: Create collections by typing or pasting a list of movie titles.
*   **Franchises**: Quickly generate collections for popular series (e.g., *Star Wars*, *Harry Potter*, *James Bond*) using TMDb data (or built-in fallback lists if no API key is provided).
*   **Studios & Collections**:
    *   **Local Search**: Scans your library to find top studios (e.g. "A24 (45 movies)").
    *   **Web Import**: Scrapes Wikipedia/Criterion for accurate lists (e.g. *Academy Award Winners*, *Criterion Collection*).
    *   **TMDb Discovery**: Finds movies by production company.
*   **Smart Matching**: Automatically searches your Plex library for matches and handles year disambiguation.

### 🖼️ Artwork Tools
*   **Fix Posters & Backgrounds**: Scans your media to apply the official TMDb poster and background.
    *   **Collection Mode**: Fix posters & backgrounds for items within a specific collection.
    *   **Library Mode**: Scan and fix the entire library (Movies or TV Shows).
    *   **TV Support**: Automatically fixes posters for Seasons when processing TV Shows.
*   **Safety Locks**: Respects your manual edits by skipping items where the poster or background fields are locked in Plex.

## Prerequisites 📋

*   **Python 3.9+**
*   **uv**: Install from [astral.sh/uv](https://astral.sh/uv/)
*   **Plex Media Server**: You need the URL and an X-Plex-Token.
*   **TMDb API Key**: (Optional) Required for dynamic franchise searching and the Fix Posters & Backgrounds tool.

## Installation 🚀

1.  **Clone or Download** the repository.
2.  **Create the Environment and Install Dependencies**:
    `uv` creates and manages the virtual environment for you.
    ```bash
    uv sync --extra dev
    ```
3.  **Run the App**:
    ```bash
    uv run python main.py
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

1.  **Franchise / Series**: Select from a list of major film franchises.
2.  **Studio / Collections**: Find movies by studio, import from Wikipedia, or discover via TMDb.
3.  **Manual Entry**: Type movie names manually.
4.  **Tools / Fix Posters & Backgrounds**: Run the tool on a collection or the whole library.
5.  **Settings**: Manage your API keys and connection settings.

## Troubleshooting & Tips 💡

*   **Emojis not showing?**
    This tool uses emojis for a better UI. If you see squares or unusual characters, try using a modern terminal like **Windows Terminal**, **VS Code Integrated Terminal**, or **iTerm2**.
*   **Plex Connection Failed?**
    *   Ensure your **Plex URL** includes the protocol and port (e.g., `http://192.168.1.5:32400`).
    *   Check that your **Plex Token** is correct and hasn't expired.
*   **No TMDb Key?**
    The tool works without a TMDb API key, but functionality is limited:
    *   **Franchise/Studio Mode**: Uses a built-in "fallback" list of popular collections instead of searching the live database.
    *   **Poster Tool**: Will not work (requires TMDb to fetch images).

## Development 🛠️

If you wish to modify the code, the following tools are included to ensure quality:

*   **Sync Dependencies**: Run `uv sync --extra dev`.
*   **Formatting**: Run `uv run black .` to auto-format code.
*   **Linting**: Run `uv run ruff check .` to catch style issues and bugs.
*   **Testing**: Run `uv run pytest` to execute unit tests.

## Disclaimer ⚠️

This tool is not affiliated with Plex Inc. or The Movie Database. Use at your own risk.

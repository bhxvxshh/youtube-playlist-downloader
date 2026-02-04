# YouTube Playlist Downloader

A professional Python script to download entire YouTube playlists in the highest quality available (up to 4K/8K).

## Features

- ✅ Download entire playlists in highest quality
- ✅ Estimated total download size before downloading
- ✅ Progress bar with speed and ETA
- ✅ Resume interrupted downloads
- ✅ Skip already downloaded videos
- ✅ Age-restricted video bypass (Android client)
- ✅ Cookie authentication support
- ✅ Interactive and CLI modes
- ✅ Cross-platform (Windows, macOS, Linux)

## Requirements

- Python 3.7+
- ffmpeg (for merging video and audio)

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/bhxvxshh/youtube-playlist-downloader.git
cd youtube-playlist-downloader
```

### 2. Create virtual environment (recommended)

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install ffmpeg

**Windows:**
- Download from [ffmpeg.org](https://ffmpeg.org/download.html)
- Extract and add the `bin` folder to your system PATH

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update && sudo apt install ffmpeg
```

## Usage

### Interactive Mode

Simply run without arguments:

```bash
python playlist_downloader.py
```

You'll be prompted to:
1. Enter the playlist URL
2. Choose authentication method
3. Confirm the download after seeing the summary

### Command Line Mode

```bash
# Basic usage (auto Android bypass for age-restricted content)
python playlist_downloader.py "PLAYLIST_URL"

# Specify output directory
python playlist_downloader.py "PLAYLIST_URL" -o ./downloads

# Show playlist info without downloading
python playlist_downloader.py "PLAYLIST_URL" --info-only

# Skip confirmation prompt
python playlist_downloader.py "PLAYLIST_URL" -y

# Use cookies file for authentication
python playlist_downloader.py "PLAYLIST_URL" --cookies cookies.txt

# Use browser cookies (browser must be closed)
python playlist_downloader.py "PLAYLIST_URL" --browser chrome
```

### CLI Options

| Option | Description |
|--------|-------------|
| `url` | YouTube playlist URL |
| `-o, --output` | Output directory |
| `--cookies` | Path to cookies.txt file |
| `--browser` | Browser for cookie extraction (chrome/firefox/edge) |
| `--android` | Use Android client bypass (default) |
| `--no-android` | Disable Android client bypass |
| `--info-only` | Only show info, don't download |
| `-y, --yes` | Skip confirmation prompt |

## Authentication Methods

### 1. Android Client Bypass (Recommended)
No login required. Works for most age-restricted videos.

### 2. Cookies File
Export cookies using a browser extension:
- Chrome: [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
- Firefox: [cookies.txt](https://addons.mozilla.org/addon/cookies-txt/)

Steps:
1. Go to YouTube.com and sign in
2. Click the extension icon
3. Export/save as `cookies.txt`

### 3. Browser Cookies
Requires browser to be completely closed.

## Output Structure

```
output_directory/
├── Playlist Name/
│   ├── 001 - Video Title.mp4
│   ├── 002 - Video Title.mp4
│   └── ...
└── downloaded_videos.txt  # Tracks downloaded videos
```

## Troubleshooting

### "ffmpeg not found"
Make sure ffmpeg is installed and in your system PATH.

### "Sign in to confirm your age"
Try using:
1. Android client bypass (option 1)
2. Cookies file authentication

### "Could not copy cookie database"
Close your browser completely before using browser cookie extraction.

### Slow download speed
Try using multiple connections:
```python
'concurrent_fragment_downloads': 10  # Increase from default 5
```

## Legal Disclaimer

This tool is for educational purposes. Downloading videos may violate YouTube's Terms of Service. Only download content you have the right to download.

## License

MIT License - see [LICENSE](LICENSE) file.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

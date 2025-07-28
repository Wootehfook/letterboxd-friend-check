# Letterboxd Friend Check

A Python desktop application that compares your Letterboxd watchlist with friends' watchlists to find common movies.

## 🚀 Quick Start (No Installation Required!)

### 📥 **Download Ready-to-Use Version**
**Just want to use the app? No Python needed!**

#### Windows Users:
1. **Download** `LetterboxdFriendCheck.exe` (28.4 MB)
2. **Double-click** to run (Windows will show security warning - click "More info" → "Run anyway")
3. **Enter your Letterboxd username** and start finding movies! 🎬

#### Linux Users:
1. **Download** `LetterboxdFriendCheck-Linux` (25.0 MB)
2. **Make executable**: `chmod +x LetterboxdFriendCheck-Linux`
3. **Run**: `./LetterboxdFriendCheck-Linux`
4. **Enter your Letterboxd username** and start finding movies! 🎬

[**→ Windows Download**](LetterboxdFriendCheck.exe) | [**→ Linux Download**](LetterboxdFriendCheck-Linux) | [**→ Installation Guide**](INSTALL.md)

---

## ✨ Features

- 🎬 **Compare Watchlists**: Find movies you and your friends both want to watch
- 👥 **Friends Management**: Easily select which friends to sync with
- 🎨 **Modern UI**: Professional interface with light/dark themes
- 🎭 **TMDB Integration**: Optional movie details, posters, and ratings
- 💾 **Data Persistence**: Saves your data between sessions
- ♿ **Accessibility**: WCAG AA compliant themes
- 🌐 **Cross-Platform**: Works on Windows, macOS, and Linux

## 👨‍💻 Developer Setup (Python Required)

### Prerequisites
- Python 3.8+ installed
- Internet connection
- Public Letterboxd profile

### Installation Steps

1. **Clone this repository**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/letterboxd-friend-check.git
   cd letterboxd-friend-check
   ```
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the application**:
   ```bash
   python run_letterboxd.py
   ```

## First Run Setup

1. Enter your Letterboxd username
2. (Optional) Add your TMDB API key for enhanced movie details
3. Click "Fetch Friends" to load your friends list
4. Select friends you want to compare with
5. Click "Sync Watchlists" to find common movies

## TMDB API Key (Optional)

For movie posters, ratings, and additional details:

1. Sign up at [TMDB](https://www.themoviedb.org/)
2. Get your free API key from [Account Settings → API](https://www.themoviedb.org/settings/api)
3. Enter it in the Setup tab

## Requirements

- Python 3.8 or higher
- Internet connection
- Public Letterboxd profile

## Privacy & Data

- Only accesses **public** Letterboxd data
- No login required
- All data stored **locally** on your computer
- Respects Letterboxd's rate limits

## License

GNU General Public License v3.0 - see [LICENSE](LICENSE)

## Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

---

**Note**: This application was developed with AI assistance and is not affiliated with Letterboxd.

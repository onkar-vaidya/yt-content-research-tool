# YouTube Keyword & Video Scraper

> Automated YouTube keyword research and video data collection tool for content creators, marketers, and SEO analysts.

## 🎯 What It Does

This tool helps you discover trending YouTube keywords and analyze video performance by:

1. **Keyword Expansion** - Takes your seed keywords and expands them into hundreds/thousands of related keywords using YouTube's autocomplete API
2. **Video Research** - Automatically scrapes video metadata (title, channel, views, duration) for all discovered keywords
3. **Smart Organization** - Outputs data in well-organized folders with descriptive names based on keyword analysis

## ✨ Key Features

- 🚀 **Multi-threaded** - Fast parallel processing for both keywords and videos
- 📊 **Organized Output** - Smart folder structure with descriptive names (e.g., `home_ideas_renovation_20260109/`)
- 🔄 **Resume Support** - Detects and resumes interrupted runs automatically
- 📈 **Keyword Tree** - Tracks parent-child relationships showing how keywords expanded
- 🎨 **Clean Data** - CSV and TXT formats ready for analysis
- ⚙️ **Configurable** - Easy-to-adjust settings for depth, threads, and limits

## 🎬 Perfect For

- **Content Creators** - Find trending topics and video ideas
- **SEO Analysts** - Keyword research and competitive analysis
- **Marketers** - Understand what your audience searches for
- **Researchers** - Analyze YouTube content trends

## 📦 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/onkar-vaidya/yt-content-research-tool.git
cd yt-content-research-tool

# 2. Install dependencies
pip install requests pandas openpyxl yt-dlp

# 3. Add your keywords to InputKeywords.txt
echo "your topic here" > InputKeywords.txt

# 4. Run the script
python3 main.py
# Or use the quick start script
./quick_start.sh
```

## 📁 Output Structure

```
Keywords/
└── topic_name_20260109_123456/
    ├── keywords.csv          # All keywords with metadata
    ├── keywords.txt          # Plain text list
    └── keywords_tree.csv     # Parent-child relationships

Videos/
└── topic_name_20260109_123456.csv  # Video data for all keywords
```

## 🛠️ Configuration

All settings are in one place at the top of `main.py`:

```python
MAX_KEYWORDS = 5000              # Total keywords to collect
MAX_DEPTH = 4                    # Keyword expansion depth
MAX_RESULTS_PER_KEYWORD = 20     # Videos per keyword
KEYWORD_THREADS = 15             # Parallel threads for keywords
VIDEO_THREADS = 50               # Parallel threads for videos
```

## 📊 Example Output

**Input:** Home decor, DIY, interior design

**Keywords Generated:** 5000+ related keywords  
**Videos Scraped:** 100,000+ video records  
**Folder Name:** `home_ideas_renovation_20260109_075201/`

Sample keyword data:
```csv
Keyword,Depth,Origin_Seed
interior design,0,interior design
home design ideas,1,interior design
diy home decor,1,home decor
living room makeover,2,interior design
...
```

Sample video data:
```csv
Keyword,Rank,Video Title,Channel,Views,Video Link,Duration
diy home decor,1,"Amazing DIY Ideas",HomeChannel,2840780,https://youtube.com/...,10:15
...
```

## 🔧 Technologies

- **Python 3.x** - Main programming language
- **YouTube Autocomplete API** - No API key required!
- **yt-dlp** - Video metadata extraction
- **pandas** - Data processing and CSV handling
- **Multi-threading** - Fast parallel processing
- **Smart keyword analysis** - Automatic descriptive naming

## 📖 Documentation

- [NEW_FILE_NAMING.md](NEW_FILE_NAMING.md) - Explanation of the smart naming system
- [TEST_RUN_RESULTS.md](TEST_RUN_RESULTS.md) - Example test run results

## 💡 Usage Tips

### For Quick Tests
Edit `main.py` to use smaller limits:
```python
MAX_KEYWORDS = 100
MAX_DEPTH = 2
```

### To Avoid Rate Limiting
Reduce thread counts if you encounter 429 errors:
```python
KEYWORD_THREADS = 5
VIDEO_THREADS = 20
```

### Using Custom Keywords
Simply add your topics to `InputKeywords.txt`, one per line:
```
cooking recipes
fitness workouts
gaming tips
```

## 🚨 Common Issues

**Issue:** `yt-dlp not installed`  
**Solution:** `pip install yt-dlp`

**Issue:** YouTube blocking requests (429 errors)  
**Solution:** Reduce thread counts in configuration

**Issue:** Empty keywords file  
**Solution:** Add keywords to `InputKeywords.txt` before running

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests

## 📄 License

MIT License - Free to use and modify

## ⚠️ Disclaimer

This tool is for research and educational purposes. Please respect:
- YouTube's Terms of Service
- Rate limits and fair use policies
- Copyright and intellectual property rights

Use responsibly and ethically.

## 🌟 Star This Repo

If you find this tool useful, please consider giving it a star ⭐

---

**Created by:** [Onkar Vaidya](https://github.com/onkar-vaidya)  
**Repository:** [yt-content-research-tool](https://github.com/onkar-vaidya/yt-content-research-tool)

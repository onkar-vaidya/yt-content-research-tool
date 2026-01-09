#!/usr/bin/env python3
"""
Unified YouTube Keywords & Videos Scraper
Combines:
1. Keywords Finder (using YouTube autocomplete API)
2. Videos Finder (using yt-dlp to search videos by keywords)

Features:
- Configurable parameters at the top
- Separate output folders for keywords and videos
- Timestamped outputs for each run
- Automatic folder creation
"""

import requests
import time
import threading
import queue
import json
import csv
import random
import os
import sys
import re
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import pandas as pd

try:
    import yt_dlp
except ImportError:
    print("Warning: yt-dlp is not installed. Videos scraping will not work.")
    print("Install it with: pip install yt-dlp")
    yt_dlp = None

# ============================================
# CONFIGURATION SECTION - MODIFY THESE VALUES
# ============================================

# --- KEYWORDS FINDER CONFIGURATION ---
MAX_KEYWORDS = 5000
MAX_DEPTH = 4
KEYWORD_THREADS = 15
KEYWORD_DELAY = 0.15

# --- VIDEOS FINDER CONFIGURATION ---
# This file will be auto-generated from keywords if not provided
VIDEO_KEYWORDS_FILE = None  # Set to None to use keywords from scraper
MAX_RESULTS_PER_KEYWORD = 20
VIDEO_THREADS = 50
VIDEO_STRICTNESS = "strict"  # "strict" or "relaxed"

# --- OUTPUT FOLDERS ---
KEYWORDS_OUTPUT_FOLDER = "Keywords"
VIDEOS_OUTPUT_FOLDER = "Videos"


# --- INPUT DATA CONFIGURATION ---
INPUT_KEYWORDS_FILE = "InputKeywords.txt"

# Load keywords from file
try:
    with open(INPUT_KEYWORDS_FILE, "r", encoding="utf-8") as f:
        SEED_KEYWORDS = [line.strip() for line in f if line.strip()]
    
    if SEED_KEYWORDS:
        print(f"Loaded {len(SEED_KEYWORDS)} keywords from {INPUT_KEYWORDS_FILE}")
    else:
        print(f"Warning: {INPUT_KEYWORDS_FILE} is empty!")
        SEED_KEYWORDS = []

except FileNotFoundError:
    print(f"Warning: {INPUT_KEYWORDS_FILE} not found!")
    SEED_KEYWORDS = []

# --- PROXY CONFIGURATION (Optional) ---
PROXIES = []  # Example: ["http://IP:PORT"]
PROXY_URL = None  # For video scraping

# --- FILTER KEYWORDS ---
FILTER_KEYWORDS = [
    "free", "porn", "sex", "xxx", "hentai",
    "download", "mp3", "torrent"
]

# --- API ENDPOINTS ---
ENDPOINTS = [
    "https://clients1.google.com/complete/search?client=youtube&gs_ri=youtube&ds=yt&gl=IN&hl=en-IN&q={}",
    "https://clients1.google.com/complete/search?client=youtube&gs_ri=youtube&ds=yt&gl=IN&hl=hi&q={}",
]

# ============================================
# END OF CONFIGURATION
# ============================================

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
]

# Global storage for keywords scraper
keyword_tree = defaultdict(list)
collected = set()
task_queue = queue.Queue()
depth_map = {}
keyword_source = {}
lock = threading.Lock()

# Global locks for thread safety
csv_lock = threading.Lock()
print_lock = threading.Lock()


# ============================================
# KEYWORDS FINDER FUNCTIONS
# ============================================

def get_suggestions(query):
    """Fetch keyword suggestions from YouTube autocomplete API"""
    results = set()
    proxy = None
    if PROXIES:
        proxy = {"http": PROXIES[0], "https": PROXIES[0]}

    for endpoint in ENDPOINTS:
        for attempt in range(3):
            try:
                headers = {"User-Agent": random.choice(USER_AGENTS)}
                url = endpoint.format(query)
                # print(f"DEBUG: Requesting {url}...")  # Verbose debug
                resp = requests.get(url, headers=headers, proxies=proxy, timeout=5)
                
                if resp.status_code == 200:
                    content = resp.text
                    if content.startswith("window.google.ac.h("):
                        content = content[content.find("(")+1 : content.rfind(")")]
                    
                    data = json.loads(content)
                    
                    if len(data) > 1 and data[1]:
                        for item in data[1]:
                            if isinstance(item, list) and len(item) > 0:
                                results.add(item[0])
                            elif isinstance(item, str):
                                results.add(item)
                    break
                    
                elif resp.status_code == 403:
                    wait_time = (attempt + 1) * 2
                    time.sleep(wait_time)
                else:
                    break
            except Exception as e:
                time.sleep(1)
    
    return list(results)


def is_allowed(keyword):
    """Check if keyword passes filter"""
    k = keyword.lower()
    return not any(f in k for f in FILTER_KEYWORDS)


def keyword_worker():
    """Worker thread for keywords scraping"""
    while True:
        try:
            kw = task_queue.get(timeout=3)
        except:
            return

        depth = depth_map.get(kw, 0)

        if len(collected) >= MAX_KEYWORDS:
            return

        if depth > MAX_DEPTH:
            continue

        suggestions = get_suggestions(kw)

        with lock:
            if kw not in collected:
                collected.add(kw)
                print(f"[Keywords {len(collected)}/{MAX_KEYWORDS}] {kw}")

        for s in suggestions:
            if not is_allowed(s):
                continue

            with lock:
                keyword_tree[kw].append(s)

                if s not in collected:
                    depth_map[s] = depth + 1
                    if s not in keyword_source:
                        keyword_source[s] = keyword_source.get(kw, kw)
                    task_queue.put(s)


def scrape_keywords():
    """Main function to scrape keywords"""
    print("="*60)
    print("STEP 1: KEYWORD SCRAPING")
    print("="*60)
    
    # Initialize seed keywords
    for kw in SEED_KEYWORDS:
        depth_map[kw] = 0
        keyword_source[kw] = kw
        task_queue.put(kw)

    try:
        with ThreadPoolExecutor(max_workers=KEYWORD_THREADS) as executor:
            futures = [executor.submit(keyword_worker) for _ in range(KEYWORD_THREADS)]
            for f in futures:
                f.result()
        print("\nKeyword scraping complete.")
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by User! Saving collected data...")
    finally:
        print(f"Total unique keywords: {len(collected)}")
        return save_keywords()


def analyze_keywords_for_name(keywords_list, max_words=3):
    """Analyze keywords to generate a descriptive name"""
    from collections import Counter
    
    # Common words to ignore
    stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                 'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'how',
                 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'your', 'you', 'my'}
    
    # Count word frequency across all keywords
    word_counts = Counter()
    keywords_as_list = list(keywords_list) if not isinstance(keywords_list, list) else keywords_list
    for kw in keywords_as_list[:50]:  # Analyze first 50 keywords
        words = kw.lower().split()
        for word in words:
            # Clean word
            word = re.sub(r'[^a-z0-9]', '', word)
            if len(word) > 2 and word not in stopwords:
                word_counts[word] += 1
    
    # Get top words
    top_words = [word for word, count in word_counts.most_common(max_words)]
    
    if not top_words:
        # Fallback to sanitized first keyword
        first_kw = list(keywords_list)[0] if keywords_list else "keywords"
        top_words = [re.sub(r'[^a-z0-9]', '', first_kw.lower().replace(' ', '_'))[:20]]
    
    return '_'.join(top_words)


def save_keywords():
    """Save keywords to files with timestamp"""
    if not collected:
        print("No keywords collected to save.")
        return None
    
    # Create output folder
    os.makedirs(KEYWORDS_OUTPUT_FOLDER, exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Analyze keywords to create descriptive name
    descriptive_name = analyze_keywords_for_name(collected)
    
    # Create run folder
    run_folder_name = f"{descriptive_name}_{timestamp}"
    run_folder = os.path.join(KEYWORDS_OUTPUT_FOLDER, run_folder_name)
    os.makedirs(run_folder, exist_ok=True)
    
    # Generate filenames inside the run folder
    csv_file = os.path.join(run_folder, "keywords.csv")
    tree_file = os.path.join(run_folder, "keywords_tree.csv")
    txt_file = os.path.join(run_folder, "keywords.txt")
    
    # Save main keywords
    df = pd.DataFrame({
        "Keyword": list(collected),
        "Depth": [depth_map.get(k, None) for k in collected],
        "Origin_Seed": [keyword_source.get(k, None) for k in collected]
    })
    df.to_csv(csv_file, index=False)
    
    # Save as txt for easy video scraping
    with open(txt_file, 'w', encoding='utf-8') as f:
        for kw in sorted(collected):
            f.write(f"{kw}\n")
    
    # Save tree
    tree_rows = []
    for parent, children in keyword_tree.items():
        for child in children:
            tree_rows.append([parent, child])
    
    tree_df = pd.DataFrame(tree_rows, columns=["Parent", "Child"])
    tree_df.to_csv(tree_file, index=False)
    
    print(f"\n✅ Keywords files generated in folder: {run_folder_name}/")
    print(f"   - keywords.csv")
    print(f"   - keywords.txt")
    print(f"   - keywords_tree.csv")
    
    return txt_file, descriptive_name


# ============================================
# VIDEOS FINDER FUNCTIONS
# ============================================

def normalize_text(text):
    """Normalize text for comparison"""
    if not text:
        return ""
    return text.lower().strip()


def is_video_relevant(keyword, video_title):
    """Check if video is relevant to keyword"""
    k_norm = normalize_text(keyword)
    t_norm = normalize_text(video_title)
    
    if k_norm in t_norm:
        return True
        
    k_words = set(k_norm.split())
    t_words = set(t_norm.split())
    if not k_words:
        return False

    common_words = k_words.intersection(t_words)
    
    if VIDEO_STRICTNESS == "strict":
        required_matches = len(k_words) - 1 if len(k_words) > 1 else 1
        return len(common_words) >= required_matches
    else:
        return (len(common_words) / len(k_words)) >= 0.5


def scrape_single_keyword(keyword, output_file):
    """Scrape videos for a single keyword"""
    if yt_dlp is None:
        print("Error: yt-dlp not available")
        return
    
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'noplaylist': True,
        'ignoreerrors': False,
        'no_warnings': True,
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }

    if PROXY_URL:
        ydl_opts['proxy'] = PROXY_URL

    query = f"ytsearch{MAX_RESULTS_PER_KEYWORD}:{keyword}"
    results_to_save = []
    rank_counter = 1
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(query, download=False)
                if 'entries' in info:
                    for entry in info['entries']:
                        if not entry:
                            continue
                        title = entry.get('title')
                        if not title:
                            continue
                        
                        # Always include video (set to True)
                        if True:
                            # Duration Logic
                            duration_str = entry.get('duration_string')
                            if not duration_str:
                                duration_sec = entry.get('duration')
                                if duration_sec:
                                    m, s = divmod(duration_sec, 60)
                                    h, m = divmod(m, 60)
                                    if h > 0:
                                        duration_str = f"{int(h)}:{int(m):02d}:{int(s):02d}"
                                    else:
                                        duration_str = f"{int(m)}:{int(s):02d}"
                                else:
                                    duration_str = 'N/A'

                            results_to_save.append([
                                keyword,
                                rank_counter,
                                title,
                                entry.get('uploader') or entry.get('channel') or 'N/A',
                                entry.get('view_count', 0),
                                entry.get('url') or entry.get('webpage_url'),
                                duration_str
                            ])
                            rank_counter += 1
            break
        except Exception as e:
            if "429" in str(e):
                with print_lock:
                    print(f"!!! CRITICAL: YouTube blocking requests (Error 429). Pausing...")
                time.sleep(60)
                return
            
            if "403" in str(e) or "Forbidden" in str(e):
                if attempt < max_retries - 1:
                    wait_time = random.uniform(5, 10) + (attempt * 5)
                    with print_lock:
                        print(f"[!] '{keyword}': 403 Forbidden. Retrying in {wait_time:.1f}s")
                    time.sleep(wait_time)
                    continue
                else:
                    with print_lock:
                        print(f"[-] '{keyword}': Failed after {max_retries} attempts")
                    return
            return

    # Write to file safely
    if results_to_save:
        with csv_lock:
            with open(output_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(results_to_save)
    
    with print_lock:
        if results_to_save:
            print(f"[Videos +] '{keyword}': Found {len(results_to_save)} videos")
        else:
            print(f"[Videos -] '{keyword}': No matches")

    time.sleep(random.uniform(1.0, 3.0))


def scrape_videos(keywords_file, descriptive_name=None):
    """Main function to scrape videos"""
    if yt_dlp is None:
        print("⚠️ Skipping video scraping (yt-dlp not installed)")
        return
    
    print("\n" + "="*60)
    print("STEP 2: VIDEO SCRAPING")
    print("="*60)
    
    if not os.path.exists(keywords_file):
        print(f"Error: {keywords_file} not found.")
        return

    # Load keywords
    with open(keywords_file, 'r', encoding='utf-8') as f:
        keywords = [line.strip() for line in f if line.strip()]

    # Create output folder
    os.makedirs(VIDEOS_OUTPUT_FOLDER, exist_ok=True)
    
    # Generate timestamp and output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Use descriptive name if provided, otherwise analyze keywords
    if not descriptive_name:
        descriptive_name = analyze_keywords_for_name(keywords)
    
    output_file = os.path.join(VIDEOS_OUTPUT_FOLDER, f"{descriptive_name}_{timestamp}.csv")
    
    # Resume logic
    processed_keywords = set()
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            try:
                next(reader)
                for row in reader:
                    if row:
                        processed_keywords.add(row[0])
            except:
                pass
    else:
        # Create file with header
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Keyword', 'Rank', 'Video Title', 'Channel', 'Views', 'Video Link', 'Duration'])

    keywords_to_do = [k for k in keywords if k not in processed_keywords]
    
    print(f"Total Keywords: {len(keywords)}")
    print(f"Already Done:   {len(processed_keywords)}")
    print(f"Remaining:      {len(keywords_to_do)}")
    print(f"Active Threads: {VIDEO_THREADS}")
    print(f"Output File:    {descriptive_name}_{timestamp}.csv")
    print("Starting in 3 seconds...")
    time.sleep(3)

    # Parallel execution
    with ThreadPoolExecutor(max_workers=VIDEO_THREADS) as executor:
        executor.map(lambda k: scrape_single_keyword(k, output_file), keywords_to_do)

    print(f"\n✅ Videos saved to: {output_file}")


# ============================================
# MAIN EXECUTION
# ============================================

def main():
    """Main execution function"""
    print("\n" + "="*60)
    print("UNIFIED YOUTUBE SCRAPER")
    print("="*60)
    print(f"Seed Keywords: {len(SEED_KEYWORDS)}")
    print(f"Max Keywords to Collect: {MAX_KEYWORDS}")
    print(f"Max Results per Video Keyword: {MAX_RESULTS_PER_KEYWORD}")
    print("="*60 + "\n")
    
    # Step 1: Scrape keywords
    result = scrape_keywords()
    
    if result is None:
        print("No keywords collected. Exiting.")
        return
    
    keywords_txt_file, descriptive_name = result
    
    # Step 2: Scrape videos
    video_input = VIDEO_KEYWORDS_FILE if VIDEO_KEYWORDS_FILE else keywords_txt_file
    scrape_videos(video_input, descriptive_name)
    
    print("\n" + "="*60)
    print("✨ ALL DONE!")
    print("="*60)
    print(f"Keywords saved in: {KEYWORDS_OUTPUT_FOLDER}/")
    print(f"Videos saved in:   {VIDEOS_OUTPUT_FOLDER}/")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()

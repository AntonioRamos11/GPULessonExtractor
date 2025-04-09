from pytube import YouTube
from datetime import datetime, timedelta
import re
import json
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random
import os
from concurrent.futures import ThreadPoolExecutor

# Add caching to avoid re-fetching videos
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

# User agents to rotate through to avoid detection
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0'
]

# Create a shared browser instance to avoid repeatedly starting/stopping browsers
def get_shared_browser():
    if not hasattr(get_shared_browser, "browser"):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
        get_shared_browser.browser = webdriver.Chrome(options=chrome_options)
    return get_shared_browser.browser

def get_video_details_with_selenium(video_id, use_shared_browser=True):
    """Get video details using Selenium to avoid HTTP 400 errors"""
    # Check cache first
    cache_file = os.path.join(CACHE_DIR, f"{video_id}_details.json")
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except:
            # If cache read fails, continue with normal flow
            pass
    
    if use_shared_browser:
        driver = get_shared_browser()
    else:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
        driver = webdriver.Chrome(options=chrome_options)
    
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        driver.get(url)
        
        # Wait for title to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1.title"))
        )
        
        # Extract video details
        title_elem = driver.find_element(By.CSS_SELECTOR, "h1.title")
        title = title_elem.text.strip()
        
        # Try to get description
        try:
            description_elem = driver.find_element(By.CSS_SELECTOR, "div#description-inline-expander")
            description = description_elem.text.strip()
        except:
            description = ""
        
        # Try to get publish date
        try:
            date_elem = driver.find_element(By.CSS_SELECTOR, "div#info-strings yt-formatted-string")
            date_text = date_elem.text.strip()
            publish_date = date_text
        except:
            publish_date = None
        
        # Get thumbnail URL
        thumbnail = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        
        if not use_shared_browser:
            driver.quit()
        
        result = {
            'id': video_id,
            'title': title,
            'description': description,
            'publish_date': publish_date,
            'url': url,
            'thumbnail': thumbnail
        }
        
        # Cache the result
        with open(cache_file, 'w') as f:
            json.dump(result, f)
            
        return result
    except Exception as e:
        print(f"Selenium error getting video details for {video_id}: {str(e)}")
        if not use_shared_browser:
            driver.quit()
        return None

def get_video_details(video_id):
    """Get video details with better error handling and fallbacks"""
    cache_file = os.path.join(CACHE_DIR, f"{video_id}_details.json")
    
    # Check cache first with better error handling
    try:
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
                # Validate cached data
                if all(key in cached_data for key in ['id', 'title', 'url']):
                    return cached_data
    except (json.JSONDecodeError, IOError) as e:
        print(f"Cache read error for {video_id}, regenerating: {str(e)}")
    
    # Try yt-dlp first (if installed)
    try:
        import yt_dlp
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'force_generic_extractor': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f'https://www.youtube.com/watch?v={video_id}', download=False)
            
            result = {
                'id': video_id,
                'title': info.get('title', ''),
                'description': info.get('description', ''),
                'publish_date': info.get('upload_date', ''),
                'url': f"https://www.youtube.com/watch?v={video_id}",
                'thumbnail': info.get('thumbnail', f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg'),
                'duration': info.get('duration', None),
                'view_count': info.get('view_count', None)
            }
            
            # Cache the result
            with open(cache_file, 'w') as f:
                json.dump(result, f)
                
            return result
    except ImportError:
        pass  # Fall through to pytube
    except Exception as e:
        print(f"yt-dlp failed for {video_id}, trying pytube: {str(e)}")
    
    # Then try pytube with better session handling
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': random.choice(USER_AGENTS),
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
        })
        
        # Create YouTube object with custom session
        yt = YouTube(
            f"https://www.youtube.com/watch?v={video_id}",
            defer_prefetch_init=True,
            allow_oauth_cache=True
        )
        
        # Manually set the stream monostate session
        yt._vid_info_url = f"https://www.youtube.com/get_video_info?video_id={video_id}"
        yt._js_url = None  # Skip JS download which often fails
        yt._js = None
        
        # Get video info
        video_info = yt.vid_info
        
        result = {
            'id': video_id,
            'title': yt.title or '',
            'description': yt.description or '',
            'publish_date': yt.publish_date.isoformat() if yt.publish_date else '',
            'url': f"https://www.youtube.com/watch?v={video_id}",
            'thumbnail': yt.thumbnail_url or f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg',
        }
        
        # Cache the result
        with open(cache_file, 'w') as f:
            json.dump(result, f)
            
        return result
    except Exception as e:
        print(f"PyTube error for {video_id}, trying Selenium fallback: {str(e)}")
        return get_video_details_with_selenium(video_id)

def get_channel_video_ids(channel_handle, max_results=50):
    """Get just the video IDs from a channel"""
    # Format the channel URL correctly for channel handles
    if channel_handle.startswith('@'):
        channel_url = f"https://www.youtube.com/{channel_handle}/videos"
    else:
        # If it doesn't start with @, add it
        channel_url = f"https://www.youtube.com/@{channel_handle}/videos"
        
    print(f"Fetching channel data from: {channel_url}")
    
    # Set up headless Chrome browser
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
    
    try:
        # Initialize driver
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(channel_url)
        
        # Wait for the videos to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "contents"))
        )
        
        # Scroll down to load more videos (optional)
        for _ in range(3):  # Scroll a few times to load more videos
            driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            time.sleep(2)  # Wait for content to load
        
        # Get page source after JavaScript has loaded content
        page_source = driver.page_source
        driver.quit()
        
        # Now use BeautifulSoup on the fully rendered page
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Video IDs can be found in multiple ways
        video_elements = soup.find_all('a', {'id': 'thumbnail', 'class': 'yt-simple-endpoint'})
        
        video_ids = []
        for elem in video_elements:
            href = elem.get('href', '')
            if '/watch?v=' in href:
                video_id = href.split('/watch?v=')[1].split('&')[0]
                if video_id not in video_ids:
                    video_ids.append(video_id)
        
        print(f"Found {len(video_ids)} video IDs")
        return video_ids
        
    except Exception as e:
        print(f"Error fetching channel data: {str(e)}")
        return []

def get_channel_videos_parallel(channel_handle, published_after=None, max_results=50, max_workers=4):
    """Get video details in parallel to speed up processing"""
    video_ids = get_channel_video_ids(channel_handle, max_results)
    
    videos = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_video = {executor.submit(get_video_details, vid): vid for vid in video_ids[:max_results]}
        
        # Process results as they complete
        for future in future_to_video:
            video_id = future_to_video[future]
            try:
                video_details = future.result()
                if video_details:
                    # Check publishing date if needed
                    if 'publish_date' in video_details and video_details['publish_date']:
                        try:
                            date_str = video_details['publish_date']
                            # Handle different date formats
                            if 'T' in date_str:
                                # ISO format
                                publish_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                            else:
                                # Text format like "Apr 9, 2023"
                                try:
                                    publish_date = datetime.strptime(date_str, "%b %d, %Y")
                                except:
                                    # Try other common YouTube date formats
                                    try:
                                        publish_date = datetime.strptime(date_str, "%d %b %Y")
                                    except:
                                        publish_date = None
                                        
                            if published_after and publish_date and publish_date < published_after:
                                continue
                        except:
                            # If we can't parse date, include video anyway
                            pass
                    
                    videos.append(video_details)
            except Exception as e:
                print(f"Error processing video {video_id}: {str(e)}")
                
    return videos

def get_channel_videos(channel_handle, published_after=None, max_results=50):
    """
    Get videos from a channel using Selenium to handle dynamic content
    """
    # Use the parallel version for better performance
    return get_channel_videos_parallel(channel_handle, published_after, max_results)
def get_video_transcript_with_selenium(video_id):
    """Get video transcript using Selenium when API method fails"""
    cache_file = os.path.join(CACHE_DIR, f"{video_id}_transcript.txt")
    
    # Set up Chrome browser
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        url = f"https://www.youtube.com/watch?v={video_id}"
        driver.get(url)
        
        # Click on the "..." menu to show more options
        time.sleep(2)
        try:
            more_button = driver.find_element(By.CSS_SELECTOR, "button[aria-label='More actions']")
            more_button.click()
            time.sleep(1)
            
            # Look for "Show transcript" option
            menu_items = driver.find_elements(By.CSS_SELECTOR, "tp-yt-paper-item")
            for item in menu_items:
                if "transcript" in item.text.lower():
                    item.click()
                    time.sleep(2)
                    break
            
            # Get transcript text
            transcript_container = driver.find_element(By.CSS_SELECTOR, "div#transcript-scrollbox")
            transcript_segments = transcript_container.find_elements(By.CSS_SELECTOR, "yt-formatted-string")
            
            transcript_text = []
            for segment in transcript_segments:
                text = segment.text.strip()
                if text:
                    transcript_text.append(text)
            
            full_transcript = " ".join(transcript_text)
            
            # Cache the result
            with open(cache_file, 'w') as f:
                f.write(full_transcript)
                
            driver.quit()
            return full_transcript
            
        except Exception as e:
            print(f"Selenium error getting transcript: {str(e)}")
            driver.quit()
            return None
            
    except Exception as e:
        print(f"Error setting up Selenium for transcript: {str(e)}")
        return None


def get_video_transcript(video_id):
    """Get video transcript/captions without using the API"""
    # Check cache first
    cache_file = os.path.join(CACHE_DIR, f"{video_id}_transcript.txt")
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                return f.read()
        except:
            # If cache read fails, continue with normal flow
            pass
    
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': random.choice(USER_AGENTS),
            'Accept-Language': 'en-US,en;q=0.5'
        })
        
        url = f"https://www.youtube.com/watch?v={video_id}"
        video = YouTube(url)
        
        # Attempt to set the session on the pytube object
        try:
            video.http = session
        except:
            # If this fails, continue anyway
            pass
        
        # Get English captions if available
        caption_tracks = video.captions
        captions = None
        
        # Try to get English captions
        if 'en' in caption_tracks:
            captions = caption_tracks['en']
        elif 'a.en' in caption_tracks:  # Auto-generated English
            captions = caption_tracks['a.en']
        else:
            # Get the first available caption track
            for lang_code in caption_tracks:
                captions = caption_tracks[lang_code]
                break
        
        if captions:
            # Get transcript as text
            transcript = captions.generate_srt_captions()
            
            # Clean up the transcript (remove timestamps and formatting)
            cleaned_transcript = re.sub(r'\d+\s+\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}\s+', '', transcript)
            cleaned_transcript = re.sub(r'\n\n', ' ', cleaned_transcript)
            
            # Cache the result
            with open(cache_file, 'w') as f:
                f.write(cleaned_transcript)
                
            return cleaned_transcript
        
        return None
    except Exception as e:
        print(f"Error getting transcript for {video_id}: {str(e)}")
        print("Trying Selenium fallback for transcript...")
        return get_video_transcript_with_selenium(video_id)

def get_last_year_timestamp():
    """Get datetime object for one year ago"""
    return datetime.now() - timedelta(days=365)

# Clean up function to close shared browser when done
def cleanup():
    if hasattr(get_shared_browser, "browser"):
        try:
            get_shared_browser.browser.quit()
        except:
            pass
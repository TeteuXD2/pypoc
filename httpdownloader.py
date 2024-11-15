import requests
from bs4 import BeautifulSoup
import re
import os
import time
from urllib.parse import urljoin, urlparse
import argparse
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.firefox import GeckoDriverManager
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Disclaimer Notice
def show_disclaimer():
    """Display a disclaimer about legal responsibility."""
    print("\nDISCLAIMER: By using this script, you acknowledge and agree that the script owner is not responsible for any legal issues, "
          "including but not limited to copyright infringements, illegal downloads, or any bans imposed by websites. "
          "Use this script at your own risk. Ensure you have the legal right to download content from the websites you scrape.\n")

# List of user-agent strings to mimic a browser request
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
]

EXCLUDED_DOMAINS = ['youtube.com', 'instagram.com', 'facebook.com', 'twitter.com', 'discord.com', 'telegram.org']
EXCLUDED_EXTENSIONS = ['.jpg', '.jpeg', '.gif', '.png']  # Excluded image formats
EXCLUDED_DIRS = ['/thumb/', '/thumbnail/', '/thumbnails/', '/tmb/', '/ads/', '/ad/', '/ads_content/']  # Directories to exclude
INCLUDED_DIRS = ['/videos/', '/video/', '/mp4/', '/hls/', '/get_file/', '/get_files/']  # Directories to include

DEBUG_MODE = True  # Set to False to disable debug prints

def debug_print(msg):
    """Print debug messages only if DEBUG_MODE is True."""
    if DEBUG_MODE:
        print(f"{Fore.CYAN}[DEBUG] {msg}{Style.RESET_ALL}")

def verbose_print(msg):
    """Print verbose messages."""
    print(f"{Fore.YELLOW}[VERBOSE] {msg}{Style.RESET_ALL}")

def error_print(msg):
    """Print error messages in red."""
    print(f"{Fore.RED}[ERROR] {msg}{Style.RESET_ALL}")

def info_print(msg):
    """Print info messages in light green."""
    print(f"{Fore.LIGHTGREEN_EX}[INFO] {msg}{Style.RESET_ALL}")

def is_excluded(url):
    """Check if the URL is from an excluded domain."""
    for domain in EXCLUDED_DOMAINS:
        if domain in url:
            debug_print(f"Excluded due to domain: {domain}")
            return True
    return False

def is_onion_domain(url):
    """Check if the URL is a .onion domain."""
    return '.onion' in urlparse(url).netloc

def fetch_page(url, use_selenium=False):
    """Fetch the webpage content, using Selenium for JavaScript-heavy sites."""
    if is_onion_domain(url):
        info_print(f"Blocking .onion domain: {url}")
        return None  # Block the request

    if use_selenium:
        return fetch_with_selenium(url)
    else:
        return fetch_with_requests(url)

def fetch_with_requests(url):
    """Fetch the page content using requests and parse it with BeautifulSoup."""
    headers = {'User-Agent': USER_AGENTS[0]}  # Pick a random user-agent here if needed
    try:
        verbose_print(f"Fetching page: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.text
    except requests.RequestException as e:
        error_print(f"Error fetching page {url}: {e}")
        return None

def fetch_with_selenium(url):
    """Fetch the page content using Selenium (for JavaScript-heavy sites) with Firefox."""
    if is_onion_domain(url):
        info_print(f"Blocking .onion domain: {url}")
        return None  # Block the request

    try:
        verbose_print(f"Fetching page (Selenium with Firefox): {url}")
        options = webdriver.FirefoxOptions()
        options.add_argument('--headless')  # Run headless to avoid opening a browser window
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # Firefox WebDriver setup
        driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)
        driver.get(url)
        time.sleep(5)  # Wait for JavaScript to load
        page_content = driver.page_source
        driver.quit()
        return page_content
    except Exception as e:
        error_print(f"Error fetching page with Selenium (Firefox): {e}")
        return None

def is_video_file(url):
    """Check if the URL points to a video file (m3u8, mp4, ts, mov, m4v)."""
    return re.search(r'\.(m3u8|mp4|ts|mov|m4v)$', url, re.IGNORECASE)

def find_video_links(page_content, base_url):
    """Extract video links (m3u8, mp4, ts, mov, m4v) from the HTML content."""
    video_urls = []

    # Regex patterns to find m3u8, mp4, ts, mov, m4v files
    patterns = [
        r'https?://[^\s]+\.m3u8',  # m3u8 pattern
        r'https?://[^\s]+\.mp4',   # mp4 pattern
        r'https?://[^\s]+\.ts',    # ts pattern
        r'https?://[^\s]+\.mov',   # mov pattern
        r'https?://[^\s]+\.m4v'    # m4v pattern
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, page_content)
        for match in matches:
            if match not in video_urls:
                verbose_print(f"Found video link: {match}")
                video_urls.append(match)

    # Handle relative URLs (m3u8, mp4, ts, mov, m4v)
    soup = BeautifulSoup(page_content, 'html.parser')
    for link in soup.find_all('a', href=True):
        href = link['href']
        if is_video_file(href):
            video_url = urljoin(base_url, href)  # Ensure absolute URL
            if video_url not in video_urls:
                verbose_print(f"Found video link (relative URL): {video_url}")
                video_urls.append(video_url)

    # Find and scrape embed links
    for iframe in soup.find_all('iframe', src=True):
        iframe_src = iframe['src']
        if '/embed/' in iframe_src:
            embed_url = urljoin(base_url, iframe_src)  # Ensure absolute URL
            verbose_print(f"Found embed link: {embed_url}")
            embed_page_content = fetch_page(embed_url)
            if embed_page_content:
                video_urls.extend(find_video_links(embed_page_content, embed_url))

    # Filter out image URLs (jpg, jpeg, gif, png)
    video_urls = [url for url in video_urls if not any(url.lower().endswith(ext) for ext in EXCLUDED_EXTENSIONS)]
    debug_print(f"Video links after filtering image files: {video_urls}")

    # Exclude videos from certain directories, but **not** from directories in INCLUDED_DIRS
    video_urls = [url for url in video_urls if not any(excluded_dir in url and not any(included_dir in url for included_dir in INCLUDED_DIRS) for excluded_dir in EXCLUDED_DIRS)]
    debug_print(f"Video links after filtering excluded directories: {video_urls}")
    
    # Block any file that contains "preview" in the name or URL
    video_urls = [url for url in video_urls if "preview" not in os.path.basename(url).lower()]
    debug_print(f"Video links after filtering 'preview' in the filename: {video_urls}")

    return video_urls

def download_video(url, download_folder="downloads"):
    """Download a video file with progress indicator and prompt to rename after downloading."""
    if is_onion_domain(url):
        info_print(f"Blocking .onion domain: {url}")
        return  # Block download for .onion domains

    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Get the total file size from the response headers
        total_size = int(response.headers.get('Content-Length', 0))
        filename = url.split('/')[-1]
        filepath = os.path.join(download_folder, filename)

        # Create the download folder if it doesn't exist
        if not os.path.exists(download_folder):
            os.makedirs(download_folder)

        # Download and save the file in chunks
        with open(filepath, 'wb') as file:
            downloaded = 0  # Keep track of how much we've downloaded
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
                    downloaded += len(chunk)

                    # Print download progress
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\rDownloaded {percent:.2f}% ({downloaded}/{total_size} bytes)", end="")

        print(f"\nDownloaded: {filename}")

        # Ask if user wants to rename the file after download
        rename_file(filepath)

    except requests.RequestException as e:
        error_print(f"Error downloading {url}: {e}")

def rename_file(filepath):
    """Prompt the user to rename the downloaded file."""
    rename = input("Do you want to rename the downloaded file? (yes/no): ").strip().lower()
    if rename in ['yes', 'y']:
        new_name = input("Enter the new name (without extension): ").strip()
        if new_name:
            new_filepath = os.path.join(os.path.dirname(filepath), new_name + os.path.splitext(filepath)[1])
            os.rename(filepath, new_filepath)
            print(f"File renamed to: {new_filepath}")
        else:
            print(f"{Fore.LIGHTGREEN_EX}[INFO] No new name provided. Keeping the original file name.")
    else:
        print(f"{Fore.LIGHTGREEN_EX}[INFO] File not renamed.")

def is_valid_url(url):
    """Check if the URL is properly formatted."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])  # Ensure it has a valid scheme and netloc
    except ValueError:
        return False

def ask_to_download(url):
    """Ask the user if they want to download a video URL with a file extension."""
    answer = input(f"Do you want to download the video: {url} (yes/no)? ").strip().lower()
    if answer in ['yes', 'y']:
        download_video(url)
    else:
        print(f"{Fore.LIGHTGREEN_EX}[INFO] Download cancelled.")

def scrape_website(url, use_selenium=False):
    """Scrape the website for video files."""
    if is_excluded(url) or is_onion_domain(url):
        verbose_print(f"Skipping excluded or .onion domain site: {url}")
        return []

    verbose_print(f"Scraping {url}...")
    page_content = fetch_page(url, use_selenium)
    if page_content:
        video_links = find_video_links(page_content, url)
        if video_links:
            verbose_print(f"Found {len(video_links)} video links on {url}")
            return video_links
        else:
            print(f"{Fore.LIGHTGREEN_EX}[INFO] No video links found on this page.")
    return []

def main():
    # Display disclaimer at the start
    show_disclaimer()

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Scrape video links from websites.")
    parser.add_argument('url', help='The URL of the website to scrape.')
    parser.add_argument('-s', '--selenium', action='store_true', help="Use Selenium for JavaScript-heavy pages.")
    args = parser.parse_args()

    # Ensure the URL is valid and starts with http:// or https://
    website_url = args.url
    if not website_url.startswith(('http://', 'https://')):
        error_print('[ERROR] Please provide a URL starting with "http://" or "https://"')
        return

    if not is_valid_url(website_url):
        error_print('[ERROR] Invalid URL format. Please check the URL and try again.')
        return
    
    # Scrape the provided website
    video_links = scrape_website(website_url, use_selenium=args.selenium)
    
    if video_links:
        print("\nFound the following video links:")
        for i, link in enumerate(video_links, start=1):
            print(f"{i}. {link}")

        # Check if the video URL has a file extension (mp4, m3u8, ts, mov, m4v, etc.)
        for link in video_links:
            if is_video_file(link):
                ask_to_download(link)

        # Optionally ask to download files that don't have file extensions
        print("\nOptionally you can choose to download videos that aren't automatically recognized as having a file extension.")
        try:
            choice = int(input("\nEnter the number of the video to download (0 to cancel): ").strip())
            if choice == 0:
                print(f"{Fore.LIGHTGREEN_EX}[INFO] Download cancelled.")
                return
            selected_url = video_links[choice - 1]
            if not is_video_file(selected_url):  # If the file doesn't have an extension
                ask_to_download(selected_url)
            else:
                download_video(selected_url)  # Already confirmed or automatic download
        except (ValueError, IndexError):
            error_print("[ERROR] Invalid selection. Please enter a valid number.")
    else:
        print(f"{Fore.LIGHTGREEN_EX}[INFO] No video links found.")

if __name__ == '__main__':
    main()


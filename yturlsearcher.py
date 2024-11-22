import random
import string
import requests
from googleapiclient.discovery import build
from langdetect import detect
import time

# Set up YouTube API key and initialize the YouTube client
API_KEY = 'YOUR_API_KEY'  # Replace with your actual API key
youtube = build('youtube', 'v3', developerKey=API_KEY)

# List of languages to show (ISO 639-1 codes)
SELECTED_LANGUAGES = ['pt-br', 'pt']  # Add more languages as needed

# Pattern to detect "Video unavailable"
pattern = '"playabilityStatus":{"status":"ERROR","reason":"Video unavailable"'

# Function to generate random video ID
def generate_random_video_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=11))

# Function to check if a video exists on YouTube using YouTube Data API
def video_exists(video_id):
    try:
        response = youtube.videos().list(part='snippet,contentDetails', id=video_id).execute()
        return len(response['items']) > 0  # If the video exists, there will be items
    except Exception as e:
        print(f"Error checking video ID {video_id}: {e}")
        return False

# Function to detect language from a text string (title or description)
def detect_language(text):
    try:
        return detect(text)
    except Exception as e:
        print(f"Error detecting language: {e}")
        return 'unknown'

# Function to check if the video is unavailable by making an HTTP request
def try_site(url):
    try:
        request = requests.get(url)
        return False if pattern in request.text else True
    except Exception as e:
        print(f"Error accessing URL {url}: {e}")
        return False

# Function to check multiple videos
def check_multiple_videos(rate=10):
    count = 0
    while count < rate:
        video_id = generate_random_video_id()
        video_url = f"https://youtube.com/watch?v={video_id}"

        print(f"Checking video: {video_url}")

        if video_exists(video_id):
            print(f"Video {video_url} exists!")
            # Check if the video is unavailable
            if not try_site(video_url):
                print(f"Video {video_url} is unavailable.")
                count += 1
                time.sleep(1)
                continue

            # Get video details
            video_details = youtube.videos().list(part='snippet,contentDetails', id=video_id).execute()
            title = video_details['items'][0]['snippet']['title']
            description = video_details['items'][0]['snippet']['description']
            duration = video_details['items'][0]['contentDetails']['duration']

            print(f"Title: {title}")
            print(f"Description: {description}")
            print(f"Duration: {duration}")

            # Detect language of title and description
            title_lang = detect_language(title)
            description_lang = detect_language(description)

            print(f"Detected language of title: {title_lang}")
            print(f"Detected language of description: {description_lang}")

            # Check if the detected languages match the selected ones
            if title_lang in SELECTED_LANGUAGES or description_lang in SELECTED_LANGUAGES:
                print(f"** This video matches the selected languages! **")
            else:
                print("This video does not match the selected languages.")
        else:
            print(f"Video {video_url} does not exist.")

        count += 1
        # Optional: add a delay to avoid hitting API rate limits
        time.sleep(15)

# Set how many videos to check
rate_of_videos = 255  # For example, check 15 videos
check_multiple_videos(rate=rate_of_videos)

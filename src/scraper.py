"""
Safely Endangered Comic Scraper

This module provides functionality to scrape Safely Endangered comics, including the comic image
and title. It fetches the current latest comic from the Safely Endangered website.

Usage:
    python scraper.py
"""

import datetime
import os
import shutil
from typing import Optional, Dict
from bs4 import BeautifulSoup
import requests


# Constants
SE_BASE_URL = "https://safelyendangered.com/"
INVALID_FILENAME_CHARS = ['/', '\\', '?', '%', '*', ':', '|', '"', '<', '>', '.']


def sanitize_filename(filename: str) -> str:
    """
    Remove characters from a string that are invalid in filenames.

    Args:
        filename: The original filename string to sanitize

    Returns:
        A sanitized filename string with invalid characters removed
    """
    return ''.join(char for char in filename if char not in INVALID_FILENAME_CHARS)


def fetch_webpage(url: str) -> Optional[BeautifulSoup]:
    """
    Fetch and parse a webpage into a BeautifulSoup object.

    Args:
        url: The URL of the webpage to fetch

    Returns:
        BeautifulSoup object if successful, None if request fails
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None


def extract_comic_data(soup: BeautifulSoup) -> Optional[Dict[str, str]]:
    """
    Extract comic data (comic page URL and title) from parsed HTML.

    Args:
        soup: BeautifulSoup object containing the parsed Safely Endangered homepage

    Returns:
        Dictionary containing 'comic_url' and 'title' keys,
        or None if extraction fails
    """
    try:
        # Find the featured blog post
        comic_li = soup.find('li', id=lambda x: x and x.startswith('Slide-template--17273659850913__featured_blog_'))
        if comic_li is None:
            print("Error: Could not find comic list item")
            return None

        # Extract comic link and title
        comic_link = comic_li.find('a', class_='full-unstyled-link')
        if comic_link is None:
            print("Error: Could not find comic link")
            return None

        comic_url = SE_BASE_URL.rstrip('/') + comic_link['href']
        title = comic_link.text.strip()

        return {
            'comic_url': comic_url,
            'title': title
        }
    except (AttributeError, KeyError, TypeError) as e:
        print(f"Error extracting comic data: {e}")
        return None


def extract_comic_image_url(soup: BeautifulSoup) -> Optional[str]:
    """
    Extract comic image URL from the comic page.

    Args:
        soup: BeautifulSoup object containing the parsed comic page

    Returns:
        The comic image URL, or None if extraction fails
    """
    try:
        # Find the hero container with the comic image
        comic_hero = soup.find('div', class_='article-template__hero-container')
        if comic_hero is None:
            print("Error: Could not find comic hero container")
            return None

        comic_img = comic_hero.find('img')
        if comic_img is None:
            print("Error: Could not find comic image")
            return None

        image_url = comic_img['src'].replace('//', 'https://')
        # Remove query parameters and get the full resolution image
        if '?' in image_url:
            base_url = image_url.split('?')[0]
            return base_url
        return image_url
    except (AttributeError, KeyError, TypeError) as e:
        print(f"Error extracting comic image URL: {e}")
        return None


def download_image(image_url: str) -> Optional[bytes]:
    """
    Download image data from a URL.

    Args:
        image_url: The URL of the image to download

    Returns:
        Image data as bytes if successful, None if download fails
    """
    # Add https: prefix if not present
    if image_url.startswith("//"):
        image_url = "https:" + image_url

    try:
        response = requests.get(image_url)
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        print(f"Error downloading image from {image_url}: {e}")
        return None


def save_image(image_data: bytes, filepath: str) -> bool:
    """
    Save image data to a file.

    Args:
        image_data: The image data as bytes
        filepath: The path where the image should be saved

    Returns:
        True if successful, False otherwise
    """
    try:
        with open(filepath, 'wb') as handler:
            handler.write(image_data)
        return True
    except IOError as e:
        print(f"Error saving image to {filepath}: {e}")
        return False


def get_file_extension(url: str) -> str:
    """
    Extract file extension from a URL.

    Args:
        url: The URL to extract extension from

    Returns:
        File extension (e.g., 'png', 'jpg')
    """
    return url.split('.')[-1]



def get_current_comic() -> Optional[str]:
    """
    Download the current latest Safely Endangered comic.

    This function fetches the Safely Endangered homepage to get the latest comic,
    then downloads the image to the current working directory.

    Returns:
        The sanitized title of the comic if successful, None otherwise
    """
    # Fetch the main Safely Endangered page
    soup = fetch_webpage(SE_BASE_URL)
    if soup is None:
        return None

    # Extract comic data (URL and title from homepage)
    comic_data = extract_comic_data(soup)
    if comic_data is None:
        return None

    # Fetch the comic page
    comic_page_soup = fetch_webpage(comic_data['comic_url'])
    if comic_page_soup is None:
        return None

    # Extract the image URL from the comic page
    image_url = extract_comic_image_url(comic_page_soup)
    if image_url is None:
        return None

    # Sanitize the title for use as filename
    sanitized_title = sanitize_filename(comic_data['title'])

    # Download the image
    image_data = download_image(image_url)
    if image_data is None:
        return None

    # Save the image
    file_extension = get_file_extension(image_url)
    image_path = f"{sanitized_title}.{file_extension}"
    if not save_image(image_data, image_path):
        return None


    print(f"Successfully downloaded current comic: {comic_data['title']}")
    return sanitized_title


def get_most_recent_previous_directory() -> Optional[str]:
    """
    Get the most recent previous data directory (not including today).

    Returns:
        The absolute path to the most recent previous directory, or None if none exists
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_root = os.path.join(project_root, 'data')

    if not os.path.exists(data_root):
        return None

    # Get today's date for comparison
    today = datetime.datetime.now().strftime("%Y-%m-%d")

    # Get all subdirectories in data folder
    subdirs = [d for d in os.listdir(data_root)
               if os.path.isdir(os.path.join(data_root, d)) and d != today]

    if not subdirs:
        return None

    # Sort and get the most recent one
    subdirs.sort(reverse=True)
    return os.path.join(data_root, subdirs[0])


def get_previous_comic_title() -> Optional[str]:
    """
    Get the title of the most recent previous comic.

    Returns:
        The title of the previous comic (without extension), or None if not found
    """
    prev_dir = get_most_recent_previous_directory()
    if prev_dir is None:
        return None

    # List all files in the previous directory
    try:
        files = os.listdir(prev_dir)
        # Filter for image files (png, jpg, gif, etc.)
        image_files = [f for f in files if f.endswith(('.png', '.jpg', '.jpeg', '.gif'))]
        if image_files:
            # Remove extension to get title
            title = os.path.splitext(image_files[0])[0]
            return title
    except OSError:
        return None

    return None


def setup_daily_directory() -> str:
    """
    Create and return the path to today's data directory.

    Creates a directory structure: data/YYYY-MM-DD/ relative to the project root.

    Returns:
        The absolute path to the created directory
    """
    # Get current date
    date = datetime.datetime.now().strftime("%Y-%m-%d")

    # Construct path to data directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(project_root, 'data', date)

    # Create directory if it doesn't exist
    os.makedirs(data_dir, exist_ok=True)

    return data_dir


def main():
    """
    Main function to run the daily comic scraper.

    Sets up the daily directory and downloads the current Safely Endangered comic.
    If the current comic is the same as the previous day's comic,
    the download is skipped and the directory is removed.
    """
    # Create and change to today's data directory
    data_dir = setup_daily_directory()
    os.chdir(data_dir)

    print(f"Saving comic to: {data_dir}")

    # Get the previous comic title for comparison
    previous_comic_title = get_previous_comic_title()

    # Download the current comic
    current_comic_title = get_current_comic()

    if current_comic_title is None:
        print("Failed to download comic.")
        # Clean up the directory if download failed
        os.chdir(os.path.dirname(data_dir))
        shutil.rmtree(data_dir)
        return

    # Check if today's comic is the same as the previous comic
    if previous_comic_title and current_comic_title == previous_comic_title:
        print(f"Today's comic '{current_comic_title}' is the same as the previous comic.")
        print(f"Removing directory: {data_dir}")
        # Change out of the directory before removing it
        os.chdir(os.path.dirname(data_dir))
        shutil.rmtree(data_dir)
        print("No new comic available today.")
    else:
        print("Comic download completed successfully!")


if __name__ == "__main__":
    main()


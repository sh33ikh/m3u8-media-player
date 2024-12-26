import os
import requests
from bs4 import BeautifulSoup
import logging
from urllib.parse import urljoin
import concurrent.futures
from requests.exceptions import RequestException
from colorama import Fore, init
import re

# Initialize colorama for cross-platform support
init(autoreset=True)

# Enable logging with colors
logging.basicConfig(level=logging.DEBUG, format=f'{Fore.CYAN}%(asctime)s - %(levelname)s - %(message)s')

# Modern headers to mimic a browser request
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive',
}

# Function to fetch video links
def fetch_video_links(url):
    try:
        logging.info(f"{Fore.YELLOW}Sending request to {url}")
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Parse the page content using BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all links to video files (multiple formats)
        links = [urljoin(url, link['href']) for link in soup.find_all('a', href=True) if link['href'].endswith(('.mkv', '.mp4', '.avi', '.webm'))]

        logging.info(f"{Fore.GREEN}Found {len(links)} video links.")
        return links
    except RequestException as e:
        logging.error(f"{Fore.RED}Error fetching URL: {e}")
        return []

# Function to generate m3u8 playlist with original file names
def generate_m3u8_playlist(video_links, output_file='final_playlist.m3u8'):
    try:
        logging.info(f"{Fore.CYAN}Generating m3u8 playlist in {output_file}")
        with open(output_file, 'w') as f:
            f.write('#EXTM3U\n')

            # Iterate through the video links
            for video in video_links:
                file_name = os.path.basename(video)  # Extract original file name
                duration = 10  # Set a default duration for each video segment
                f.write(f'#EXTINF:{duration}, {file_name}\n')  # Include the original file name in m3u8
                f.write(f'{video}\n')

        logging.info(f"{Fore.GREEN}m3u8 playlist generated successfully.")
    except Exception as e:
        logging.error(f"{Fore.RED}Error generating m3u8 playlist: {e}")

# Function to fetch video links concurrently
def fetch_video_links_concurrently(urls):
    video_links = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(fetch_video_links, url): url for url in urls}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                links = future.result()
                video_links.extend(links)
            except Exception as e:
                logging.error(f"{Fore.RED}Error processing {url}: {e}")
    return video_links

# Main function to orchestrate the process
def main():
    logging.info(f"{Fore.MAGENTA}Starting the video link fetch and playlist generation process.")
    
    # Ask user for the URL to use for fetching video links
    base_url = input(f"{Fore.GREEN}Please enter the URL for the video series directory: ")
    
    # Validate the URL format (basic validation)
    if not base_url.startswith('http'):
        logging.error(f"{Fore.RED}Invalid URL. Please enter a valid URL that starts with 'http'.")
        return
    
    # Fetch video links concurrently from the given URL
    video_links = fetch_video_links_concurrently([base_url])

    if video_links:
        # Ask for the output file name (with a default)
        output_file = input(f"{Fore.YELLOW}Enter the output filename (default is 'final_playlist.m3u8'): ")
        if not output_file:
            output_file = 'final_playlist.m3u8'

        generate_m3u8_playlist(video_links, output_file)
    else:
        logging.error(f"{Fore.RED}No video links found.")

    logging.info(f"{Fore.YELLOW}For more updates, join our community at: {Fore.CYAN}t.me/RektDevelopers")

if __name__ == '__main__':
    main()

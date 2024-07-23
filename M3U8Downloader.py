import requests
from urllib.parse import urljoin
from moviepy.editor import VideoFileClip
import os
from tqdm import tqdm

class M3U8Downloader:
    """
    A class to download and convert video from a given M3U8 URL.

    Attributes:
        url (str): The URL of the M3U8 playlist.
        m3u8_content (str): The content of the M3U8 file.
        media_urls (dict): A dictionary mapping resolution names to media URLs.
        output_mp4 (str): The name of the output MP4 file.
    """

    def __init__(self, url, output_mp4="output.mp4"):
        """
        Initializes the M3U8Downloader with the provided URL and starts the download process.

        Parameters:
            url (str): The URL of the M3U8 playlist.
            output_mp4 (str): The name of the output MP4 file.
        """
        self.url = url
        self.m3u8_content = None
        self.media_urls = {}
        self.output_mp4 = output_mp4

        # Start the process immediately upon initialization
        self.download_m3u8()
        self.parse_m3u8()
        self.ask_resolution_and_download()

    def download_m3u8(self):
        """
        Downloads the M3U8 file from the given URL.
        """
        response = requests.get(self.url)
        if response.status_code == 200:
            self.m3u8_content = response.text
            print("Successfully downloaded the .m3u8 file.")
        else:
            raise Exception(f"Failed to download .m3u8 file. Status code: {response.status_code}")

    def parse_m3u8(self):
        """
        Parses the M3U8 file content to extract media URLs and resolutions.
        """
        lines = self.m3u8_content.splitlines()
        for line in lines:
            if line.startswith('https://'):
                # Extract the resolution name from the previous line if it exists
                resolution_line = lines[lines.index(line) - 1] if lines.index(line) > 0 else ""
                resolution = self.extract_resolution(resolution_line)
                self.media_urls[resolution] = line

    def extract_resolution(self, line):
        """
        Extracts the resolution name from a line of the M3U8 file.

        Parameters:
            line (str): A line from the M3U8 file.

        Returns:
            str: The resolution name (e.g., "1080p").
        """
        if 'RESOLUTION=' in line:
            resolution = line.split('RESOLUTION=')[1].split(',')[0]
            return resolution
        return "Unknown"

    def ask_resolution_and_download(self):
        """
        Prompts the user to select a resolution and then downloads and merges the video segments.
        """
        if not self.media_urls:
            print("No media URLs found.")
            return

        print("Available resolutions:")
        for index, (resolution, url) in enumerate(self.media_urls.items()):
            print(f"{index + 1}. {resolution} - {url}")

        choice = input("Enter the resolution name (e.g., 1080p) or number (e.g., 1) or press Enter to select the highest resolution: ").strip()

        if choice.isdigit():
            choice = int(choice)
            if 1 <= choice <= len(self.media_urls):
                selected_resolution = list(self.media_urls.keys())[choice - 1]
            else:
                print("Invalid choice.")
                return
        else:
            selected_resolution = choice if choice in self.media_urls else None
            if selected_resolution is None:
                print("Invalid resolution name.")
                return

        selected_url = self.media_urls.get(selected_resolution, None)
        if selected_url:
            self.merge_segments_and_convert(selected_url)
        else:
            print("Resolution not found.")

    def merge_segments_and_convert(self, url):
        """
        Downloads the media file from the selected URL, merges the segments, and converts them to MP4.

        Parameters:
            url (str): The URL of the selected media stream.
        """
        response = requests.get(url)
        if response.status_code == 200:
            m3u8_content = response.text
            print("Successfully downloaded the media .m3u8 file.")

            # Parse and merge segments
            self.concatenate_segments(m3u8_content)
        else:
            print(f"Failed to download media .m3u8 file. Status code: {response.status_code}")

    def concatenate_segments(self, m3u8_content):
        """
        Merges video segments from the M3U8 playlist into a single temporary .ts file.

        Parameters:
            m3u8_content (str): The content of the media M3U8 file.
        """
        lines = m3u8_content.splitlines()
        base_url = "https://embed-cloudfront.wistia.com"  # Base URL for segments
        temp_ts_file = "temp.ts"

        # Get the segment URLs
        segment_urls = [urljoin(base_url, line) for line in lines if line.startswith('/')]

        # Download segments with a progress bar
        with open(temp_ts_file, 'wb') as outfile:
            for segment_url in tqdm(segment_urls, desc="Downloading and merging segments", unit="segment"):
                response = requests.get(segment_url, stream=True)
                if response.status_code == 200:
                    for chunk in response.iter_content(chunk_size=8192):
                        outfile.write(chunk)
                else:
                    print(f"Failed to download segment. Status code: {response.status_code}")

        print(f"All segments have been merged into {temp_ts_file}.")
        self.convert_to_mp4(temp_ts_file)

    def convert_to_mp4(self, ts_file):
        """
        Converts the temporary .ts file to an MP4 file using moviepy and then deletes the temporary file.

        Parameters:
            ts_file (str): The name of the temporary .ts file.
        """
        try:
            # Use moviepy to convert the .ts file to .mp4
            video_clip = VideoFileClip(ts_file)
            video_clip.write_videofile(self.output_mp4, codec='libx264')
            print(f"Successfully converted {ts_file} to {self.output_mp4}.")
        except Exception as e:
            print(f"Failed to convert video. Error: {e}")
        finally:
            # Explicitly close the video clip to ensure file is not in use
            if 'video_clip' in locals():
                video_clip.close()

            # Delete the temporary .ts file
            if os.path.exists(ts_file):
                try:
                    os.remove(ts_file)
                    print(f"Deleted temporary file {ts_file}.")
                except PermissionError as e:
                    print(f"Failed to delete temporary file. Error: {e}")


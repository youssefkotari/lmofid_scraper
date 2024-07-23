import requests
from urllib.parse import urljoin
from moviepy.editor import VideoFileClip
import os

class M3U8Downloader:
    def __init__(self, url):
        self.url = url
        self.m3u8_content = None
        self.media_urls = {}
    
    def download_m3u8(self):
        # Download the .m3u8 file
        response = requests.get(self.url)
        if response.status_code == 200:
            self.m3u8_content = response.text
            print("Successfully downloaded the .m3u8 file.")
        else:
            raise Exception(f"Failed to download .m3u8 file. Status code: {response.status_code}")

    def parse_m3u8(self):
        # Parse the .m3u8 file content
        lines = self.m3u8_content.splitlines()
        for line in lines:
            if line.startswith('https://'):
                # Extract the resolution name from the previous line if it exists
                resolution_line = lines[lines.index(line) - 1] if lines.index(line) > 0 else ""
                resolution = self.extract_resolution(resolution_line)
                self.media_urls[resolution] = line

    def extract_resolution(self, line):
        # Extract resolution name from the line
        if 'RESOLUTION=' in line:
            resolution = line.split('RESOLUTION=')[1].split(',')[0]
            return resolution
        return "Unknown"

    def ask_resolution_and_download(self):
        # Display available resolutions and ask user for their choice
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
        # Download the media file from the selected URL
        response = requests.get(url)
        if response.status_code == 200:
            m3u8_content = response.text
            print("Successfully downloaded the media .m3u8 file.")

            # Parse and merge segments
            self.concatenate_segments(m3u8_content)
        else:
            print(f"Failed to download media .m3u8 file. Status code: {response.status_code}")

    def concatenate_segments(self, m3u8_content):
        # Parse the segment URLs from the downloaded .m3u8 file
        lines = m3u8_content.splitlines()
        base_url = "https://embed-cloudfront.wistia.com"  # Base URL for segments
        temp_ts_file = "temp.ts"

        with open(temp_ts_file, 'wb') as outfile:
            for line in lines:
                if line.startswith('/'):
                    # Full URL for the segment
                    segment_url = urljoin(base_url, line)
                    print(f"Downloading segment: {segment_url}")
                    response = requests.get(segment_url, stream=True)
                    if response.status_code == 200:
                        for chunk in response.iter_content(chunk_size=8192):
                            outfile.write(chunk)
                        print(f"Segment downloaded and appended.")
                    else:
                        print(f"Failed to download segment. Status code: {response.status_code}")

        print(f"All segments have been merged into {temp_ts_file}.")
        self.convert_to_mp4(temp_ts_file)

    def convert_to_mp4(self, ts_file):
        # Convert the .ts file to .mp4 using moviepy
        output_file = "output.mp4"
        try:
            video_clip = VideoFileClip(ts_file)
            video_clip.write_videofile(output_file, codec='libx264')
            print(f"Successfully converted {ts_file} to {output_file}.")
        except Exception as e:
            print(f"Failed to convert video. Error: {e}")
        finally:
            # Delete the temporary .ts file
            if os.path.exists(ts_file):
                os.remove(ts_file)
                print(f"Deleted temporary file {ts_file}.")

if __name__ == "__main__":
    url = "https://fast.wistia.com/embed/medias/w9dz27s7pu.m3u8"
    downloader = M3U8Downloader(url)
    
    downloader.download_m3u8()
    downloader.parse_m3u8()
    downloader.ask_resolution_and_download()

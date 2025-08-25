import os

from crewai_tools import BaseTool
import pyktok as pyk

from ..settings import DOWNLOADS_DIR

class TikTokDownloadTool(BaseTool):
    name: str = "TikTok Download Tool"
    description: str = "Download TikTok videos and their metadata using pyktok."

    def __init__(self):
        super().__init__()
        # It's recommended to have your TikTok cookies available for pyktok to use.
        # You can generate these by logging into TikTok in a browser.
        pyk.specify_browser("chrome")

    def _run(self, video_url: str) -> dict:
        """Download a TikTok video and its metadata."""
        try:
            target_dir = DOWNLOADS_DIR / "TikTok"
            os.makedirs(target_dir, exist_ok=True)
            
            # pyktok.save_tiktok downloads the video and saves the metadata to a CSV file.
            # The third argument is the name of the CSV file.
            pyk.save_tiktok(video_url, True, f"{target_dir}/tiktok_data.csv")
            
            # Since we don't have the exact filename of the downloaded video,
            # we will return the directory where it was saved.
            return {
                'status': 'success',
                'video_url': video_url,
                'local_path': str(target_dir)
            }
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

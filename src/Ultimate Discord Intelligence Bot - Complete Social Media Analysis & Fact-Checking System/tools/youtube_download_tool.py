import logging
import os
import subprocess

from crewai_tools import BaseTool

from ..settings import (
    DOWNLOADS_DIR,
    YTDLP_ARCHIVE,
    YTDLP_CONFIG,
    TEMP_DIR,
)

class YouTubeDownloadTool(BaseTool):
    name: str = "YouTube Download Tool"
    description: str = "Download YouTube videos with optimal settings for Discord sharing"

    def _run(self, video_url: str, quality: str = "1080p") -> dict:
        """Download YouTube video using yt-dlp with CrewAI integration"""
        
        config_file = str(YTDLP_CONFIG)

        # Construct command with quality-specific settings
        command = [
            "yt-dlp",
            "--config-locations",
            config_file,
            "--print",
            "%(id)s|%(title)s|%(uploader)s|%(duration)s|%(filesize_approx)s|%(filepath)s",
            video_url,
        ]

        env = os.environ.copy()
        env.update(
            {
                "CREWAI_DOWNLOADS_DIR": str(DOWNLOADS_DIR),
                "CREWAI_YTDLP_ARCHIVE": str(YTDLP_ARCHIVE),
                "CREWAI_TEMP_DIR": str(TEMP_DIR),
            }
        )

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=1800,  # 30 minutes max
                env=env,
            )

            if result.returncode == 0:
                # Parse output for metadata
                output_lines = result.stdout.strip().split("\n")
                download_info = output_lines[-1].split("|")

                local_path = download_info[5]
                return {
                    "status": "success",
                    "video_id": download_info[0],
                    "title": download_info[1],
                    "uploader": download_info[2],
                    "duration": download_info[3],
                    "file_size": download_info[4],
                    "local_path": local_path,
                    "download_command": " ".join(command),
                }
            else:
                return {
                    "status": "error",
                    "error": result.stderr,
                    "command": " ".join(command),
                }

        except subprocess.TimeoutExpired:
            return {"status": "error", "error": "Download timeout after 30 minutes"}
        except Exception as e:
            logging.exception("YouTube download failed")
            return {"status": "error", "error": str(e)}

    # Provide run wrapper for consistency with other tools
    def run(self, *args, **kwargs):  # pragma: no cover - thin wrapper
        return self._run(*args, **kwargs)

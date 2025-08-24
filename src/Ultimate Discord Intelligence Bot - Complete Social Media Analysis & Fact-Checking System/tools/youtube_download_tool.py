from crewai_tools import BaseTool
import subprocess
import json

class YouTubeDownloadTool(BaseTool):
    name: str = "YouTube Download Tool"
    description: str = "Download YouTube videos with optimal settings for Discord sharing"
    
    def _run(self, video_url: str, quality: str = "1080p") -> str:
        """Download YouTube video using yt-dlp with CrewAI integration"""
        
        config_file = "F:/yt-auto/crewaiv2/yt-dlp/config/crewai-system.conf"
        
        # Construct command with quality-specific settings
        command = [
            "yt-dlp",
            "--config-locations", config_file,
            "--print", "%(id)s|%(title)s|%(uploader)s|%(duration)s|%(filesize_approx)s",
            video_url
        ]
        
        try:
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                timeout=1800  # 30 minutes max
            )
            
            if result.returncode == 0:
                # Parse output for metadata
                output_lines = result.stdout.strip().split('\n')
                download_info = output_lines[-1].split('|')
                
                return json.dumps({
                    'status': 'success',
                    'video_id': download_info[0],
                    'title': download_info[1],
                    'uploader': download_info[2],
                    'duration': download_info[3],
                    'file_size': download_info[4],
                    'local_path': f"F:/yt-auto/crewaiv2/CrewAI_Content_System/Downloads/YouTube/{download_info[2]}/",
                    'download_command': ' '.join(command)
                })
            else:
                return json.dumps({
                    'status': 'error',
                    'error': result.stderr,
                    'command': ' '.join(command)
                })
                
        except subprocess.TimeoutExpired:
            return json.dumps({
                'status': 'error',
                'error': 'Download timeout after 30 minutes'
            })
        except Exception as e:
            return json.dumps({
                'status': 'error', 
                'error': str(e)
            })

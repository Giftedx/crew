from crewai_tools import BaseTool
import cv2
from moviepy.editor import VideoFileClip
import os

from ..settings import PROCESSING_DIR

class VideoAnalysisTool(BaseTool):
    name: str = "Video Analysis Tool"
    description: str = "Analyze video content to extract metadata, generate summaries, and transcribe audio."

    def _run(self, video_path: str) -> dict:
        """Analyze a video file."""
        try:
            metadata = self.extract_metadata(video_path)
            summary = self.generate_summary(video_path)
            
            return {
                'status': 'success',
                'metadata': metadata,
                'summary': summary
            }
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def extract_metadata(self, video_path: str) -> dict:
        """Extract metadata from a video file."""
        try:
            clip = VideoFileClip(video_path)
            metadata = {
                'duration': clip.duration,
                'resolution': clip.size,
                'fps': clip.fps
            }
            clip.close()
            return metadata
        except Exception as e:
            return {'error': str(e)}

    def generate_summary(self, video_path: str, num_frames: int = 5) -> dict:
        """Generate a summary of a video by extracting keyframes."""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return {'error': 'Could not open video file.'}

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            frame_indices = [int(i) for i in range(0, total_frames, total_frames // num_frames)]
            
            summary_path = PROCESSING_DIR / "Summaries" / os.path.basename(video_path)
            os.makedirs(summary_path, exist_ok=True)
            
            saved_frames = []
            for i, frame_index in enumerate(frame_indices):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
                ret, frame = cap.read()
                if ret:
                    frame_path = os.path.join(summary_path, f"frame_{i}.jpg")
                    cv2.imwrite(frame_path, frame)
                    saved_frames.append(frame_path)
            
            cap.release()
            
            return {
                'summary_path': summary_path,
                'saved_frames': saved_frames
            }
        except Exception as e:
            return {'error': str(e)}

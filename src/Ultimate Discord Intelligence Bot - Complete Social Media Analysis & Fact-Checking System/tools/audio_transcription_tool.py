from crewai_tools import BaseTool
import whisper
import os

class AudioTranscriptionTool(BaseTool):
    name: str = "Audio Transcription Tool"
    description: str = "Transcribe audio from a video file using Whisper."

    def __init__(self):
        super().__init__()
        self.model = whisper.load_model("base")

    def _run(self, video_path: str) -> dict:
        """Transcribe audio from a video file."""
        try:
            if not os.path.exists(video_path):
                return {'status': 'error', 'error': 'Video file not found.'}

            result = self.model.transcribe(video_path)
            
            return {
                'status': 'success',
                'transcript': result["text"]
            }
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

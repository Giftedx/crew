from crewai_tools import BaseTool
from pyannote.audio import Pipeline
import os

class SpeakerDiarizationTool(BaseTool):
    name: str = "Speaker Diarization Tool"
    description: str = "Identify speakers in an audio file using pyannote.audio."

    def __init__(self):
        super().__init__()
        # You will need to accept the user agreement on the Hugging Face Hub
        # for the pyannote/speaker-diarization-3.1 model.
        # You will also need to provide a Hugging Face access token.
        # This can be done by setting the HUGGING_FACE_HUB_TOKEN environment variable.
        self.pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=os.environ.get("HUGGING_FACE_HUB_TOKEN")
        )

    def _run(self, audio_path: str) -> dict:
        """Identify speakers in an audio file."""
        try:
            if not os.path.exists(audio_path):
                return {'status': 'error', 'error': 'Audio file not found.'}

            diarization = self.pipeline(audio_path)
            
            # The output of the pipeline is a pyannote.core.Annotation object.
            # We can convert it to a more usable format.
            result = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                result.append({
                    'speaker': speaker,
                    'start': turn.start,
                    'end': turn.end
                })
            
            return {
                'status': 'success',
                'diarization': result
            }
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

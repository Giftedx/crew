from crewai_tools import BaseTool
from googleapiclient.discovery import build
import os

class FactCheckingTool(BaseTool):
    name: str = "Fact Checking Tool"
    description: str = "Check the factual accuracy of a claim using the Google Fact Check Tools API."

    def __init__(self):
        super().__init__()
        # You will need to create an API key from the Google Cloud Console
        # and set it as an environment variable.
        self.api_key = os.environ.get("GOOGLE_API_KEY")
        self.service = build("factchecktools", "v1alpha1", developerKey=self.api_key)

    def _run(self, query: str) -> dict:
        """Check the factual accuracy of a claim."""
        try:
            request = self.service.claims().search(query=query)
            response = request.execute()
            
            return {
                'status': 'success',
                'response': response
            }
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

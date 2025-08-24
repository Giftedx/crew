import requests
import json
from pathlib import Path
from crewai_tools import BaseTool
from datetime import datetime

class DiscordManagementTool(BaseTool):
    name: str = "Discord Management Tool"
    description: str = "Manage Discord channels, threads, and messages."
    
    def __init__(self, webhook_url: str, bot_token: str):
        super().__init__()
        self.webhook_url = webhook_url
        self.bot_token = bot_token
        self.headers = {
            "Authorization": f"Bot {self.bot_token}",
            "Content-Type": "application/json"
        }

    def _run(self, **kwargs) -> dict:
        """Run a specified Discord management task."""
        task = kwargs.get("task")
        if not task:
            return {"status": "error", "error": "No task specified."}

        if task == "post_message":
            return self.post_message(kwargs.get("channel_id"), kwargs.get("content"), kwargs.get("embed"))
        elif task == "create_thread":
            return self.create_thread(kwargs.get("channel_id"), kwargs.get("name"), kwargs.get("message"))
        elif task == "search_threads":
            return self.search_threads(kwargs.get("channel_id"), kwargs.get("query"))
        else:
            return {"status": "error", "error": f"Unknown task: {task}"}

    def post_message(self, channel_id: str, content: str = None, embed: dict = None) -> dict:
        """Post a message to a Discord channel."""
        payload = {}
        if content:
            payload["content"] = content
        if embed:
            payload["embeds"] = [embed]

        try:
            response = requests.post(f"https://discord.com/api/v10/channels/{channel_id}/messages", headers=self.headers, json=payload)
            return self._handle_response(response)
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def create_thread(self, channel_id: str, name: str, message: str) -> dict:
        """Create a new thread in a Discord channel."""
        payload = {
            "name": name,
            "auto_archive_duration": 1440 # 1 day
        }
        try:
            # First, post a message to start the thread from
            message_response = self.post_message(channel_id, content=message)
            if message_response["status"] != "success":
                return message_response
            
            message_id = message_response["data"]["id"]
            response = requests.post(f"https://discord.com/api/v10/channels/{channel_id}/messages/{message_id}/threads", headers=self.headers, json=payload)
            return self._handle_response(response)
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def search_threads(self, channel_id: str, query: str) -> dict:
        """Search for threads in a Discord channel."""
        try:
            # This is a simplified search. A more robust implementation would use a search index.
            response = requests.get(f"https://discord.com/api/v10/channels/{channel_id}/threads/archived/public", headers=self.headers)
            if response.status_code == 200:
                threads = response.json()["threads"]
                results = [thread for thread in threads if query.lower() in thread["name"].lower()]
                return {"status": "success", "results": results}
            else:
                return self._handle_response(response)
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def _handle_response(self, response) -> dict:
        """Handle Discord API response."""
        if 200 <= response.status_code < 300:
            return {'status': 'success', 'data': response.json()}
        else:
            return {
                'status': 'error',
                'status_code': response.status_code,
                'error': response.text
            }

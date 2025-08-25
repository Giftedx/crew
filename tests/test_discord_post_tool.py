import json
from pathlib import Path
from unittest.mock import MagicMock

import requests

from ultimate_discord_intelligence_bot___complete_social_media_analysis_fact_checking_system.tools.discord_post_tool import (
    DiscordPostTool,
)


def test_embed_post(monkeypatch):
    captured = {}

    def fake_post(url, json=None, headers=None, files=None):
        captured['json'] = json
        response = MagicMock()
        response.status_code = 204
        return response

    monkeypatch.setattr(requests, 'post', fake_post)

    tool = DiscordPostTool('http://example.com/webhook')
    data = {
        'title': 'Video',
        'uploader': 'Author',
        'duration': '10',
        'file_size': str(200 * 1024 * 1024),  # >100MB triggers embed posting
        'platform': 'YouTube',
    }
    result = tool.run(data, {})
    assert result['status'] == 'success'
    assert captured['json']['embeds'][0]['title'] == 'Video'


def test_file_upload(monkeypatch, tmp_path):
    payload = {}

    def fake_post(url, files=None, json=None, headers=None):
        payload['files'] = files
        response = MagicMock()
        response.status_code = 204
        return response

    monkeypatch.setattr(requests, 'post', fake_post)

    file_path = tmp_path / 'video.mp4'
    file_path.write_bytes(b'test')

    tool = DiscordPostTool('http://example.com/webhook')
    data = {
        'title': 'Video',
        'uploader': 'Author',
        'duration': '10',
        'file_size': str(50 * 1024 * 1024),  # <100MB triggers upload
        'local_path': str(file_path),
        'platform': 'YouTube',
    }
    result = tool.run(data, {})
    assert result['status'] == 'success'
    # ensure file handle closed after request
    assert payload['files']['file'][1].closed

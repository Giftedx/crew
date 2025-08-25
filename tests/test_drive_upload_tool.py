from unittest.mock import MagicMock

from ultimate_discord_intelligence_bot___complete_social_media_analysis_fact_checking_system.tools.drive_upload_tool import DriveUploadTool


def test_drive_folder_reuse(monkeypatch):
    service = MagicMock()
    files_mock = MagicMock()
    service.files.return_value = files_mock
    files_mock.list.return_value.execute.side_effect = [
        {'files': [{'id': 'base'}]},
        {'files': [{'id': 'yt'}]},
        {'files': [{'id': 'ig'}]},
        {'files': [{'id': 'proc'}]},
    ]
    files_mock.create.return_value.execute.return_value = {'id': 'new'}

    monkeypatch.setattr(DriveUploadTool, '_setup_service', lambda self: service)

    tool = DriveUploadTool()

    assert tool.base_folder_id == 'base'
    assert tool.subfolders == {'youtube': 'yt', 'instagram': 'ig', 'processed': 'proc'}
    files_mock.create.assert_not_called()

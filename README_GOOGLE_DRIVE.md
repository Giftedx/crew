Google Drive upload setup (service account)

This project uses a Google service account for Drive uploads (server-to-server). OAuth client JSON for "installed" apps will NOT work.

What you need

- A Google Cloud project
- A Service Account with Drive access
- A JSON key (service account credentials)
- Optionally: a folder you control if you want to share links or organize uploads

Steps

1. Create service account
   - Console: IAM & Admin → Service Accounts → Create
   - Name: drive-uploader
   - Grant roles: at least "Drive File Creator" (or use Google Drive API with appropriate scopes)
   - Create key → JSON → download

1. Enable Drive API
   - Console: APIs & Services → Library → Google Drive API → Enable

1. (Optional) Share a folder you own with the service account
   - Open the target folder in Drive
   - Share with the service account email: `drive-uploader@your-gcp-project-id.iam.gserviceaccount.com`
   - Give Editor access

1. Place credentials
   - Save the downloaded JSON as:
     - Default: `crew_data/Config/google-credentials.json` (no env changes needed)
     - Or set `GOOGLE_CREDENTIALS=/absolute/path/to/google-credentials.json` in `.env`

1. Environment
   - Ensure `DISABLE_GOOGLE_DRIVE` is NOT set (or set to `0`/`false`)
   - Optional: set `GOOGLE_CREDENTIALS` if using a non-default path

Verify

- Run a pipeline that includes Drive upload. Logs should show folder creation under `CrewAI_Content` and a successful upload.
- If you see "Google Drive not configured (no credentials provided)", your JSON path is missing or unreadable.
- If you see credential errors, ensure the JSON is `service_account` type and that the key is valid.

Important note about where files go

- By default, uploads are created in the service account's own Drive under a folder named `CrewAI_Content` with subfolders (`YouTube_Videos`, etc.). Files are made publicly readable by link so you can share/view them without logging in.
- If you need files to live under your personal Drive UI, you must extend the tool to use a specific parent folder ID you share with the service account. The current default does not target a user-owned folder.

Security

- Treat JSON keys as secrets. Do not commit them. A sample is included at: `crew_data/Config/google-credentials.sample.json`
- If rotating keys, update the JSON file path and restart the process.

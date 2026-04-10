# Google Contacts Birthday Mirror

This repo contains an n8n workflow that mirrors Google Contacts birthdays into the dedicated Google Calendar listed in `infos.md`.

## Files

- `workflows/google-contacts-birthday-mirror.json`: importable workflow for n8n `2.11.3`
- `scripts/mint_google_refresh_token.py`: local helper to mint a Google refresh token for the installed-app OAuth client in the repo root

## Google OAuth Scopes

- `https://www.googleapis.com/auth/contacts.readonly`
- `https://www.googleapis.com/auth/calendar`

## Local Refresh Token Minting

Run:

```bash
python3 scripts/mint_google_refresh_token.py
```

Open the printed Google consent URL in a browser on the same machine. After Google redirects to `http://localhost:8765/`, the script prints the token payload. Use the `refresh_token` value for the n8n credential import.

## Server Deployment

Copy the workflow JSON to the server and import it into the running container:

```bash
scp -i ~/.ssh/ssh-key-2023-09-20.key workflows/google-contacts-birthday-mirror.json ubuntu@89.168.90.195:/tmp/
ssh -i ~/.ssh/ssh-key-2023-09-20.key ubuntu@89.168.90.195
sudo docker cp /tmp/google-contacts-birthday-mirror.json n8n-n8n-1:/tmp/google-contacts-birthday-mirror.json
sudo docker exec n8n-n8n-1 n8n import:workflow --input=/tmp/google-contacts-birthday-mirror.json --projectId=9QwdGVmKWAneiZU0
```

Import the OAuth2 credential the same way with a JSON payload matching n8n's `oAuth2Api` credential format, then restart n8n if you want to force trigger re-registration:

```bash
sudo docker restart n8n-n8n-1
```

## Workflow Behavior

- Fetches Google Contacts birthdays with pagination from the People API
- Generates all-day birthday events for the current year and next year
- Uses private extended properties to track managed events
- Creates missing events, updates changed events, and deletes stale managed events
- Runs daily at `02:15` in `Europe/Berlin`

## Manual Verification

Run the workflow once after import:

```bash
sudo docker exec n8n-n8n-1 n8n execute --id=googleContactsBirthdayMirror01
```

Then verify the dedicated Google Calendar contains the expected generated birthday events.

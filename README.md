# n8n Workflows

This repo stores importable n8n workflows plus small helper scripts used to provision credentials and deploy to the server.

## Repository Layout

- `workflows/google-contacts-birthday-mirror/workflow.json`: importable workflow for the Google Contacts birthday sync
- `workflows/google-contacts-birthday-mirror/scripts/mint_google_refresh_token.py`: local helper for the birthday sync Google OAuth flow
- `workflows/google-contacts-birthday-mirror/client_secret_*.json`: Google installed-app OAuth client secret for the birthday sync helper
- `workflows/gmail-inbox-cleanup/workflow.json`: importable workflow for the Gmail inbox cleanup flow

## Workflow Catalog

### Google Contacts Birthday Mirror

- Workflow ID: `googleContactsBirthdayMirror01`
- File: `workflows/google-contacts-birthday-mirror/workflow.json`
- Purpose: mirror Google Contacts birthdays into the dedicated Google Calendar listed in `infos.md`
- Trigger: daily at `02:15` in `Europe/Berlin`
- Behavior:
  - fetches Google Contacts birthdays with pagination from the People API
  - generates birthday events for the current year and next year at `10:00` in `Europe/Berlin`
  - uses private extended properties to track managed events
  - creates missing events, updates changed events, and deletes stale managed events
  - sets a popup reminder at event start so the notification lands at `10:00` on the birthday
- Credential requirements:
  - `oAuth2Api`
  - Google OAuth scopes:
    - `https://www.googleapis.com/auth/contacts.readonly`
    - `https://www.googleapis.com/auth/calendar`
  - local helper assets:
    - `workflows/google-contacts-birthday-mirror/scripts/mint_google_refresh_token.py`
    - `workflows/google-contacts-birthday-mirror/client_secret_*.json`

### Gmail Inbox Cleanup Live

- Workflow ID: `gmailInboxCleanupLive01`
- File: `workflows/gmail-inbox-cleanup/workflow.json`
- Purpose: archive matching Gmail messages by removing the `INBOX` label after listing inbox messages that match the workflow query
- Trigger: daily at `03:00`
- Behavior:
  - queries Gmail for `in:inbox is:read older_than:1m has:userlabels`
  - summarizes the matched message set
  - removes the `INBOX` label from each matched message
- Credential requirements:
  - `gmailOAuth2`

## n8n UI Access Over SSH Tunnel

The server-side n8n container is bound to `localhost:5678`, so the easiest way to open the website locally is an SSH tunnel:

```bash
ssh -i ~/.ssh/ssh-key-2023-09-20.key -L 5678:localhost:5678 ubuntu@89.168.90.195
```

Then open:

```text
http://localhost:5678
```

Keep the SSH session open while you use the n8n UI.

## Local Google Refresh Token Minting

Run:

```bash
python3 workflows/google-contacts-birthday-mirror/scripts/mint_google_refresh_token.py
```

Open the printed Google consent URL in a browser on the same machine. After Google redirects to `http://localhost:8765/`, the script prints the token payload. Use the `refresh_token` value for the n8n credential import.

## Server Deployment

The current server target is:

- Host: `ubuntu@89.168.90.195`
- Container: `n8n-n8n-1`
- Project ID: `9QwdGVmKWAneiZU0`

### Import Google Contacts Birthday Mirror

```bash
scp -i ~/.ssh/ssh-key-2023-09-20.key workflows/google-contacts-birthday-mirror/workflow.json ubuntu@89.168.90.195:/tmp/google-contacts-birthday-mirror.json
ssh -i ~/.ssh/ssh-key-2023-09-20.key ubuntu@89.168.90.195
sudo docker cp /tmp/google-contacts-birthday-mirror.json n8n-n8n-1:/tmp/google-contacts-birthday-mirror.json
sudo docker exec n8n-n8n-1 n8n import:workflow --input=/tmp/google-contacts-birthday-mirror.json --projectId=9QwdGVmKWAneiZU0
```

### Import Gmail Inbox Cleanup Live

```bash
scp -i ~/.ssh/ssh-key-2023-09-20.key workflows/gmail-inbox-cleanup/workflow.json ubuntu@89.168.90.195:/tmp/gmail-inbox-cleanup.json
ssh -i ~/.ssh/ssh-key-2023-09-20.key ubuntu@89.168.90.195
sudo docker cp /tmp/gmail-inbox-cleanup.json n8n-n8n-1:/tmp/gmail-inbox-cleanup.json
sudo docker exec n8n-n8n-1 n8n import:workflow --input=/tmp/gmail-inbox-cleanup.json --projectId=9QwdGVmKWAneiZU0
```

Import credentials the same way with JSON payloads matching n8n's credential formats. Restart n8n if you want to force trigger re-registration:

```bash
sudo docker restart n8n-n8n-1
```

## Manual Verification

Run the birthday mirror workflow once after import:

```bash
sudo docker exec n8n-n8n-1 n8n execute --id=googleContactsBirthdayMirror01
```

Then verify the dedicated Google Calendar contains the expected generated birthday events.

Run the Gmail cleanup workflow once after import:

```bash
sudo docker exec n8n-n8n-1 n8n execute --id=gmailInboxCleanupLive01
```

Then verify matching Gmail messages were archived as expected.

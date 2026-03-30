# zemi-reminder

This repository contains a lightweight reminder sender targeting a LINE group.

Files added:

- `scripts/send_reminder.py`: Python script to POST to LINE Notify (supports `--dry-run` and retries)
- `.github/workflows/reminder.yml`: GitHub Actions workflow that runs on schedule and can be manually dispatched
- `requirements.txt`: Python dependency list (`requests`)

Quick start

1. In the repository, add a secret named `LINE_NOTIFY_TOKEN` (Settings → Secrets & variables → Actions). This token can be created via LINE Notify and added to the target group.
2. Optional: add `REMINDER_MESSAGE` secret to override the default message. Otherwise edit the script or pass message via workflow secrets.
3. Test locally:

```bash
python scripts/send_reminder.py --dry-run
```

4. To run the actual send locally (not recommended for production), export the token then run:

```bash
export LINE_NOTIFY_TOKEN="YOUR_TOKEN"
python scripts/send_reminder.py
```

GitHub Actions

- The workflow triggers on schedule (Monday & Thursday 09:00 JST -> specified as UTC cron) and via `workflow_dispatch` for manual testing.
- Ensure `LINE_NOTIFY_TOKEN` is set in repository secrets.

Security

- Never commit tokens into the repository. Use GitHub Secrets as described above.

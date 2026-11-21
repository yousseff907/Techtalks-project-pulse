# Security policy

## Supported versions

Only the latest code on the `main` branch receives security fixes.

## Reporting a vulnerability

Report security problems privately through GitHub, so the details stay hidden until a fix is out:

1. Go to the [Security tab](https://github.com/yousseff907/Techtalks-project-pulse/security) of this repository.
2. Click **Report a vulnerability**.
3. Describe the problem, the steps to reproduce it, and what an attacker could do with it.

Please give us a chance to release a fix before you disclose the problem publicly.

## How the app handles sensitive data

- Users log in with one-time codes sent by email, so the app stores no passwords.
- Sessions use signed JWTs (`JWT_SECRET`).
- The backend encrypts Jira and Notion API keys with Fernet (`ENCRYPTION_KEY`) before saving them to the database.
- The app reads secrets from `.env`, which `.gitignore` keeps out of the repository. Never commit it.

If you run your own instance, generate your own `JWT_SECRET` and `ENCRYPTION_KEY`.

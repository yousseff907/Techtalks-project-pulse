# Contributing to Project Pulse

## Setup

Follow [Getting started](README.md#getting-started) in the README to run the stack with Docker. Copy `.env.example` to `.env` and fill in the secrets and API keys before you start it.

## Branches

Create a branch off `main` for each change. Name it after the part of the app you are changing, followed by a short description:

```
Frontend/All-Tasks-Page
API-Endpoint/Workspace-Summary
DB-Model/Workspace-Data
Auth-Endpoint/Verify-Code
```

## Before you open a pull request

CI runs Ruff and Pytest on every pull request into `main`. Run them locally first:

```bash
pip install -r backend/requirements.txt
ruff check .
pytest backend/tests/
```

The tests need a Postgres at `localhost:5432` with user `testuser`, password `testpass` and database `testdb`. The quickest way to get one:

```bash
docker run --rm -d --name pulse-test-db -p 5432:5432 \
  -e POSTGRES_USER=testuser -e POSTGRES_PASSWORD=testpass -e POSTGRES_DB=testdb postgres:17
```

For frontend changes, also run the linter:

```bash
cd frontend
npm install
npm run lint
```

Add or update tests in `backend/tests/` when you change backend behavior.

## Pull requests

Open the pull request against `main` and describe what changed and how you tested it. Include a screenshot for UI changes, and ask another team member to review it. The branch can only be merged once CI passes.

Keep each pull request to one feature or fix. Never commit `.env` or real API keys.

## Reporting bugs

Open a GitHub issue with the steps to reproduce, what you expected, and what happened instead. For security problems, follow [SECURITY.md](SECURITY.md) instead.

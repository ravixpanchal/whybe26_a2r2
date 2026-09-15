# Setup Guide

## Prerequisites

- Python 3.12+
- Node.js 20+
- npm

## Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

## Environment

Create a local `.env` file from `.env.example` and fill in the required values before running the app.
The default configuration loads the validated portable ML bundle and keeps
artifact loading required. Do not disable `ARTIFACT_LOADING_REQUIRED` in
production.

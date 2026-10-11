# Studychat

A ChatGPT-style AI tutor web application designed for students, powered by **Google Gemini API** and built with **Flask** and **SQLite**.

---

## Features

- **Student Accounts:** Sign up and log in securely with email & password (hashed via Werkzeug).
- **Personalized Profile:** Fill in student details (grade, school, interests, learning goals) which are dynamically injected into Gemini's system instructions to tailor every explanation.
- **Multiple Conversations:** Create, open, rename, and delete chat threads with a persistent sidebar history.
- **Google Gemini Integration:** Uses Google's official GenAI SDK (`google-genai`) with models like `gemini-2.5-flash` or `gemini-1.5-flash`.
- **Socratic Tutoring:** Custom system prompt designed to guide and teach conceptually rather than just dumping answers.
- **Email Chat Transcripts:** Optional SMTP integration to email entire conversation transcripts directly to the student's registered email address.
- **Clean Single-File Frontend:** Fast and responsive dark-mode UI with no heavy node build steps required.

---

## Quickstart

### 1. Install Dependencies

Ensure Python 3.10+ is installed:

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root (or copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env` and set your **Google Gemini API key**:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

> **Where to get a key:** You can get a free Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey).

### 3. Run the Application

```bash
python app.py
```

Open your browser and navigate to:
**[http://localhost:5000](http://localhost:5000)**

---

## Configuration Reference

| Variable | Default | Description |
|---|---|---|
| `GEMINI_API_KEY` | *(None)* | Your Google Gemini API Key |
| `GOOGLE_API_KEY` | *(None)* | Fallback environment variable for Gemini API Key |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model name (e.g., `gemini-2.5-flash`, `gemini-1.5-flash`, `gemini-1.5-pro`) |
| `FLASK_SECRET_KEY` | Random hex | Secret key for Flask sessions |
| `FLASK_DEBUG` | `0` | Enable Flask debug mode (`1` or `0`) |
| `PORT` | `5000` | Port to run the server on |
| `DB_PATH` | `studymate.db` | Path to SQLite database file |
| `MAX_CONTEXT_MESSAGES` | `30` | Maximum message history sent to Gemini per turn |
| `SMTP_HOST` | *(None)* | SMTP host for transcript emails (e.g. `smtp.gmail.com`) |
| `SMTP_PORT` | `587` | SMTP port |
| `SMTP_USER` | *(None)* | SMTP username / email address |
| `SMTP_PASSWORD` | *(None)* | SMTP password or App Password |
| `SMTP_FROM` | *(None)* | Sender address in outbound emails |

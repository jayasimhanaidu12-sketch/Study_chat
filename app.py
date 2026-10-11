"""
StudyMate AI - a ChatGPT-style AI tutor for students.

Features
- Email/password accounts for students
- Editable student profile (name, school, grade, interests, learning goal)
  that personalises the AI tutor's answers
- Multiple chats with a sidebar chat history (create, open, delete)
- Answers any question via Google Gemini API, tuned for learning
- Emails the full transcript of any chat to the student's registered address

Run:  python app.py   then open http://localhost:5000
"""
import os
import json
import re
import secrets
import smtplib
import sqlite3
from datetime import datetime, timezone
from email.message import EmailMessage
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, Response, g, jsonify, request, session, stream_with_context
from google import genai
from google.genai import errors, types
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()

APP_NAME = os.getenv("APP_NAME", "Studychat")
DB_PATH = os.getenv("DB_PATH", "studymate.db")
MODEL = os.getenv("GEMINI_MODEL") or os.getenv("MODEL", "gemini-3.8-flash")
MAX_CONTEXT_MESSAGES = int(os.getenv("MAX_CONTEXT_MESSAGES", "30"))
MAX_MESSAGE_CHARS = 8000

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY") or secrets.token_hex(32)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PROFILE_LIMITS = {
    "full_name": 80,
    "school": 120,
    "grade": 40,
    "interests": 300,
    "learning_goal": 300,
}

_llm = None
_cached_key = None


def llm():
    """Create the Google GenAI client lazily and re-initialize if API key changes."""
    global _llm, _cached_key
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY (or GOOGLE_API_KEY) is not set in the environment.")
    if _llm is None or _cached_key != api_key:
        _llm = genai.Client(api_key=api_key)
        _cached_key = api_key
    return _llm


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------- database
SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name     TEXT NOT NULL DEFAULT '',
    school        TEXT NOT NULL DEFAULT '',
    grade         TEXT NOT NULL DEFAULT '',
    interests     TEXT NOT NULL DEFAULT '',
    learning_goal TEXT NOT NULL DEFAULT '',
    created_at    TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS chats (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title      TEXT NOT NULL DEFAULT 'New chat',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS messages (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id    INTEGER NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
    role       TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content    TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_chats_user ON chats(user_id, updated_at);
CREATE INDEX IF NOT EXISTS idx_messages_chat ON messages(chat_id, id);
"""


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(SCHEMA)


def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def _close_db(_exc):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


# ---------------------------------------------------------------- helpers
def error(message, code=400):
    return jsonify(error=message), code


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "uid" not in session:
            return error("Please log in.", 401)
        return view(*args, **kwargs)
    return wrapper


def current_user():
    return db().execute("SELECT * FROM users WHERE id = ?", (session["uid"],)).fetchone()


def get_owned_chat(chat_id):
    """Return the chat only if it belongs to the logged-in student."""
    return db().execute(
        "SELECT * FROM chats WHERE id = ? AND user_id = ?", (chat_id, session["uid"])
    ).fetchone()


def user_dict(row):
    return {k: row[k] for k in ("id", "email", "full_name", "school", "grade", "interests", "learning_goal")}


def make_title(text):
    return " ".join(text.split())[:50] or "New chat"


def build_system_prompt(user):
    labels = [
        ("full_name", "Name"),
        ("school", "School / college"),
        ("grade", "Grade / year / level"),
        ("interests", "Interests"),
        ("learning_goal", "Learning goal"),
    ]
    profile_lines = [f"- {label}: {user[key]}" for key, label in labels if user[key]]
    profile = "\n".join(profile_lines) or "- (the student has not filled in a profile yet)"

    return f"""You are {APP_NAME}, a friendly, patient AI assistant built for students.

How you help:
- Answer any question the student asks clearly and accurately. If you are not sure, say so rather than guessing.
- Teach, don't just tell. For homework or exam problems, give hints and reasoning first, and show the full solution when the student asks for it or after they have tried.
- Match your explanations to the student's level and goals below. Use examples, analogies and a short check-up question when they help understanding.
- Use Markdown (headings, lists, code blocks) and LaTeX-style math ($...$) when it makes the answer easier to read.
- Keep answers focused. Ask a short clarifying question when a request is ambiguous.
- If a student seems distressed or unsafe, respond with empathy and encourage them to talk to a trusted adult, teacher or counsellor. If there is immediate danger, advise contacting local emergency services.

Student profile:
{profile}"""


def send_email(to_addr, subject, body):
    load_dotenv(override=True)
    host = os.getenv("SMTP_HOST")
    if not host:
        raise RuntimeError("Email is not configured on this server yet.")
    port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = (os.getenv("SMTP_PASSWORD") or "").replace(" ", "").strip()
    sender = os.getenv("SMTP_FROM", smtp_user or "no-reply@localhost")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to_addr
    msg.set_content(body)

    # STARTTLS (port 587). For implicit TLS on port 465, swap to smtplib.SMTP_SSL.
    with smtplib.SMTP(host, port, timeout=20) as smtp:
        smtp.starttls()
        if smtp_user:
            smtp.login(smtp_user, smtp_password)
        smtp.send_message(msg)


# ---------------------------------------------------------------- auth API
@app.post("/api/register")
def register():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email") or "").strip().lower()
    password = str(data.get("password") or "")
    if not EMAIL_RE.match(email):
        return error("Enter a valid email address.")
    if len(password) < 8:
        return error("Password must be at least 8 characters.")

    d = db()
    try:
        d.execute(
            "INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)",
            (email, generate_password_hash(password), now()),
        )
        d.commit()
    except sqlite3.IntegrityError:
        return error("An account with this email already exists.", 409)

    uid = d.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()["id"]
    session.clear()
    session["uid"] = uid
    return jsonify(user=user_dict(current_user())), 201


@app.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email") or "").strip().lower()
    password = str(data.get("password") or "")
    row = db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if row is None or not check_password_hash(row["password_hash"], password):
        return error("Incorrect email or password.", 401)
    session.clear()
    session["uid"] = row["id"]
    return jsonify(user=user_dict(row))


@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify(ok=True)


@app.get("/api/me")
@login_required
def me():
    return jsonify(user=user_dict(current_user()))


@app.put("/api/profile")
@login_required
def update_profile():
    data = request.get_json(silent=True) or {}
    values = {}
    for field, limit in PROFILE_LIMITS.items():
        if field in data:
            value = str(data[field] or "").strip()
            if len(value) > limit:
                return error(f"{field.replace('_', ' ').capitalize()} must be under {limit} characters.")
            values[field] = value

    if values:
        assignments = ", ".join(f"{column} = ?" for column in values)  # keys come from PROFILE_LIMITS only
        d = db()
        d.execute(f"UPDATE users SET {assignments} WHERE id = ?", (*values.values(), session["uid"]))
        d.commit()
    return jsonify(user=user_dict(current_user()))


# ---------------------------------------------------------------- chats API
@app.get("/api/chats")
@login_required
def list_chats():
    rows = db().execute(
        "SELECT id, title, updated_at FROM chats WHERE user_id = ? ORDER BY updated_at DESC",
        (session["uid"],),
    ).fetchall()
    return jsonify(chats=[dict(r) for r in rows])


@app.post("/api/chats")
@login_required
def create_chat():
    ts = now()
    d = db()
    cur = d.execute(
        "INSERT INTO chats (user_id, title, created_at, updated_at) VALUES (?, 'New chat', ?, ?)",
        (session["uid"], ts, ts),
    )
    d.commit()
    return jsonify(id=cur.lastrowid, title="New chat"), 201


@app.get("/api/chats/<int:chat_id>")
@login_required
def get_chat(chat_id):
    chat = get_owned_chat(chat_id)
    if chat is None:
        return error("Chat not found.", 404)
    messages = db().execute(
        "SELECT role, content, created_at FROM messages WHERE chat_id = ? ORDER BY id",
        (chat_id,),
    ).fetchall()
    return jsonify(id=chat["id"], title=chat["title"], messages=[dict(m) for m in messages])


@app.patch("/api/chats/<int:chat_id>")
@login_required
def rename_chat(chat_id):
    if get_owned_chat(chat_id) is None:
        return error("Chat not found.", 404)
    title = " ".join(str((request.get_json(silent=True) or {}).get("title") or "").split())[:100]
    if not title:
        return error("Title cannot be empty.")
    d = db()
    d.execute("UPDATE chats SET title = ? WHERE id = ?", (title, chat_id))
    d.commit()
    return jsonify(id=chat_id, title=title)


@app.delete("/api/chats/<int:chat_id>")
@login_required
def delete_chat(chat_id):
    if get_owned_chat(chat_id) is None:
        return error("Chat not found.", 404)
    d = db()
    d.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
    d.commit()
    return jsonify(ok=True)


@app.post("/api/chats/<int:chat_id>/messages")
@login_required
def send_message(chat_id):
    chat = get_owned_chat(chat_id)
    if chat is None:
        return error("Chat not found.", 404)

    content = str((request.get_json(silent=True) or {}).get("content") or "").strip()
    if not content:
        return error("Message cannot be empty.")
    if len(content) > MAX_MESSAGE_CHARS:
        return error(f"Message is too long (max {MAX_MESSAGE_CHARS} characters).")

    d = db()
    rows = d.execute(
        "SELECT role, content FROM messages WHERE chat_id = ? ORDER BY id DESC LIMIT ?",
        (chat_id, MAX_CONTEXT_MESSAGES),
    ).fetchall()
    history = [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]
    history.append({"role": "user", "content": content})
    while history and history[0]["role"] != "user":  # Gemini conversation starts with user turn
        history.pop(0)

    # Convert conversation history to Gemini types.Content objects
    gemini_contents = []
    for m in history:
        gemini_role = "model" if m["role"] == "assistant" else "user"
        gemini_contents.append(
            types.Content(
                role=gemini_role,
                parts=[types.Part.from_text(text=m["content"])],
            )
        )

    candidate_models = [MODEL]
    if "gemini-3.5-flash-lite" not in candidate_models:
        candidate_models.append("gemini-3.5-flash-lite")
    if "gemini-flash-latest" not in candidate_models:
        candidate_models.append("gemini-flash-latest")

    reply = None
    last_err = None
    for m_name in candidate_models:
        try:
            response = llm().models.generate_content(
                model=m_name,
                contents=gemini_contents,
                config=types.GenerateContentConfig(
                    system_instruction=build_system_prompt(current_user()),
                    max_output_tokens=2000,
                ),
            )
            reply = (response.text or "").strip()
            break
        except RuntimeError as exc:
            app.logger.error("Configuration error: %s", exc)
            return error("AI service is not configured. Please set GEMINI_API_KEY in .env.", 500)
        except Exception as exc:
            app.logger.warning("Model %s failed: %s", m_name, exc)
            last_err = exc

    if reply is None:
        if isinstance(last_err, errors.APIError):
            return error("The AI service is unavailable right now. Please try again.", 502)
        return error("The AI service encountered an error. Please try again.", 502)

    reply = reply or "I'm sorry, I couldn't generate a response. Could you rephrase your question?"

    # Persist only after a successful model call, so failed turns leave no half-saved state.
    ts = now()
    d.execute("INSERT INTO messages (chat_id, role, content, created_at) VALUES (?, 'user', ?, ?)", (chat_id, content, ts))
    d.execute("INSERT INTO messages (chat_id, role, content, created_at) VALUES (?, 'assistant', ?, ?)", (chat_id, reply, ts))
    if chat["title"] == "New chat":
        d.execute("UPDATE chats SET title = ? WHERE id = ?", (make_title(content), chat_id))
    d.execute("UPDATE chats SET updated_at = ? WHERE id = ?", (ts, chat_id))
    d.commit()
    return jsonify(reply=reply)


@app.post("/api/chats/<int:chat_id>/messages/stream")
@login_required
def stream_message(chat_id):
    chat = get_owned_chat(chat_id)
    if chat is None:
        return error("Chat not found.", 404)

    content = str((request.get_json(silent=True) or {}).get("content") or "").strip()
    if not content:
        return error("Message cannot be empty.")
    if len(content) > MAX_MESSAGE_CHARS:
        return error(f"Message is too long (max {MAX_MESSAGE_CHARS} characters).")

    d = db()
    rows = d.execute(
        "SELECT role, content FROM messages WHERE chat_id = ? ORDER BY id DESC LIMIT ?",
        (chat_id, MAX_CONTEXT_MESSAGES),
    ).fetchall()
    history = [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]
    history.append({"role": "user", "content": content})
    while history and history[0]["role"] != "user":
        history.pop(0)

    gemini_contents = []
    for m in history:
        gemini_role = "model" if m["role"] == "assistant" else "user"
        gemini_contents.append(
            types.Content(
                role=gemini_role,
                parts=[types.Part.from_text(text=m["content"])],
            )
        )

    sys_prompt = build_system_prompt(current_user())
    initial_title = chat["title"]

    def generate():
        client = llm()
        candidate_models = [MODEL]
        if "gemini-3.5-flash-lite" not in candidate_models:
            candidate_models.append("gemini-3.5-flash-lite")
        if "gemini-flash-latest" not in candidate_models:
            candidate_models.append("gemini-flash-latest")

        accumulated = []
        for m_name in candidate_models:
            try:
                stream = client.models.generate_content_stream(
                    model=m_name,
                    contents=gemini_contents,
                    config=types.GenerateContentConfig(
                        system_instruction=sys_prompt,
                        max_output_tokens=2000,
                    ),
                )
                for chunk in stream:
                    text = chunk.text or ""
                    if text:
                        accumulated.append(text)
                        yield f"data: {json.dumps({'chunk': text})}\n\n"
                if accumulated:
                    break
            except Exception as e:
                app.logger.warning("Streaming error on %s: %s", m_name, e)
                if accumulated:
                    break

        if not accumulated:
            fallback_msg = "The AI service is experiencing high demand right now. Please try again in a few moments."
            yield f"data: {json.dumps({'chunk': fallback_msg})}\n\n"
            accumulated.append(fallback_msg)

        reply = "".join(accumulated).strip()

        ts = now()
        db_conn = db()
        db_conn.execute(
            "INSERT INTO messages (chat_id, role, content, created_at) VALUES (?, 'user', ?, ?)",
            (chat_id, content, ts),
        )
        db_conn.execute(
            "INSERT INTO messages (chat_id, role, content, created_at) VALUES (?, 'assistant', ?, ?)",
            (chat_id, reply, ts),
        )
        new_title = None
        if initial_title == "New chat":
            new_title = make_title(content)
            db_conn.execute("UPDATE chats SET title = ? WHERE id = ?", (new_title, chat_id))
        db_conn.execute("UPDATE chats SET updated_at = ? WHERE id = ?", (ts, chat_id))
        db_conn.commit()

        yield f"data: {json.dumps({'done': True, 'title': new_title or initial_title})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/chats/<int:chat_id>/email")
@login_required
def email_chat(chat_id):
    chat = get_owned_chat(chat_id)
    if chat is None:
        return error("Chat not found.", 404)

    messages = db().execute(
        "SELECT role, content, created_at FROM messages WHERE chat_id = ? ORDER BY id",
        (chat_id,),
    ).fetchall()
    if not messages:
        return error("This chat has no messages yet.")

    user = current_user()
    lines = [
        f"{APP_NAME} - chat transcript",
        f"Chat: {chat['title']}",
        f"Sent: {now()}",
        "=" * 60,
        "",
    ]
    for m in messages:
        who = "You" if m["role"] == "user" else APP_NAME
        lines += [f"[{m['created_at']}] {who}:", m["content"], ""]

    # Always sent to the logged-in student's own address, never a user-supplied one.
    try:
        send_email(user["email"], f"{APP_NAME}: {chat['title']}", "\n".join(lines))
    except RuntimeError as exc:
        return error(str(exc), 503)
    except (smtplib.SMTPException, OSError):
        app.logger.exception("SMTP send failed")
        return error("Could not send the email. Please try again later.", 502)
    return jsonify(sent_to=user["email"])


# ---------------------------------------------------------------- front end
INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Studychat</title>
<link rel="icon" type="image/png" href="/static/studychat-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
<script src="https://cdn.jsdelivr.net/npm/marked@12.0.2/marked.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
<style>
:root {
  --bg: #050713;
  --side: #080C1B;
  --panel: #0E1428;
  --panel-hover: #141C36;
  --text: #F1F5F9;
  --muted: #8493A8;
  --blue-solid: #1D4ED8;
  --blue-hover: #1E40AF;
  --blue-accent: #2563EB;
  --blue-border: #1E293B;
  --blue-glow: rgba(29, 78, 216, 0.4);
  --border: #162038;
  --danger: #EF4444;
}
* { box-sizing: border-box; }
html, body {
  margin: 0;
  height: 100%;
  background: var(--bg);
  color: var(--text);
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  -webkit-font-smoothing: antialiased;
}
button { font: inherit; cursor: pointer; }
button:disabled { opacity: .5; cursor: not-allowed; }
.hidden { display: none !important; }

/* scrollbars */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-thumb { background: #162038; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #1D4ED8; }

input, textarea {
  width: 100%;
  background: var(--panel);
  border: 1px solid var(--border);
  color: var(--text);
  border-radius: 12px;
  padding: 10px 14px;
  font: inherit;
  outline: none;
  transition: border-color .15s;
}
input:focus, textarea:focus { border-color: var(--blue-accent); }
input:disabled { opacity: .6; }

.btn {
  background: var(--blue-solid);
  color: #fff;
  border: 0;
  border-radius: 10px;
  padding: 9px 15px;
  font-weight: 600;
  font-size: 14px;
  transition: all .15s;
  box-shadow: 0 2px 10px rgba(29, 78, 216, 0.3);
}
.btn:hover:not(:disabled) {
  background: var(--blue-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(29, 78, 216, 0.45);
}
.btn:active:not(:disabled) { transform: translateY(0); }
.btn.block { width: 100%; }
.btn.ghost {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text);
  font-weight: 500;
  box-shadow: none;
}
.btn.ghost:hover:not(:disabled) { background: var(--panel); border-color: #243054; }

.field { margin-bottom: 14px; }
.field label { display: block; font-size: 13px; color: var(--muted); margin-bottom: 6px; }
.error { color: var(--danger); font-size: 13px; min-height: 18px; margin: 8px 0 0; }
.muted { color: var(--muted); font-size: 14px; }
.link { background: none; border: 0; color: var(--blue-accent); padding: 0; font: inherit; cursor: pointer; }
.link:hover { text-decoration: underline; }

/* ---------------- Studychat S-Logo ONLY for AI Thinking Animation ---------------- */
.logo-3d-wrap {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  perspective: 700px;
  user-select: none;
}
.sc-logo {
  display: block;
  transform-style: preserve-3d;
  will-change: transform, filter;
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), filter 0.3s ease;
}

/* 1. Idle: The S logo stays still with a subtle solid blue glow */
.sc-logo.idle {
  filter: drop-shadow(0 0 8px rgba(29, 78, 216, 0.5));
}

/* 2. Thinking: Fast, energetic 3D rotation (0.85s) with vivid blue power glow like ChatGPT */
.sc-logo.thinking {
  animation: rotateY360 0.85s infinite cubic-bezier(0.4, 0, 0.2, 1);
}
@keyframes rotateY360 {
  0% {
    transform: perspective(600px) rotateY(0deg) scale(1);
    filter: drop-shadow(0 0 8px rgba(37, 99, 235, 0.8)) drop-shadow(0 0 16px rgba(59, 130, 246, 0.5));
  }
  50% {
    transform: perspective(600px) rotateY(180deg) scale(1.08);
    filter: drop-shadow(0 0 16px rgba(37, 99, 235, 1)) drop-shadow(0 0 28px rgba(96, 165, 250, 0.8));
  }
  100% {
    transform: perspective(600px) rotateY(360deg) scale(1);
    filter: drop-shadow(0 0 8px rgba(37, 99, 235, 0.8)) drop-shadow(0 0 16px rgba(59, 130, 246, 0.5));
  }
}

/* 3. Responding: Quick smooth settle when answer begins streaming */
.sc-logo.responding {
  transform: perspective(600px) rotateY(360deg) scale(1);
  filter: drop-shadow(0 0 10px rgba(37, 99, 235, 0.6));
}

/* 4. Error: subtle red indicator */
.sc-logo.error {
  filter: drop-shadow(0 0 14px rgba(239, 68, 68, 0.85));
}

@media (prefers-reduced-motion: reduce) {
  .sc-logo.thinking {
    animation: pulseBlueGlow 0.9s infinite ease-in-out;
    transform: none !important;
  }
  @keyframes pulseBlueGlow {
    0%, 100% { opacity: 0.8; filter: drop-shadow(0 0 8px rgba(29, 78, 216, 0.6)); }
    50% { opacity: 1; filter: drop-shadow(0 0 18px rgba(37, 99, 235, 0.9)); }
  }
}

/* auth page */
#auth { min-height: 100%; display: flex; align-items: center; justify-content: center; padding: 20px; }
.auth-card {
  width: 100%;
  max-width: 400px;
  background: var(--side);
  padding: 36px 32px;
  border-radius: 18px;
  border: 1px solid var(--border);
  box-shadow: 0 10px 40px rgba(0,0,0,0.65);
  text-align: center;
}
.auth-card h1 { margin: 0 0 6px; font-size: 28px; font-weight: 800; letter-spacing: -0.5px; }
.auth-card .sub { color: var(--muted); margin: 0 0 24px; font-size: 14px; }
.auth-card .field { text-align: left; }

/* layout */
#app { display: flex; height: 100vh; overflow: hidden; position: relative; }

/* ---------------- Sidebar Navigation (Collapsible) ---------------- */
#sidebar {
  width: 270px;
  background: var(--side);
  display: flex;
  flex-direction: column;
  padding: 14px 12px;
  gap: 10px;
  flex-shrink: 0;
  border-right: 1px solid var(--border);
  transition: width 0.26s cubic-bezier(0.2, 0, 0, 1), padding 0.26s ease, transform 0.26s ease, opacity 0.2s ease;
  overflow: hidden;
  z-index: 10;
}
#sidebar.collapsed {
  width: 0 !important;
  padding-left: 0 !important;
  padding-right: 0 !important;
  opacity: 0;
  pointer-events: none;
  border-right: 0;
}

.side-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 6px 12px;
  border-bottom: 1px solid var(--border);
}
.brand-title {
  font-size: 19px;
  font-weight: 800;
  letter-spacing: -0.4px;
  user-select: none;
}
.brand-white { color: #ffffff; }
.brand-blue { color: var(--blue-accent); }

/* Hide Nav button inside sidebar */
.nav-close-btn {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--muted);
  border-radius: 8px;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s;
}
.nav-close-btn:hover {
  background: var(--panel);
  color: #fff;
  border-color: var(--blue-solid);
}

#chat-list { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 4px; }
.chat-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 9px;
  cursor: pointer;
  font-size: 14px;
  color: #cbd5e1;
  transition: background .15s;
}
.chat-item:hover, .chat-item.active { background: var(--panel); color: #fff; }
.chat-item.active { border-left: 3px solid var(--blue-accent); }
.chat-title { flex: 1; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.chat-del {
  opacity: 0;
  background: none;
  border: 0;
  color: var(--muted);
  padding: 2px 6px;
  border-radius: 6px;
  font-size: 13px;
}
.chat-item:hover .chat-del { opacity: 1; }
.chat-del:hover { color: var(--danger); background: rgba(255,255,255,0.06); }

.side-footer {
  border-top: 1px solid var(--border);
  padding-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.side-footer .who {
  font-size: 13px;
  color: var(--muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding: 0 6px;
}

/* ---------------- Main Content ---------------- */
#main { flex: 1; display: flex; flex-direction: column; min-width: 0; height: 100%; position: relative; }
#topbar {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 0 18px;
  border-bottom: 1px solid var(--border);
  background: var(--bg);
  z-index: 5;
}
#topbar-left { display: flex; align-items: center; gap: 12px; min-width: 0; }
#chat-title { font-size: 15px; font-weight: 600; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; color: #fff; }
#status { font-size: 13px; color: var(--blue-accent); white-space: nowrap; font-weight: 500; }

/* Show/Hide Nav Toggle Button in Topbar */
#toggle-sidebar-btn {
  background: var(--panel);
  border: 1px solid var(--border);
  color: var(--muted);
  border-radius: 8px;
  padding: 6px 10px;
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  flex-shrink: 0;
}
#toggle-sidebar-btn:hover {
  background: var(--panel-hover);
  color: #fff;
  border-color: var(--blue-solid);
}
#toggle-sidebar-btn svg { width: 16px; height: 16px; flex-shrink: 0; }

/* Messages Thread */
#messages { flex: 1; overflow-y: auto; padding: 24px 0 30px; scroll-behavior: smooth; }
.thread { max-width: 820px; margin: 0 auto; padding: 0 24px; }

.msg { display: flex; margin: 24px 0; }
.msg.user { justify-content: flex-end; }
.msg.user .bubble {
  background: var(--panel);
  border: 1px solid #1c2747;
  padding: 13px 18px;
  border-radius: 20px;
  max-width: 82%;
  line-height: 1.6;
  font-size: 15.5px;
  color: #fff;
  white-space: pre-wrap;
  word-break: break-word;
  box-shadow: 0 2px 12px rgba(0,0,0,0.3);
}

/* Assistant Message - Clean without static logo */
.msg.assistant {
  display: flex;
  gap: 14px;
  align-items: flex-start;
}
.ai-badge {
  width: 32px;
  height: 32px;
  border-radius: 9px;
  background: var(--blue-solid);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 3px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.5px;
  box-shadow: 0 2px 8px rgba(29, 78, 216, 0.4);
}
.msg-body { flex: 1; min-width: 0; }

/* ---------------- Studychat Thinking Box (ChatGPT-style Thinking Pill) ---------------- */
.thinking-box {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 8px 16px;
  background: rgba(14, 20, 40, 0.85);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(37, 99, 235, 0.45);
  border-radius: 20px;
  font-size: 13.5px;
  color: #F1F5F9;
  margin-bottom: 12px;
  box-shadow: 0 4px 18px rgba(0, 0, 0, 0.4), 0 0 16px rgba(37, 99, 235, 0.25);
  animation: fadeIn 0.15s ease;
  user-select: none;
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}
.thinking-box.thought-complete {
  background: rgba(15, 23, 42, 0.65);
  border: 1px solid rgba(51, 65, 85, 0.7);
  color: #94a3b8;
  padding: 5px 12px;
  font-size: 12.5px;
  box-shadow: none;
  border-radius: 14px;
}
.thinking-text {
  font-weight: 500;
  letter-spacing: 0.1px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.thinking-timer {
  color: #60A5FA;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  font-weight: 600;
  padding: 1px 6px;
  background: rgba(37, 99, 235, 0.2);
  border-radius: 8px;
}
.thinking-dots {
  display: inline-flex;
  gap: 3px;
  align-items: center;
}
.thinking-dots span {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--blue-accent);
  animation: dotPulse 0.9s infinite ease-in-out both;
}
.thinking-dots span:nth-child(1) { animation-delay: -0.3s; }
.thinking-dots span:nth-child(2) { animation-delay: -0.15s; }
.thinking-dots span:nth-child(3) { animation-delay: 0s; }
@keyframes dotPulse {
  0%, 80%, 100% { transform: scale(0.7); opacity: 0.35; }
  40% { transform: scale(1.3); opacity: 1; background: #93C5FD; box-shadow: 0 0 8px #3B82F6; }
}

/* Streaming Blinking Cursor */
.stream-cursor {
  display: inline-block;
  width: 7px;
  height: 16px;
  background: var(--blue-accent);
  margin-left: 3px;
  vertical-align: -2px;
  border-radius: 1px;
  animation: cursorBlink 0.8s infinite;
}
@keyframes cursorBlink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* Markdown typography */
.markdown-body {
  font-size: 15.5px;
  line-height: 1.7;
  color: var(--text);
  word-break: break-word;
}
.markdown-body p { margin: 0 0 14px 0; }
.markdown-body p:last-child { margin-bottom: 0; }
.markdown-body h1, .markdown-body h2, .markdown-body h3, .markdown-body h4 {
  color: #fff;
  margin: 20px 0 10px;
  font-weight: 700;
  line-height: 1.35;
}
.markdown-body h1 { font-size: 22px; }
.markdown-body h2 { font-size: 19px; }
.markdown-body h3 { font-size: 17px; }
.markdown-body ul, .markdown-body ol { margin: 0 0 14px 0; padding-left: 24px; }
.markdown-body li { margin: 5px 0; }
.markdown-body blockquote {
  margin: 12px 0;
  padding: 6px 14px;
  border-left: 3px solid var(--blue-solid);
  background: rgba(29, 78, 216, 0.08);
  border-radius: 0 8px 8px 0;
  color: #cbd5e1;
}
.markdown-body hr { border: 0; height: 1px; background: var(--border); margin: 18px 0; }
.markdown-body table {
  width: 100%;
  border-collapse: collapse;
  margin: 14px 0;
  font-size: 14px;
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
}
.markdown-body th, .markdown-body td { padding: 9px 12px; border: 1px solid var(--border); text-align: left; }
.markdown-body th { background: #10162B; font-weight: 600; color: #fff; }
.markdown-body tr:nth-child(even) { background: rgba(255,255,255,0.02); }
.markdown-body code:not(pre code) {
  background: rgba(29, 78, 216, 0.15);
  border: 1px solid rgba(29, 78, 216, 0.3);
  color: #93C5FD;
  padding: 2px 6px;
  border-radius: 5px;
  font-family: 'JetBrains Mono', Consolas, monospace;
  font-size: 13.5px;
}

/* ChatGPT Code Block with Header and Copy Button */
.code-block-wrap {
  margin: 16px 0;
  border-radius: 12px;
  background: #080A14;
  border: 1px solid #1c2747;
  overflow: hidden;
  box-shadow: 0 4px 18px rgba(0,0,0,0.35);
}
.code-block-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 14px;
  background: #0f152d;
  border-bottom: 1px solid #1c2747;
  font-size: 12.5px;
  color: #94a3b8;
}
.code-lang-label { font-family: monospace; text-transform: lowercase; font-weight: 600; color: #93C5FD; }
.copy-code-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: transparent;
  border: 0;
  color: #94a3b8;
  font-size: 12px;
  padding: 3px 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}
.copy-code-btn:hover { color: #fff; background: rgba(255, 255, 255, 0.08); }
.copy-code-btn.copied { color: #60A5FA; }
.code-block-wrap pre {
  margin: 0;
  padding: 14px 16px;
  overflow-x: auto;
  font-size: 13.5px;
  line-height: 1.55;
  background: #080A14;
}
.code-block-wrap pre code {
  font-family: 'JetBrains Mono', Consolas, monospace;
  background: transparent;
  padding: 0;
}

/* Assistant Message Actions Toolbar */
.msg-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
  opacity: 0.85;
}
.msg-action-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: transparent;
  border: 1px solid transparent;
  color: #94a3b8;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 12.5px;
  cursor: pointer;
  transition: all 0.15s;
}
.msg-action-btn:hover { color: #fff; background: rgba(255, 255, 255, 0.06); border-color: var(--blue-solid); }
.msg-action-btn.copied { color: #60A5FA; }

/* Welcome Screen - Clean, No Static Logo */
.welcome { text-align: center; margin-top: 10vh; color: var(--muted); padding: 0 16px; }
.welcome h2 { color: #fff; font-weight: 800; font-size: 30px; margin: 0 0 10px; letter-spacing: -0.5px; }
.welcome p { font-size: 15px; margin: 0 0 32px; color: #94a3b8; }
.suggestions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
  max-width: 720px;
  margin: 0 auto;
}
.suggestion-card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 14px 16px;
  text-align: left;
  cursor: pointer;
  font-size: 13.5px;
  color: #cbd5e1;
  transition: all 0.15s;
  box-shadow: 0 2px 10px rgba(0,0,0,0.25);
}
.suggestion-card:hover {
  background: var(--panel-hover);
  border-color: var(--blue-solid);
  color: #fff;
  transform: translateY(-2px);
  box-shadow: 0 4px 18px rgba(29, 78, 216, 0.25);
}

/* ---------------- GLOSSY FINISH on Chat Input Area ---------------- */
#composer-wrap {
  padding: 14px 20px 20px;
  background: var(--bg);
}
#composer {
  max-width: 820px;
  margin: 0 auto;
  display: flex;
  align-items: flex-end;
  gap: 10px;
  background: rgba(14, 20, 40, 0.78);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border-radius: 24px;
  padding: 10px 12px 10px 20px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  box-shadow:
    inset 0 1px 1px 0 rgba(255, 255, 255, 0.22),
    inset 0 -1px 1px 0 rgba(0, 0, 0, 0.35),
    0 8px 32px 0 rgba(0, 0, 0, 0.55),
    0 2px 12px 0 rgba(29, 78, 216, 0.2);
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  position: relative;
}
#composer::before {
  content: '';
  position: absolute;
  top: 0;
  left: 15%;
  right: 15%;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.45), transparent);
  pointer-events: none;
}
#composer:focus-within {
  border-color: var(--blue-accent);
  box-shadow:
    inset 0 1px 1px 0 rgba(255, 255, 255, 0.35),
    0 0 25px rgba(29, 78, 216, 0.45),
    0 10px 36px rgba(0, 0, 0, 0.6);
}
#input {
  background: transparent;
  border: 0;
  resize: none;
  max-height: 200px;
  padding: 6px 0;
  line-height: 1.55;
  min-height: 26px;
  font-size: 15.5px;
  color: #ffffff;
  outline: none;
  text-shadow: 0 1px 2px rgba(0,0,0,0.3);
}
#input::placeholder {
  color: #718096;
}
#send {
  background: var(--blue-solid);
  color: #fff;
  border: 0;
  border-radius: 50%;
  width: 38px;
  height: 38px;
  flex-shrink: 0;
  font-size: 19px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all .18s;
  box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.35), 0 3px 12px rgba(29, 78, 216, 0.45);
}
#send:hover:not(:disabled) {
  background: var(--blue-accent);
  transform: scale(1.05);
  box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.45), 0 5px 18px rgba(37, 99, 235, 0.6);
}
#send.stop-btn {
  background: #ececec;
  color: #171717;
  font-size: 13px;
  box-shadow: none;
}
#send.stop-btn:hover { background: #ff5252; color: #fff; }
.hint { text-align: center; font-size: 12px; color: var(--muted); margin-top: 8px; }

/* Profile modal */
#modal { position: fixed; inset: 0; background: rgba(0,0,0,.75); backdrop-filter: blur(6px); display: flex; align-items: center; justify-content: center; padding: 20px; z-index: 20; }
.modal-card { background: var(--side); border: 1px solid var(--border); border-radius: 18px; padding: 28px; width: 100%; max-width: 480px; max-height: 90vh; overflow-y: auto; box-shadow: 0 10px 40px rgba(0,0,0,0.65); }
.modal-card h2 { margin: 0 0 18px; font-size: 20px; font-weight: 700; }
.modal-actions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 10px; }

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Responsive */
@media (max-width: 720px) {
  #sidebar:not(.collapsed) { position: fixed; left: 0; top: 0; bottom: 0; z-index: 30; box-shadow: 6px 0 25px rgba(0,0,0,.8); }
  #sidebar.collapsed { width: 0 !important; left: -280px !important; opacity: 0 !important; }
  .thread { padding: 0 14px; }
  #composer-wrap { padding: 10px 12px 14px; }
}
</style>
</head>
<body>

<!-- Login / Register Screen - Clean, No Static Logo -->
<div id="auth">
  <div class="auth-card">
    <h1><span class="brand-white">Study</span><span class="brand-blue">chat</span></h1>
    <p class="sub" id="auth-sub">Log in to continue learning.</p>
    <form id="auth-form">
      <div class="field"><label for="auth-email">Email</label><input id="auth-email" type="email" autocomplete="email" required></div>
      <div class="field"><label for="auth-pass">Password</label><input id="auth-pass" type="password" autocomplete="current-password" minlength="8" required></div>
      <button class="btn block" id="auth-submit" type="submit">Log in</button>
      <p class="error" id="auth-error"></p>
    </form>
    <p class="sub" style="margin:16px 0 0;text-align:center">
      <span id="auth-toggle-text">New here?</span>
      <button class="link" id="auth-toggle" type="button">Create an account</button>
    </p>
  </div>
</div>

<!-- Main App Screen -->
<div id="app" class="hidden">
  <!-- Side Navbar (Collapsible) -->
  <aside id="sidebar">
    <div class="side-header">
      <span class="brand-title"><span class="brand-white">Study</span><span class="brand-blue">chat</span></span>
      <!-- Hide nav button inside the sidebar -->
      <button class="nav-close-btn" id="sidebar-close-btn" type="button" title="Hide navigation bar" aria-label="Hide navigation bar">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6L6 18M6 6l12 12"/></svg>
      </button>
    </div>
    <button class="btn ghost" id="new-chat" type="button">+ New chat</button>
    <div id="chat-list"></div>
    <div class="side-footer">
      <div class="who" id="side-user"></div>
      <button class="btn ghost" id="profile-btn" type="button">Edit profile</button>
      <button class="btn ghost" id="logout-btn" type="button">Log out</button>
    </div>
  </aside>

  <main id="main">
    <header id="topbar">
      <div id="topbar-left">
        <!-- Hide/Open Navbar Toggle Button in Topbar -->
        <button id="toggle-sidebar-btn" type="button" title="Toggle navigation bar" aria-label="Toggle navigation bar">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 3v18"/></svg>
          <span id="toggle-nav-text">Hide bar</span>
        </button>
        <div id="chat-title">New chat</div>
      </div>
      <div style="display:flex;align-items:center;gap:12px">
        <span id="status"></span>
        <button class="btn ghost" id="email-btn" type="button">Email transcript</button>
      </div>
    </header>

    <div id="messages"><div class="thread" id="thread"></div></div>

    <!-- Glossy Input Area -->
    <div id="composer-wrap">
      <form id="composer">
        <textarea id="input" rows="1" placeholder="Ask anything..."></textarea>
        <button id="send" type="submit" aria-label="Send" title="Send message">&uarr;</button>
      </form>
      <div class="hint">Studychat can make mistakes. Verify important answers with your teacher or textbook.</div>
    </div>
  </main>
</div>

<div id="modal" class="hidden">
  <div class="modal-card">
    <h2>Your profile</h2>
    <form id="profile-form">
      <div class="field"><label for="p-name">Full name</label><input id="p-name" maxlength="80"></div>
      <div class="field"><label for="p-email">Email (transcripts are sent here)</label><input id="p-email" disabled></div>
      <div class="field"><label for="p-school">School / college</label><input id="p-school" maxlength="120"></div>
      <div class="field"><label for="p-grade">Grade / year / level</label><input id="p-grade" maxlength="40" placeholder="e.g. Class 10, B.Tech 2nd year"></div>
      <div class="field"><label for="p-interests">Interests</label><textarea id="p-interests" rows="2" maxlength="300"></textarea></div>
      <div class="field"><label for="p-goal">Learning goal</label><textarea id="p-goal" rows="2" maxlength="300" placeholder="e.g. Prepare for JEE Maths, learn Python basics"></textarea></div>
      <p class="error" id="profile-error"></p>
      <div class="modal-actions">
        <button type="button" class="btn ghost" id="profile-cancel">Cancel</button>
        <button type="submit" class="btn">Save</button>
      </div>
    </form>
  </div>
</div>

<script>
const $ = (sel) => document.querySelector(sel);
const APP = { user: null, chats: [], chatId: null, busy: false };

// Clean Welcome Screen - No Static Logo
const WELCOME_HTML = `
  <div class="welcome">
    <h2>How can <span class="brand-white">Study</span><span class="brand-blue">chat</span> help you today?</h2>
    <p>Ask a question, paste a problem, or explore concepts step-by-step.</p>
    <div class="suggestions-grid">
      <div class="suggestion-card" onclick="usePrompt('Explain how photosynthesis works in simple terms')">
        <strong>🌿 Photosynthesis</strong><br>Explain in simple terms
      </div>
      <div class="suggestion-card" onclick="usePrompt('Help me solve this quadratic equation: x^2 - 5x + 6 = 0')">
        <strong>📐 Quadratic Equations</strong><br>Step-by-step math solver
      </div>
      <div class="suggestion-card" onclick="usePrompt('Explain the difference between Python lists and tuples with code examples')">
        <strong>💻 Python Data Types</strong><br>Lists vs tuples with examples
      </div>
      <div class="suggestion-card" onclick="usePrompt('Give me a quick quiz of 3 questions on Newton laws of motion')">
        <strong>⚡ Quick Physics Quiz</strong><br>3 questions on Newton laws
      </div>
    </div>
  </div>
`;

function escapeHtml(str) {
  if (!str) return "";
  return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

// ---------- Marked Setup for ChatGPT Markdown rendering
if (window.marked) {
  marked.setOptions({
    gfm: true,
    breaks: true,
  });
  const renderer = new marked.Renderer();
  renderer.code = function(code, language) {
    const lang = (language || "").match(/\\S*/)[0] || "text";
    let highlighted = escapeHtml(code);
    if (window.hljs) {
      if (hljs.getLanguage(lang)) {
        try { highlighted = hljs.highlight(code, { language: lang, ignoreIllegals: true }).value; } catch (_) {}
      } else {
        try { highlighted = hljs.highlightAuto(code).value; } catch (_) {}
      }
    }
    return `<div class="code-block-wrap">
      <div class="code-block-header">
        <span class="code-lang-label">${escapeHtml(lang)}</span>
        <button class="copy-code-btn" type="button" onclick="copyCodeBlock(this)">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
          <span>Copy code</span>
        </button>
      </div>
      <pre><code class="hljs language-${escapeHtml(lang)}">${highlighted}</code></pre>
    </div>`;
  };
  marked.use({ renderer });
}

function renderMarkdown(rawText) {
  if (window.marked) {
    try { return marked.parse(rawText || ""); } catch (_) {}
  }
  return escapeHtml(rawText || "").replace(/\\n/g, "<br>");
}

function renderMath(container) {
  if (!window.katex || !container) return;
  const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT);
  const textNodes = [];
  while (walker.nextNode()) textNodes.push(walker.currentNode);
  for (const node of textNodes) {
    if (node.parentElement && (node.parentElement.tagName === "CODE" || node.parentElement.tagName === "PRE")) continue;
    const val = node.nodeValue;
    if (val && val.includes("$")) {
      const parent = node.parentNode;
      const span = document.createElement("span");
      let html = escapeHtml(val);
      // Display math $$...$$
      html = html.replace(/\\$\\$([\\s\\S]+?)\\$\\$/g, (_, eq) => {
        try { return katex.renderToString(eq, { displayMode: true, throwOnError: false }); } catch (_) { return `$$${eq}$$`; }
      });
      // Inline math $...$
      html = html.replace(/\\$([^\\$\\n]+?)\\$/g, (_, eq) => {
        try { return katex.renderToString(eq, { displayMode: false, throwOnError: false }); } catch (_) { return `$${eq}$`; }
      });
      span.innerHTML = html;
      parent.replaceChild(span, node);
    }
  }
}

function copyCodeBlock(btn) {
  const block = btn.closest(".code-block-wrap");
  const code = block.querySelector("pre code");
  if (!code) return;
  navigator.clipboard.writeText(code.innerText || code.textContent).then(() => {
    const span = btn.querySelector("span");
    const orig = span.textContent;
    btn.classList.add("copied");
    span.textContent = "Copied!";
    setTimeout(() => {
      span.textContent = orig;
      btn.classList.remove("copied");
    }, 2000);
  });
}

function copyFullMessage(btn) {
  const text = btn.dataset.content || btn.closest(".msg-body").querySelector(".markdown-body").innerText;
  navigator.clipboard.writeText(text).then(() => {
    const span = btn.querySelector("span");
    span.textContent = "Copied!";
    btn.classList.add("copied");
    setTimeout(() => {
      span.textContent = "Copy";
      btn.classList.remove("copied");
    }, 2000);
  });
}

async function api(path, method = "GET", body) {
  const res = await fetch(path, {
    method,
    credentials: "same-origin",
    headers: body !== undefined ? { "Content-Type": "application/json" } : {},
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  let data = {};
  try { data = await res.json(); } catch (_) {}
  if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`);
  return data;
}

function flash(message) {
  $("#status").textContent = message;
  clearTimeout(flash.timer);
  flash.timer = setTimeout(() => { $("#status").textContent = ""; }, 6000);
}

function scrollBottom() {
  const box = $("#messages");
  box.scrollTop = box.scrollHeight;
}

function appendUserMessage(text) {
  const thread = $("#thread");
  const row = document.createElement("div");
  row.className = "msg user";
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  row.appendChild(bubble);
  thread.appendChild(row);
  scrollBottom();
  return row;
}

// Creates assistant message: ChatGPT-style fast thinking indicator & 60fps streaming
function createAssistantMessage() {
  const thread = $("#thread");
  const row = document.createElement("div");
  row.className = "msg assistant";

  const startTime = Date.now();
  let timerInterval = null;

  row.innerHTML = `
    <div class="ai-badge" title="Studychat AI">SC</div>
    <div class="msg-body">
      <!-- Studychat Thinking Box: Fast 3D spin + live stopwatch timer like ChatGPT -->
      <div class="thinking-box">
        <div class="logo-3d-wrap" style="width: 22px; height: 22px;">
          <img src="/static/studychat-icon.png" class="sc-logo thinking thinking-logo" style="width: 22px; height: 22px; object-fit: contain;" alt="Studychat thinking">
        </div>
        <span class="thinking-text">Thinking <span class="thinking-timer">0.0s</span></span>
        <div class="thinking-dots">
          <span></span><span></span><span></span>
        </div>
      </div>
      <div class="markdown-body hidden"></div>
      <span class="stream-cursor hidden"></span>
      <div class="msg-actions hidden">
        <button class="msg-action-btn" type="button" onclick="copyFullMessage(this)">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
          <span>Copy</span>
        </button>
      </div>
    </div>
  `;

  thread.appendChild(row);
  scrollBottom();

  const thinkingBox = row.querySelector(".thinking-box");
  const timerSpan = row.querySelector(".thinking-timer");
  const markdownBody = row.querySelector(".markdown-body");
  const cursor = row.querySelector(".stream-cursor");
  const actions = row.querySelector(".msg-actions");

  timerInterval = setInterval(() => {
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
    if (timerSpan) timerSpan.textContent = elapsed + "s";
  }, 100);

  let targetText = "";
  let renderedText = "";
  let rafId = null;
  let mathScheduled = false;

  function scheduleRender() {
    if (rafId) return;
    rafId = requestAnimationFrame(() => {
      rafId = null;
      if (renderedText !== targetText) {
        renderedText = targetText;
        markdownBody.innerHTML = renderMarkdown(renderedText);
        markdownBody.appendChild(cursor);
        scrollBottom();

        // Debounce math rendering so stream never stutters or drops frames
        if (renderedText.includes("$") && !mathScheduled) {
          mathScheduled = true;
          setTimeout(() => {
            mathScheduled = false;
            renderMath(markdownBody);
          }, 180);
        }
      }
    });
  }

  return {
    startStreaming() {
      if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
      }
      const totalSec = Math.max(0.1, ((Date.now() - startTime) / 1000)).toFixed(1);
      if (thinkingBox) {
        thinkingBox.className = "thinking-box thought-complete";
        thinkingBox.innerHTML = `
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color:#60A5FA;">
            <circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline>
          </svg>
          <span>Thought for ${totalSec}s</span>
        `;
      }
      // Instant 0ms unhide - no artificial setTimeout!
      markdownBody.classList.remove("hidden");
      cursor.classList.remove("hidden");
      markdownBody.appendChild(cursor);
    },
    updateContent(text) {
      targetText = text;
      scheduleRender();
    },
    finish(text) {
      if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
      }
      if (rafId) {
        cancelAnimationFrame(rafId);
        rafId = null;
      }
      const finalText = (text || targetText || "").trim() || "I couldn't generate a response. Please ask again.";
      cursor.remove();
      markdownBody.classList.remove("hidden");
      markdownBody.innerHTML = renderMarkdown(finalText);
      renderMath(markdownBody);
      actions.classList.remove("hidden");
      actions.querySelector("button").dataset.content = finalText;
      scrollBottom();
    },
    showError(errMsg) {
      if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
      }
      if (rafId) {
        cancelAnimationFrame(rafId);
        rafId = null;
      }
      if (thinkingBox) thinkingBox.remove();
      cursor.remove();
      markdownBody.classList.remove("hidden");
      markdownBody.innerHTML = `<span style="color:var(--danger)">Error: ${escapeHtml(errMsg)}</span>`;
      scrollBottom();
    }
  };
}

function appendLoadedMessage(role, content) {
  const thread = $("#thread");
  const row = document.createElement("div");
  row.className = `msg ${role}`;
  if (role === "user") {
    row.innerHTML = `<div class="bubble">${escapeHtml(content)}</div>`;
  } else {
    row.innerHTML = `
      <div class="ai-badge" title="Studychat AI">SC</div>
      <div class="msg-body">
        <div class="markdown-body">${renderMarkdown(content)}</div>
        <div class="msg-actions">
          <button class="msg-action-btn" type="button" onclick="copyFullMessage(this)" data-content="${escapeHtml(content)}">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
            <span>Copy</span>
          </button>
        </div>
      </div>
    `;
    renderMath(row.querySelector(".markdown-body"));
  }
  thread.appendChild(row);
}

function showWelcome() {
  APP.chatId = null;
  $("#chat-title").textContent = "New chat";
  $("#thread").innerHTML = WELCOME_HTML;
  renderChatList();
}

function usePrompt(text) {
  input.value = text;
  autoSize();
  input.focus();
}

// ---------- auth
let authMode = "login";
function setAuthMode(mode) {
  authMode = mode;
  const login = mode === "login";
  $("#auth-sub").textContent = login ? "Log in to continue learning." : "Create your free student account.";
  $("#auth-submit").textContent = login ? "Log in" : "Create account";
  $("#auth-toggle-text").textContent = login ? "New here?" : "Already have an account?";
  $("#auth-toggle").textContent = login ? "Create an account" : "Log in";
  $("#auth-error").textContent = "";
}
$("#auth-toggle").onclick = () => setAuthMode(authMode === "login" ? "register" : "login");

$("#auth-form").onsubmit = async (e) => {
  e.preventDefault();
  $("#auth-error").textContent = "";
  $("#auth-submit").disabled = true;
  try {
    const data = await api(authMode === "login" ? "/api/login" : "/api/register", "POST", {
      email: $("#auth-email").value,
      password: $("#auth-pass").value,
    });
    $("#auth-pass").value = "";
    await enterApp(data.user);
  } catch (err) {
    $("#auth-error").textContent = err.message;
  } finally {
    $("#auth-submit").disabled = false;
  }
};

function showAuth() {
  $("#app").classList.add("hidden");
  $("#auth").classList.remove("hidden");
}

async function enterApp(user) {
  APP.user = user;
  $("#side-user").textContent = user.full_name || user.email;
  $("#auth").classList.add("hidden");
  $("#app").classList.remove("hidden");
  await loadChats();
  showWelcome();
}

// ---------- chat list & history
async function loadChats() {
  APP.chats = (await api("/api/chats")).chats;
  renderChatList();
}

function renderChatList() {
  const list = $("#chat-list");
  list.innerHTML = "";
  if (!APP.chats.length) {
    const empty = document.createElement("div");
    empty.className = "muted";
    empty.style.padding = "8px 10px";
    empty.textContent = "No chats yet";
    list.appendChild(empty);
    return;
  }
  for (const chat of APP.chats) {
    const item = document.createElement("div");
    item.className = "chat-item" + (chat.id === APP.chatId ? " active" : "");

    const title = document.createElement("span");
    title.className = "chat-title";
    title.textContent = chat.title;

    const del = document.createElement("button");
    del.className = "chat-del";
    del.type = "button";
    del.title = "Delete chat";
    del.textContent = "x";
    del.onclick = (e) => { e.stopPropagation(); deleteChat(chat.id); };

    item.append(title, del);
    item.onclick = () => openChat(chat.id);
    list.appendChild(item);
  }
}

async function openChat(id) {
  const chat = await api(`/api/chats/${id}`);
  APP.chatId = id;
  $("#chat-title").textContent = chat.title;
  const thread = $("#thread");
  thread.innerHTML = "";
  if (!chat.messages.length) thread.innerHTML = WELCOME_HTML;
  chat.messages.forEach((m) => appendLoadedMessage(m.role, m.content));
  scrollBottom();
  renderChatList();
}

async function deleteChat(id) {
  if (!confirm("Delete this chat? This cannot be undone.")) return;
  try {
    await api(`/api/chats/${id}`, "DELETE");
    if (APP.chatId === id) showWelcome();
    await loadChats();
  } catch (err) {
    flash(err.message);
  }
}

$("#new-chat").onclick = () => {
  showWelcome();
};

// ---------- sending messages with streaming & stop capability
const input = $("#input");
let currentAbortController = null;

function autoSize() {
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 200) + "px";
}
input.addEventListener("input", autoSize);
input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    $("#composer").requestSubmit();
  }
});

function setGenerating(isGen) {
  APP.busy = isGen;
  const sendBtn = $("#send");
  if (isGen) {
    sendBtn.innerHTML = `&#9632;`;
    sendBtn.title = "Stop generating";
    sendBtn.classList.add("stop-btn");
  } else {
    sendBtn.innerHTML = `&uarr;`;
    sendBtn.title = "Send message";
    sendBtn.classList.remove("stop-btn");
  }
  $("#email-btn").disabled = isGen;
}

$("#composer").onsubmit = async (e) => {
  e.preventDefault();
  if (APP.busy) {
    if (currentAbortController) {
      currentAbortController.abort();
      currentAbortController = null;
    }
    return;
  }
  const text = input.value.trim();
  if (!text) return;

  input.value = "";
  autoSize();

  if (APP.chatId === null) {
    try {
      const created = await api("/api/chats", "POST");
      APP.chatId = created.id;
      $("#thread").innerHTML = "";
    } catch (err) {
      flash(err.message);
      return;
    }
  }

  appendUserMessage(text);
  const assistantObj = createAssistantMessage();

  setGenerating(true);
  currentAbortController = new AbortController();

  let accumulated = "";
  let hasStarted = false;

  try {
    const res = await fetch(`/api/chats/${APP.chatId}/messages/stream`, {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content: text }),
      signal: currentAbortController.signal,
    });

    if (!res.ok) {
      let errData = {};
      try { errData = await res.json(); } catch (_) {}
      throw new Error(errData.error || `Server error (${res.status})`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\\n\\n");
      buffer = parts.pop();

      for (const part of parts) {
        const line = part.trim();
        if (line.startsWith("data: ")) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.error) throw new Error(data.error);
            if (data.chunk) {
              if (!hasStarted) {
                hasStarted = true;
                assistantObj.startStreaming();
              }
              accumulated += data.chunk;
              assistantObj.updateContent(accumulated);
            }
            if (data.done) {
              if (data.title) {
                $("#chat-title").textContent = data.title;
              }
            }
          } catch (pe) {
            if (pe.message && !pe.message.startsWith("Unexpected")) {
              throw pe;
            }
          }
        }
      }
    }

    assistantObj.finish(accumulated);
    await loadChats();
  } catch (err) {
    if (err.name === "AbortError") {
      assistantObj.finish(accumulated || "Generation stopped.");
    } else {
      assistantObj.showError(err.message || "Failed to generate answer.");
      flash(err.message);
    }
  } finally {
    currentAbortController = null;
    setGenerating(false);
    input.focus();
  }
};

// ---------- email transcript
$("#email-btn").onclick = async () => {
  if (APP.chatId === null) return flash("Open a chat first.");
  $("#email-btn").disabled = true;
  flash("Sending transcript...");
  try {
    const result = await api(`/api/chats/${APP.chatId}/email`, "POST");
    flash(`Transcript sent to ${result.sent_to}`);
  } catch (err) {
    flash(err.message);
  } finally {
    $("#email-btn").disabled = false;
  }
};

// ---------- profile
function openProfile() {
  const u = APP.user;
  $("#p-name").value = u.full_name || "";
  $("#p-email").value = u.email;
  $("#p-school").value = u.school || "";
  $("#p-grade").value = u.grade || "";
  $("#p-interests").value = u.interests || "";
  $("#p-goal").value = u.learning_goal || "";
  $("#profile-error").textContent = "";
  $("#modal").classList.remove("hidden");
}
$("#profile-btn").onclick = openProfile;
$("#profile-cancel").onclick = () => $("#modal").classList.add("hidden");

$("#profile-form").onsubmit = async (e) => {
  e.preventDefault();
  try {
    const { user } = await api("/api/profile", "PUT", {
      full_name: $("#p-name").value,
      school: $("#p-school").value,
      grade: $("#p-grade").value,
      interests: $("#p-interests").value,
      learning_goal: $("#p-goal").value,
    });
    APP.user = user;
    $("#side-user").textContent = user.full_name || user.email;
    $("#modal").classList.add("hidden");
    flash("Profile saved");
  } catch (err) {
    $("#profile-error").textContent = err.message;
  }
};

// ---------- logout
$("#logout-btn").onclick = async () => {
  try { await api("/api/logout", "POST"); } catch (_) {}
  APP.user = null;
  APP.chats = [];
  APP.chatId = null;
  $("#thread").innerHTML = "";
  showAuth();
};

// ---------- Hide / Show Navigation Toggle Logic
function updateSidebarToggleUI(isCollapsed) {
  const btnText = $("#toggle-nav-text");
  if (btnText) {
    btnText.textContent = isCollapsed ? "Show bar" : "Hide bar";
  }
  const btn = $("#toggle-sidebar-btn");
  if (btn) {
    btn.title = isCollapsed ? "Show navigation bar" : "Hide navigation bar";
  }
}

function toggleSidebar() {
  const sidebar = $("#sidebar");
  sidebar.classList.toggle("collapsed");
  const isCollapsed = sidebar.classList.contains("collapsed");
  updateSidebarToggleUI(isCollapsed);
}

$("#toggle-sidebar-btn").onclick = toggleSidebar;
$("#sidebar-close-btn").onclick = toggleSidebar;

// ---------- boot
(async function boot() {
  setAuthMode("login");
  try {
    const { user } = await api("/api/me");
    await enterApp(user);
  } catch (_) {
    showAuth();
  }
})();
</script>
</body>
</html>
"""


@app.get("/")
def index():
    resp = Response(INDEX_HTML.replace("__APP_NAME__", APP_NAME), mimetype="text/html")
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp


init_db()

if __name__ == "__main__":
    app.run(
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG") == "1",
    )

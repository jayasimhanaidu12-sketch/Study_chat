# -*- coding: utf-8 -*-
import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update send_email and add format_markdown_for_email
old_send_email = '''def send_email(to_addr, subject, body, html_body=None):
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_file):
        load_dotenv(env_file, override=True)
    else:
        load_dotenv(override=True)

    host = os.getenv("SMTP_HOST")
    if not host:
        raise RuntimeError("Email is not configured on this server yet. Please set SMTP_HOST in .env.")
    port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = (os.getenv("SMTP_PASSWORD") or "").replace(" ", "").strip()
    sender = os.getenv("SMTP_FROM", smtp_user or "no-reply@localhost")

    clean_subject = " ".join(str(subject).split())
    msg = EmailMessage()
    msg["Subject"] = clean_subject
    msg["From"] = sender
    msg["To"] = to_addr
    msg.set_content(body)
    if html_body:
        msg.add_alternative(html_body, subtype="html")

    def _attempt_send(use_ssl, target_port):
        if use_ssl:
            ctx = ssl.create_default_context()
            with smtplib.SMTP_SSL(host, target_port, context=ctx, timeout=15) as smtp:
                if smtp_user:
                    smtp.login(smtp_user, smtp_password)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(host, target_port, timeout=15) as smtp:
                smtp.starttls()
                if smtp_user:
                    smtp.login(smtp_user, smtp_password)
                smtp.send_message(msg)

    # Support both port 465 (implicit SSL) and port 587 (STARTTLS).
    # If connection fails due to network/firewall blocking on one port, auto-fallback to the other.
    primary_ssl = (port == 465)
    try:
        _attempt_send(primary_ssl, port)
    except (OSError, smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected) as primary_err:
        fallback_port = 465 if port != 465 else 587
        fallback_ssl = (fallback_port == 465)
        try:
            _attempt_send(fallback_ssl, fallback_port)
        except Exception:
            raise primary_err'''

new_send_email = '''def format_markdown_for_email(text):
    """Render markdown to email-compatible HTML with crisp inline styling."""
    try:
        import markdown_it
        md = markdown_it.MarkdownIt("commonmark")
        html = md.render(text)
        # Pre code blocks
        html = html.replace("<pre>", '<pre style="background: #1e293b; color: #f8fafc; padding: 14px 18px; border-radius: 8px; overflow-x: auto; font-family: Consolas, \'Courier New\', monospace; font-size: 13px; line-height: 1.5; margin: 12px 0; border: 1px solid #334155;">')
        html = html.replace("<code>", '<code style="background: #e2e8f0; color: #0f172a; padding: 2px 6px; border-radius: 4px; font-family: Consolas, \'Courier New\', monospace; font-size: 12.5px;">')
        html = html.replace('border: 1px solid #334155;"><code style="background: #e2e8f0; color: #0f172a; padding: 2px 6px; border-radius: 4px; font-family: Consolas, \'Courier New\', monospace; font-size: 12.5px;">', 'border: 1px solid #334155;"><code style="color: #f8fafc; font-family: inherit; font-size: inherit; background: none; padding: 0;">')
        # Style headings
        html = html.replace("<h1>", '<h1 style="font-size: 18px; font-weight: 700; color: #0f172a; margin: 16px 0 8px;">')
        html = html.replace("<h2>", '<h2 style="font-size: 16px; font-weight: 700; color: #0f172a; margin: 14px 0 6px;">')
        html = html.replace("<h3>", '<h3 style="font-size: 15px; font-weight: 600; color: #0f172a; margin: 12px 0 6px;">')
        # Style lists
        html = html.replace("<ul>", '<ul style="margin: 8px 0 12px 20px; padding: 0; color: #1e293b; line-height: 1.6;">')
        html = html.replace("<ol>", '<ol style="margin: 8px 0 12px 20px; padding: 0; color: #1e293b; line-height: 1.6;">')
        html = html.replace("<li>", '<li style="margin-bottom: 4px;">')
        # Style paragraphs
        html = html.replace("<p>", '<p style="margin: 0 0 10px; line-height: 1.65; color: #1e293b;">')
        return html
    except Exception:
        import html as html_mod
        escaped = html_mod.escape(str(text))
        return "<p style=\'margin: 0 0 10px; line-height: 1.6; color: #1e293b;\'>" + escaped.replace("\\n\\n", "</p><p style=\'margin: 0 0 10px; line-height: 1.6; color: #1e293b;\'>").replace("\\n", "<br>") + "</p>"


def send_email(to_addr, subject, body, html_body=None):
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_file):
        load_dotenv(env_file, override=True)
    else:
        load_dotenv(override=True)

    host = os.getenv("SMTP_HOST")
    if not host:
        raise RuntimeError("Email is not configured on this server yet. Please set SMTP_HOST in .env.")
    port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = (os.getenv("SMTP_PASSWORD") or "").replace(" ", "").strip()
    sender = os.getenv("SMTP_FROM", smtp_user or "no-reply@localhost")

    clean_subject = " ".join(str(subject).split())
    msg = EmailMessage()
    msg["Subject"] = clean_subject
    msg["From"] = sender
    msg["To"] = to_addr
    msg.set_content(body)
    if html_body:
        msg.add_alternative(html_body, subtype="html")

    def _attempt_send(use_ssl, target_port):
        if use_ssl:
            ctx = ssl.create_default_context()
            with smtplib.SMTP_SSL(host, target_port, context=ctx, timeout=15) as smtp:
                if smtp_user:
                    smtp.login(smtp_user, smtp_password)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(host, target_port, timeout=15) as smtp:
                smtp.ehlo()
                smtp.starttls()
                smtp.ehlo()
                if smtp_user:
                    smtp.login(smtp_user, smtp_password)
                smtp.send_message(msg)

    # Support both port 465 (implicit SSL) and port 587 (STARTTLS).
    # If connection fails due to network/firewall blocking on one port, auto-fallback to the other.
    primary_ssl = (port == 465)
    try:
        _attempt_send(primary_ssl, port)
    except (OSError, smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected) as primary_err:
        fallback_port = 465 if port != 465 else 587
        fallback_ssl = (fallback_port == 465)
        try:
            _attempt_send(fallback_ssl, fallback_port)
        except Exception:
            raise primary_err'''

if old_send_email not in content:
    raise Exception("Could not find old_send_email in app.py")

content = content.replace(old_send_email, new_send_email, 1)
print("1. Replaced send_email and added format_markdown_for_email")

# 2. Update update_profile route to support email updating
old_profile_route = '''@app.put("/api/profile")
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
    return jsonify(user=user_dict(current_user()))'''

new_profile_route = '''@app.put("/api/profile")
@login_required
def update_profile():
    data = request.get_json(silent=True) or {}
    values = {}
    if "email" in data:
        new_email = str(data["email"] or "").strip().lower()
        if not EMAIL_RE.match(new_email):
            return error("Enter a valid email address.")
        existing = db().execute("SELECT id FROM users WHERE email = ? AND id != ?", (new_email, session["uid"])).fetchone()
        if existing:
            return error("An account with this email already exists.", 409)
        values["email"] = new_email

    for field, limit in PROFILE_LIMITS.items():
        if field in data:
            value = str(data[field] or "").strip()
            if len(value) > limit:
                return error(f"{field.replace('_', ' ').capitalize()} must be under {limit} characters.")
            values[field] = value

    if values:
        assignments = ", ".join(f"{column} = ?" for column in values)
        d = db()
        d.execute(f"UPDATE users SET {assignments} WHERE id = ?", (*values.values(), session["uid"]))
        d.commit()
    return jsonify(user=user_dict(current_user()))'''

if old_profile_route not in content:
    raise Exception("Could not find old_profile_route in app.py")

content = content.replace(old_profile_route, new_profile_route, 1)
print("2. Updated /api/profile to allow email editing")

# 3. Update /api/chats/<int:chat_id>/email route
old_email_chat_start = '@app.post("/api/chats/<int:chat_id>/email")'
old_email_chat_end = 'return jsonify(sent_to=user["email"])'

start_pos = content.find(old_email_chat_start)
end_pos = content.find(old_email_chat_end, start_pos)
if start_pos == -1 or end_pos == -1:
    raise Exception("Could not find email_chat route in app.py")

old_email_chat_block = content[start_pos : end_pos + len(old_email_chat_end)]

new_email_chat_block = '''@app.post("/api/chats/<int:chat_id>/email")
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
        return error("This chat has no messages yet. Ask a question first to generate notes!")

    user = current_user()
    data = request.get_json(silent=True) or {}
    recipient = str(data.get("email") or "").strip().lower() or user["email"]
    if not EMAIL_RE.match(recipient):
        return error("Please enter a valid recipient email address.")

    # Optionally update primary email in database
    if data.get("update_profile_email") and recipient != user["email"]:
        try:
            existing = db().execute("SELECT id FROM users WHERE email = ? AND id != ?", (recipient, session["uid"])).fetchone()
            if not existing:
                db().execute("UPDATE users SET email = ? WHERE id = ?", (recipient, session["uid"]))
                db().commit()
        except Exception:
            pass

    chat_title = chat["title"] or "Chat Transcript"
    clean_title = " ".join(str(chat_title).split())
    dt_now = datetime.now(timezone.utc)
    date_display = dt_now.strftime("%B %d, %Y at %H:%M UTC")
    student_display = user["full_name"] or recipient

    # Plain-text formatted transcript
    lines = [
        f"{APP_NAME} - Study Session Transcript",
        f"Topic: {clean_title}",
        f"Student: {student_display}",
        f"Date: {date_display}",
        f"Total Messages: {len(messages)}",
        "=" * 60,
        "",
    ]
    for m in messages:
        who = "You (Student)" if m["role"] == "user" else f"{APP_NAME} AI Tutor"
        lines += [
            f"[{m['created_at']}] {who}:",
            "-" * 40,
            str(m["content"]).strip(),
            "",
            "=" * 60,
            "",
        ]

    # HTML formatted transcript
    html_items = []
    for m in messages:
        is_user = m["role"] == "user"
        if is_user:
            import html as html_lib
            escaped_content = html_lib.escape(str(m["content"])).replace("\\n", "<br>")
            html_items.append(f"""
            <div style="margin-bottom: 20px; border: 1px solid #cbd5e1; border-radius: 12px; background: #f8fafc; overflow: hidden;">
                <div style="background: #f1f5f9; padding: 8px 14px; border-bottom: 1px solid #e2e8f0; display: flex; align-items: center; justify-content: space-between;">
                    <span style="display: inline-block; padding: 2px 8px; font-size: 11px; font-weight: 700; border-radius: 999px; background: #e0e7ff; color: #3730a3;">YOU (STUDENT)</span>
                    <span style="font-size: 11px; color: #64748b;">{m['created_at']}</span>
                </div>
                <div style="padding: 14px 16px; font-size: 14.5px; line-height: 1.6; color: #0f172a;">{escaped_content}</div>
            </div>
            """)
        else:
            formatted_answer = format_markdown_for_email(str(m["content"]))
            html_items.append(f"""
            <div style="margin-bottom: 24px; border: 1px solid #bfdbfe; border-radius: 12px; background: #ffffff; box-shadow: 0 2px 6px rgba(0,0,0,0.04); overflow: hidden;">
                <div style="background: #eff6ff; padding: 8px 14px; border-bottom: 1px solid #dbeafe; display: flex; align-items: center; justify-content: space-between;">
                    <span style="display: inline-block; padding: 2px 8px; font-size: 11px; font-weight: 700; border-radius: 999px; background: #2563eb; color: #ffffff;">{APP_NAME} AI TUTOR</span>
                    <span style="font-size: 11px; color: #64748b;">{m['created_at']}</span>
                </div>
                <div style="padding: 16px 18px; font-size: 14.5px; line-height: 1.65; color: #1e293b;">
                    {formatted_answer}
                </div>
            </div>
            """)

    html_body = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{clean_title}</title>
</head>
<body style="margin: 0; padding: 24px 12px; background-color: #0f172a; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #334155;">
  <div style="max-width: 660px; margin: 0 auto; background: #ffffff; border-radius: 14px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.25);">
    <div style="background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 60%, #3b82f6 100%); padding: 28px 24px; color: #ffffff;">
      <div style="margin-bottom: 8px;">
        <span style="background: rgba(255,255,255,0.2); padding: 4px 10px; border-radius: 999px; font-size: 11px; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase;">
          {APP_NAME} AI Tutor
        </span>
        <span style="font-size: 12px; opacity: 0.85; margin-left: 8px;">Study Session Transcript</span>
      </div>
      <h1 style="margin: 0 0 10px; font-size: 22px; font-weight: 700; line-height: 1.3; color: #ffffff;">{clean_title}</h1>
      <div style="font-size: 12.5px; opacity: 0.9; line-height: 1.5;">
        <span>Student: <strong>{student_display}</strong></span> &bull; 
        <span>{date_display}</span> &bull; 
        <span>{len(messages)} messages</span>
      </div>
    </div>
    <div style="padding: 24px; background: #ffffff;">
      {''.join(html_items)}
    </div>
    <div style="background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 20px 24px; text-align: center; font-size: 12px; color: #64748b; line-height: 1.6;">
      <div style="font-weight: 600; color: #334155; margin-bottom: 4px;">{APP_NAME} &mdash; Your Personal AI Tutor</div>
      <div>This study transcript was emailed upon request. You can review your chats or continue asking questions on {APP_NAME} anytime.</div>
    </div>
  </div>
</body>
</html>"""

    try:
        send_email(recipient, f"{APP_NAME}: {clean_title} [Transcript]", "\\n".join(lines), html_body=html_body)
    except RuntimeError as exc:
        return error(str(exc), 503)
    except smtplib.SMTPAuthenticationError:
        app.logger.exception("SMTP authentication failed")
        return error("Email authentication failed. Please check your Gmail App Password and SMTP_USER settings in .env.", 502)
    except smtplib.SMTPRecipientsRefused:
        app.logger.exception("SMTP recipient refused")
        return error(f"The recipient address ({recipient}) was rejected by the mail server.", 502)
    except (TimeoutError, socket.timeout, smtplib.SMTPConnectError, OSError) as exc:
        app.logger.exception("SMTP connection failed")
        return error(f"Could not connect to the mail server ({exc}). Please check your internet connection or firewall.", 502)
    except smtplib.SMTPException as exc:
        app.logger.exception("SMTP send failed")
        return error(f"Could not send email: {exc}", 502)
    except Exception as exc:
        app.logger.exception("Unexpected error during email transcript send")
        return error(f"Unexpected error: {exc}", 500)

    return jsonify(sent_to=recipient)'''

content = content[:start_pos] + new_email_chat_block + content[end_pos + len(old_email_chat_end):]
print("3. Updated /api/chats/<int:chat_id>/email route")

# 4. Update CSS in INDEX_HTML
old_modal_css = '''/* Profile modal */
#modal { position: fixed; inset: 0; background: rgba(0,0,0,.75); backdrop-filter: blur(6px); display: flex; align-items: center; justify-content: center; padding: 20px; z-index: 20; }
.modal-card { background: var(--side); border: 1px solid var(--border); border-radius: 18px; padding: 28px; width: 100%; max-width: 480px; max-height: 90vh; overflow-y: auto; box-shadow: 0 10px 40px rgba(0,0,0,0.65); }
.modal-card h2 { margin: 0 0 18px; font-size: 20px; font-weight: 700; }
.modal-actions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 10px; }'''

new_modal_css = '''/* Modals */
.modal-backdrop, #modal, #email-modal { position: fixed; inset: 0; background: rgba(0,0,0,.75); backdrop-filter: blur(6px); display: flex; align-items: center; justify-content: center; padding: 20px; z-index: 50; }
.modal-card { background: var(--side); border: 1px solid var(--border); border-radius: 18px; padding: 26px; width: 100%; max-width: 480px; max-height: 90vh; overflow-y: auto; box-shadow: 0 16px 48px rgba(0,0,0,0.7); animation: modalIn 0.2s cubic-bezier(0.16, 1, 0.3, 1); }
.modal-card h2 { margin: 0 0 16px; font-size: 20px; font-weight: 700; color: #fff; }
.modal-actions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 10px; }
@keyframes modalIn {
  from { opacity: 0; transform: scale(0.96) translateY(8px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}

/* Toast Notifications */
.toast-container { position: fixed; top: 20px; right: 20px; z-index: 9999; display: flex; flex-direction: column; gap: 10px; pointer-events: none; }
.toast { pointer-events: auto; display: flex; align-items: center; gap: 12px; padding: 12px 18px; background: rgba(15, 23, 42, 0.94); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 12px; color: #fff; font-size: 13.5px; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5), 0 0 20px rgba(59, 130, 246, 0.15); transform: translateY(-20px); opacity: 0; transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1); max-width: 420px; }
.toast.show { transform: translateY(0); opacity: 1; }
.toast.success { border-color: rgba(34, 197, 94, 0.4); box-shadow: 0 10px 30px rgba(0,0,0,0.5), 0 0 20px rgba(34,197,94,0.15); }
.toast.error { border-color: rgba(239, 68, 68, 0.4); box-shadow: 0 10px 30px rgba(0,0,0,0.5), 0 0 20px rgba(239,68,68,0.15); }
.toast.info { border-color: rgba(59, 130, 246, 0.4); }
.toast-icon { flex-shrink: 0; width: 20px; height: 20px; display: inline-flex; align-items: center; justify-content: center; }'''

if old_modal_css not in content:
    raise Exception("Could not find old_modal_css in app.py")

content = content.replace(old_modal_css, new_modal_css, 1)
print("4. Updated Modal and Toast CSS in INDEX_HTML")

# 5. Update HTML elements: topbar email button, email modal, profile modal email input, toast container
old_topbar_btn = '<button class="btn ghost" id="email-btn" type="button">Email transcript</button>'
new_topbar_btn = '''<button class="btn ghost" id="email-btn" type="button" title="Email transcript of this chat">
          <svg style="width:14px;height:14px;margin-right:6px;vertical-align:-2px;display:inline-block;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg>Email transcript
        </button>'''

if old_topbar_btn not in content:
    raise Exception("Could not find old_topbar_btn in app.py")

content = content.replace(old_topbar_btn, new_topbar_btn, 1)
print("5. Updated topbar email button with icon")

old_profile_email_field = '<div class="field"><label for="p-email">Email (transcripts are sent here)</label><input id="p-email" disabled></div>'
new_profile_email_field = '<div class="field"><label for="p-email">Email address</label><input id="p-email" type="email" maxlength="120"></div>'

if old_profile_email_field not in content:
    raise Exception("Could not find old_profile_email_field in app.py")

content = content.replace(old_profile_email_field, new_profile_email_field, 1)
print("6. Made profile email editable")

old_modal_end = '''    </form>
  </div>
</div>'''

new_modal_and_toast = '''    </form>
  </div>
</div>

<div id="email-modal" class="modal-backdrop hidden">
  <div class="modal-card">
    <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:14px;">
      <div>
        <h2 style="margin:0 0 4px; font-size:20px; font-weight:700;">Email Transcript</h2>
        <div style="font-size:13px; color:var(--muted);">Send this entire conversation with full AI explanations to an email.</div>
      </div>
      <button type="button" class="btn ghost close-btn" id="email-modal-close" style="padding:4px 8px; font-size:18px; border:none; background:none; cursor:pointer; color:var(--muted); line-height:1;">&times;</button>
    </div>

    <!-- Chat preview pill -->
    <div style="background:var(--panel); border:1px solid var(--border); border-radius:10px; padding:12px 14px; margin-bottom:16px; display:flex; align-items:center; gap:12px;">
      <div style="width:36px; height:36px; border-radius:8px; background:rgba(37,99,235,0.15); color:var(--blue-accent); display:flex; align-items:center; justify-content:center; flex-shrink:0;">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
      </div>
      <div style="min-width:0; flex:1;">
        <div id="email-modal-title" style="font-size:14px; font-weight:600; color:#fff; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">Current Chat</div>
        <div id="email-modal-meta" style="font-size:12px; color:var(--muted);">0 messages</div>
      </div>
    </div>

    <form id="email-transcript-form">
      <div class="field">
        <label for="email-recipient-input">Send transcript to</label>
        <input id="email-recipient-input" type="email" required placeholder="student@example.com" autocomplete="email">
        <span style="font-size:11.5px; color:var(--muted); margin-top:5px; display:block;">Enter any email address (your own, a parent, study partner, or teacher).</span>
      </div>

      <div style="margin:12px 0 6px; display:flex; align-items:center; gap:8px;">
        <input type="checkbox" id="email-save-primary" style="accent-color:var(--blue-solid); width:15px; height:15px; cursor:pointer;">
        <label for="email-save-primary" style="font-size:12.5px; color:var(--text); cursor:pointer; user-select:none; margin:0;">Also update my profile email address to this</label>
      </div>

      <p class="error" id="email-modal-error" style="margin:10px 0 0; min-height:16px;"></p>

      <div class="modal-actions" style="margin-top:18px;">
        <button type="button" class="btn ghost" id="email-modal-cancel">Cancel</button>
        <button type="submit" class="btn primary" id="email-modal-submit" style="display:inline-flex; align-items:center; gap:8px;">
          <svg id="email-modal-send-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg>
          <span id="email-modal-submit-text">Send transcript</span>
        </button>
      </div>
    </form>
  </div>
</div>

<div id="toast-container" class="toast-container"></div>'''

if old_modal_end not in content:
    raise Exception("Could not find old_modal_end in app.py")

content = content.replace(old_modal_end, new_modal_and_toast, 1)
print("7. Added email transcript modal and toast container")

# 6. Update flash function and add showToast
old_flash = '''function flash(message) {
  $("#status").textContent = message;
  clearTimeout(flash.timer);
  flash.timer = setTimeout(() => { $("#status").textContent = ""; }, 6000);
}'''

new_flash = '''function showToast(message, type = "info", duration = 4500) {
  const container = $("#toast-container");
  if (!container) return;
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  let iconSvg = '';
  if (type === 'success') {
    iconSvg = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>';
  } else if (type === 'error') {
    iconSvg = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>';
  } else {
    iconSvg = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>';
  }
  toast.innerHTML = `<span class="toast-icon">${iconSvg}</span><span style="flex:1;line-height:1.4;">${message}</span>`;
  container.appendChild(toast);
  requestAnimationFrame(() => toast.classList.add("show"));
  setTimeout(() => {
    toast.classList.remove("show");
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

function flash(message) {
  if (!message) return;
  showToast(message, "info");
}'''

if old_flash not in content:
    raise Exception("Could not find old_flash in app.py")

content = content.replace(old_flash, new_flash, 1)
print("8. Replaced flash with modern showToast")

# 7. Update JS email transcript logic and profile submit
old_email_js = '''// ---------- email transcript
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
};'''

new_email_js = '''// ---------- email transcript
const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

$("#email-btn").onclick = () => {
  if (APP.chatId === null) {
    showToast("Please select or start a chat first.", "info");
    return;
  }
  const currentChat = APP.chats.find(c => c.id === APP.chatId);
  const title = currentChat ? currentChat.title : ($("#chat-title").textContent || "Chat Transcript");
  const msgCount = $("#thread").querySelectorAll(".msg").length;
  if (msgCount === 0) {
    showToast("This chat has no messages yet. Ask a question first!", "info");
    return;
  }

  $("#email-modal-title").textContent = title;
  $("#email-modal-meta").textContent = `${msgCount} message${msgCount === 1 ? '' : 's'} in transcript`;
  $("#email-recipient-input").value = (APP.user && APP.user.email) || "";
  $("#email-save-primary").checked = false;
  $("#email-modal-error").textContent = "";
  $("#email-modal-submit").disabled = false;
  $("#email-modal-submit-text").textContent = "Send transcript";
  $("#email-modal").classList.remove("hidden");
  setTimeout(() => $("#email-recipient-input").focus(), 50);
};

$("#email-modal-close").onclick = () => $("#email-modal").classList.add("hidden");
$("#email-modal-cancel").onclick = () => $("#email-modal").classList.add("hidden");
$("#email-modal").onclick = (e) => {
  if (e.target === $("#email-modal")) $("#email-modal").classList.add("hidden");
};
$("#modal").onclick = (e) => {
  if (e.target === $("#modal")) $("#modal").classList.add("hidden");
};

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    $("#email-modal").classList.add("hidden");
    $("#modal").classList.add("hidden");
  }
});

$("#email-transcript-form").onsubmit = async (e) => {
  e.preventDefault();
  const email = $("#email-recipient-input").value.trim().toLowerCase();
  if (!email || !emailRegex.test(email)) {
    $("#email-modal-error").textContent = "Please enter a valid email address.";
    return;
  }

  const updatePrimary = $("#email-save-primary").checked;
  const submitBtn = $("#email-modal-submit");
  const submitText = $("#email-modal-submit-text");
  submitBtn.disabled = true;
  submitText.textContent = "Sending transcript...";
  $("#email-modal-error").textContent = "";

  try {
    const res = await api(`/api/chats/${APP.chatId}/email`, "POST", {
      email: email,
      update_profile_email: updatePrimary
    });
    if (updatePrimary && APP.user) {
      APP.user.email = res.sent_to;
      $("#side-user").textContent = APP.user.full_name || APP.user.email;
    }
    $("#email-modal").classList.add("hidden");
    showToast(`Transcript sent to ${res.sent_to}! Check your inbox.`, "success", 6000);
  } catch (err) {
    $("#email-modal-error").textContent = err.message || "Failed to send email transcript.";
  } finally {
    submitBtn.disabled = false;
    submitText.textContent = "Send transcript";
  }
};'''

if old_email_js not in content:
    raise Exception("Could not find old_email_js in app.py")

content = content.replace(old_email_js, new_email_js, 1)
print("9. Updated email modal opening, form handling, and shortcuts")

# 8. Update profile submit JS to include email
old_profile_submit = '''$("#profile-form").onsubmit = async (e) => {
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
  } catch (err) {'''

new_profile_submit = '''$("#profile-form").onsubmit = async (e) => {
  e.preventDefault();
  try {
    const { user } = await api("/api/profile", "PUT", {
      email: $("#p-email").value.trim(),
      full_name: $("#p-name").value,
      school: $("#p-school").value,
      grade: $("#p-grade").value,
      interests: $("#p-interests").value,
      learning_goal: $("#p-goal").value,
    });
    APP.user = user;
    $("#side-user").textContent = user.full_name || user.email;
    $("#modal").classList.add("hidden");
    showToast("Profile saved successfully!", "success");
  } catch (err) {'''

if old_profile_submit not in content:
    raise Exception("Could not find old_profile_submit in app.py")

content = content.replace(old_profile_submit, new_profile_submit, 1)
print("10. Updated profile form JS to include email saving")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("SUCCESS: app.py successfully updated!")

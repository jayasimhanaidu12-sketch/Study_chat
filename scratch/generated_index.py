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
  transition: transform 0.6s ease, filter 0.6s ease;
}

/* 1. Idle: The S logo stays still with a subtle solid blue glow */
.sc-logo.idle {
  filter: drop-shadow(0 0 8px rgba(29, 78, 216, 0.5));
}

/* 2. Thinking: Logo rotates continuously around vertical axis (360 Y-axis, 1.8s) with blue glow */
.sc-logo.thinking {
  animation: rotateY360 1.8s infinite linear;
}
@keyframes rotateY360 {
  0% {
    transform: perspective(600px) rotateY(0deg);
    filter: drop-shadow(0 0 10px rgba(29, 78, 216, 0.7)) drop-shadow(0 0 20px rgba(37, 99, 235, 0.5));
  }
  50% {
    filter: drop-shadow(0 0 18px rgba(29, 78, 216, 0.95)) drop-shadow(0 0 30px rgba(37, 99, 235, 0.7));
  }
  100% {
    transform: perspective(600px) rotateY(360deg);
    filter: drop-shadow(0 0 10px rgba(29, 78, 216, 0.7)) drop-shadow(0 0 20px rgba(37, 99, 235, 0.5));
  }
}

/* 3. Responding: The rotation slows and stops when the answer is ready */
.sc-logo.responding {
  animation: rotateSlowStop 0.9s cubic-bezier(0.2, 0.8, 0.3, 1) forwards;
  filter: drop-shadow(0 0 10px rgba(29, 78, 216, 0.6));
}
@keyframes rotateSlowStop {
  0% { transform: perspective(600px) rotateY(0deg); }
  100% { transform: perspective(600px) rotateY(360deg); }
}

/* 4. Error: subtle red indicator */
.sc-logo.error {
  filter: drop-shadow(0 0 14px rgba(239, 68, 68, 0.85));
}

@media (prefers-reduced-motion: reduce) {
  .sc-logo.thinking {
    animation: pulseBlueGlow 1.8s infinite ease-in-out;
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

/* ---------------- Studychat Thinking Box (Contains the rotating S-Logo) ---------------- */
.thinking-box {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  padding: 10px 18px;
  background: #0E1428;
  border: 1px solid var(--blue-solid);
  border-radius: 24px;
  font-size: 14px;
  color: #F1F5F9;
  margin-bottom: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.6), 0 0 22px rgba(29, 78, 216, 0.35);
  animation: fadeIn 0.25s ease;
}
.thinking-text { font-weight: 600; letter-spacing: 0.2px; }
.thinking-dots { display: inline-flex; gap: 4px; align-items: center; }
.thinking-dots span {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--blue-accent);
  animation: dotPulse 1.4s infinite ease-in-out both;
}
.thinking-dots span:nth-child(1) { animation-delay: -0.32s; }
.thinking-dots span:nth-child(2) { animation-delay: -0.16s; }
.thinking-dots span:nth-child(3) { animation-delay: 0s; }
@keyframes dotPulse {
  0%, 80%, 100% { transform: scale(0.7); opacity: 0.35; }
  40% { transform: scale(1.3); opacity: 1; background: #60A5FA; box-shadow: 0 0 8px #2563EB; }
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

// Creates assistant message: LOGO ONLY APPEARS IN THE THINKING BOX!
function createAssistantMessage() {
  const thread = $("#thread");
  const row = document.createElement("div");
  row.className = "msg assistant";

  row.innerHTML = `
    <div class="ai-badge" title="Studychat AI">SC</div>
    <div class="msg-body">
      <!-- Studychat Thinking Box: The S logo rotates smoothly while the AI processes -->
      <div class="thinking-box">
        <div class="logo-3d-wrap" style="width: 26px; height: 26px;">
          <img src="/static/studychat-icon.png" class="sc-logo thinking thinking-logo" style="width: 26px; height: 26px; object-fit: contain;" alt="Studychat thinking">
        </div>
        <span class="thinking-text">Studychat is thinking...</span>
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
  const thinkingLogo = row.querySelector(".thinking-logo");
  const markdownBody = row.querySelector(".markdown-body");
  const cursor = row.querySelector(".stream-cursor");
  const actions = row.querySelector(".msg-actions");

  return {
    startStreaming() {
      // Rotation slows and stops when answer begins streaming
      if (thinkingLogo) {
        thinkingLogo.classList.remove("thinking");
        thinkingLogo.classList.add("responding");
      }
      setTimeout(() => {
        if (thinkingBox) thinkingBox.remove();
        markdownBody.classList.remove("hidden");
        cursor.classList.remove("hidden");
      }, 300);
    },
    updateContent(text) {
      if (thinkingBox && !markdownBody.classList.contains("hidden")) {
        thinkingBox.remove();
      }
      markdownBody.innerHTML = renderMarkdown(text);
      markdownBody.appendChild(cursor);
      renderMath(markdownBody);
      scrollBottom();
    },
    finish(text) {
      if (thinkingBox) thinkingBox.remove();
      cursor.remove();
      const finalText = (text || "").trim() || "I couldn't generate a response. Please ask again.";
      markdownBody.classList.remove("hidden");
      markdownBody.innerHTML = renderMarkdown(finalText);
      renderMath(markdownBody);
      actions.classList.remove("hidden");
      actions.querySelector("button").dataset.content = finalText;
      scrollBottom();
    },
    showError(errMsg) {
      if (thinkingLogo) {
        thinkingLogo.classList.remove("thinking");
        thinkingLogo.classList.add("error");
      }
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
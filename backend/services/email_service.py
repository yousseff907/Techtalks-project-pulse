import html
import re

import resend

from config import APP_BASE_URL, RESEND_API_KEY

resend.api_key = RESEND_API_KEY

# ── Brand palette (hex approximations of the app's oklch design tokens in
# frontend/app/globals.css , email clients can't render oklch/var()). ──
PRIMARY = "#4f46e5"        # --primary  oklch(0.51 0.23 277)
PRIMARY_DARK = "#4133cb"   # hover / darker edge
TINT = "#eef2ff"           # light primary tint (code box background)
TINT_BORDER = "#e0e7ff"    # primary-tinted border
INK = "#0f182b"            # headings --sidebar navy
BODY = "#44444f"           # body copy
MUTED = "#8a8a94"          # secondary / fine print
PAGE_BG = "#f4f4f7"        # area around the card
CARD_BG = "#ffffff"
CARD_BORDER = "#ececf0"    # hairline

_FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"


def _send_email(to: str, subject: str, html_content: str) -> bool:
	try:
		params = {
		"from": "Project Pulse <noreply@easyrecipe.online>", # display name is Project Pulse; domain stays the Resend-verified one
		"to": [to],
		"subject": subject,
		"html": html_content}
		resend.Emails.send(params)
		return True
	except Exception:
		return False


def _inline_md(text: str) -> str:
	"""Escape a line of AI/user text, then apply inline **bold** markdown."""
	escaped = html.escape(text)
	return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)


def _format_summary(text: str) -> str:
	"""Turn the AI summary's plain text into readable HTML.

	Gemini returns paragraphs plus (often) bullet or numbered lists. Injecting
	that raw into one <p> collapses every newline into a space, so we walk it
	line by line and rebuild real block elements. Consecutive list items are
	grouped into a <ul>/<ol> even when a lead-in line ("Key risks:") sits
	directly above them with no blank line. Everything is HTML-escaped first.
	"""
	text = (text or "").strip()
	p_style = f"margin:0 0 16px;font-family:{_FONT};font-size:16px;line-height:1.7;color:{BODY};"
	if not text:
		return f'<p style="{p_style}">No summary content was available.</p>'

	h_style = f"margin:0 0 12px;font-family:{_FONT};font-size:18px;line-height:1.4;font-weight:700;color:{INK};"
	list_style = f"margin:0 0 16px;padding-left:22px;font-family:{_FONT};font-size:16px;line-height:1.7;color:{BODY};"
	li_style = "margin:0 0 6px;"

	text = text.replace("\r\n", "\n").replace("\r", "\n")

	parts = []
	para: list[str] = []       # buffered paragraph lines
	items: list[str] = []      # buffered list items
	list_tag: str | None = None  # "ul" or "ol" for the buffered list

	def flush_para():
		if para:
			parts.append(f'<p style="{p_style}">' + "<br>".join(_inline_md(ln) for ln in para) + "</p>")
			para.clear()

	def flush_list():
		nonlocal list_tag
		if items:
			li = "".join(f'<li style="{li_style}">{_inline_md(it)}</li>' for it in items)
			parts.append(f'<{list_tag} style="{list_style}">{li}</{list_tag}>')
			items.clear()
			list_tag = None

	for raw in text.split("\n"):
		line = raw.strip()

		if not line:
			flush_para()
			flush_list()
			continue

		heading = re.match(r"^#{1,6}\s+", line)
		bullet = re.match(r"^[-*]\s+", line)
		numbered = re.match(r"^\d+\.\s+", line)

		if heading:
			flush_para()
			flush_list()
			parts.append(f'<p style="{h_style}">{_inline_md(line[heading.end():])}</p>')
		elif bullet:
			flush_para()
			if list_tag == "ol":
				flush_list()
			list_tag = "ul"
			items.append(line[bullet.end():])
		elif numbered:
			flush_para()
			if list_tag == "ul":
				flush_list()
			list_tag = "ol"
			items.append(line[numbered.end():])
		else:
			flush_list()
			para.append(line)

	flush_para()
	flush_list()
	return "".join(parts)


def _base_layout(preheader: str, inner_html: str) -> str:
	"""Wrap content in the shared, branded, email-client-safe chrome.

	Table-based layout with 100% inline styles and hex colors so it renders
	consistently (Gmail-first) and degrades gracefully if <style> is stripped.
	"""
	preheader = html.escape(preheader)
	return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light">
<meta name="x-apple-disable-message-reformatting">
</head>
<body style="margin:0;padding:0;background:{PAGE_BG};">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;color:{PAGE_BG};font-size:1px;line-height:1px;">{preheader}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{PAGE_BG};">
<tr><td align="center" style="padding:32px 16px;">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="width:600px;max-width:100%;background:{CARD_BG};border:1px solid {CARD_BORDER};border-radius:14px;overflow:hidden;">

<!-- Header / logo -->
<tr><td style="padding:28px 32px 20px;">
<table role="presentation" cellpadding="0" cellspacing="0"><tr>
<td style="vertical-align:middle;">
<table role="presentation" cellpadding="0" cellspacing="0"><tr>
<td width="40" height="40" align="center" valign="middle" style="width:40px;height:40px;background:{PRIMARY};border-radius:11px;">
<div style="width:17px;height:17px;background:#ffffff;border-radius:5px;line-height:17px;">&nbsp;</div>
</td></tr></table>
</td>
<td style="vertical-align:middle;padding-left:12px;font-family:{_FONT};font-size:18px;font-weight:700;letter-spacing:-0.2px;color:{INK};">Project&nbsp;Pulse</td>
</tr></table>
</td></tr>

<tr><td style="padding:0 32px;"><div style="border-top:1px solid {CARD_BORDER};font-size:0;line-height:0;">&nbsp;</div></td></tr>

<!-- Body -->
<tr><td style="padding:28px 32px 32px;">{inner_html}</td></tr>

<!-- Footer -->
<tr><td style="padding:20px 32px 26px;background:{PAGE_BG};border-top:1px solid {CARD_BORDER};">
<p style="margin:0 0 4px;font-family:{_FONT};font-size:13px;font-weight:700;color:{INK};">Project Pulse</p>
<p style="margin:0;font-family:{_FONT};font-size:12px;line-height:1.6;color:{MUTED};">Unified project management &amp; analytics. This is an automated message&mdash;please don&#39;t reply.</p>
</td></tr>

</table>
</td></tr>
</table>
</body>
</html>"""


def send_summary_email(to: str, summary: str, workspace_name: str, workspace_id: int) -> bool:
	safe_name = html.escape(workspace_name or "your workspace")
	base = (APP_BASE_URL or "").rstrip("/")
	dashboard_url = f"{base}/workspaces/{workspace_id}/dashboard"
	body_html = _format_summary(summary)

	inner = f"""
<p style="margin:0 0 6px;font-family:{_FONT};font-size:13px;font-weight:600;letter-spacing:0.4px;text-transform:uppercase;color:{PRIMARY};">Workspace summary</p>
<h1 style="margin:0 0 20px;font-family:{_FONT};font-size:22px;line-height:1.3;font-weight:700;color:{INK};">{safe_name}</h1>
{body_html}
<table role="presentation" cellpadding="0" cellspacing="0" style="margin-top:8px;"><tr>
<td align="center" bgcolor="{PRIMARY}" style="border-radius:8px;">
<a href="{dashboard_url}" target="_blank" style="display:inline-block;padding:12px 28px;font-family:{_FONT};font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;border-radius:8px;">View in Project Pulse</a>
</td></tr></table>
"""

	subject = f"Your Project Pulse summary : {workspace_name}" if workspace_name else "Your Project Pulse workspace summary"
	preheader = f"Here's the latest summary for {workspace_name}." if workspace_name else "Your latest workspace summary."

	return _send_email(to, subject, _base_layout(preheader, inner))


def send_email(to: str, code: str) -> bool:
	safe_code = html.escape(code)

	inner = f"""
<h1 style="margin:0 0 12px;font-family:{_FONT};font-size:22px;line-height:1.3;font-weight:700;color:{INK};">Verify your email</h1>
<p style="margin:0 0 24px;font-family:{_FONT};font-size:16px;line-height:1.7;color:{BODY};">Enter the code below to finish signing in to Project Pulse.</p>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
<td align="center" style="background:{TINT};border:1px solid {TINT_BORDER};border-radius:12px;padding:22px 24px;font-family:'Courier New',Courier,monospace;font-size:34px;font-weight:700;letter-spacing:10px;color:{PRIMARY};">{safe_code}</td>
</tr></table>
<p style="margin:20px 0 0;font-family:{_FONT};font-size:14px;line-height:1.6;color:{MUTED};">This code expires in <strong style="color:{BODY};">15 minutes</strong>. If you didn&#39;t request it, you can safely ignore this email.</p>
"""

	subject = "Your Project Pulse verification code"
	preheader = "Your Project Pulse verification code (expires in 15 minutes)."

	return _send_email(to, subject, _base_layout(preheader, inner))
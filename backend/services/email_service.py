import resend
from config import RESEND_API_KEY

resend.api_key = RESEND_API_KEY

def _send_email(to: str, subject: str, html_content: str) -> bool:
	try:
		params = {
		"from": "EasyRecipe <noreply@easyrecipe.online>", # This is my domain / the domain on hand that we will be using
		"to": [to],
		"subject": subject,
		"html": html_content}
		resend.Emails.send(params)
		return True
	except Exception:
		return False

def send_summary_email(to: str, summary: str) -> bool:
	html_content = f"""
	<!DOCTYPE html>
	<html>
	<body>
		<h1>Your Workspace Summary</h1>
		<p>{summary}</p>
	</body>
	</html>"""

	subject = "Your Workspace Summary"

	return _send_email(to, subject, html_content)

def send_email(to: str, code: str) -> bool:
	html_content = f"""
	<!DOCTYPE html>
	<html>
	<body>
		<h1>Your verification code is:</h1>
		<h2>{code}</h2>
		<p>This code expires in 15 minutes.</p>
	</body>
	</html>""" # Will create a better design later on

	subject = "Your Project-Pulse Verification Code"

	return _send_email(to, subject, html_content)
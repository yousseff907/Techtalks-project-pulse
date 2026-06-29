import resend
from config import RESEND_API_KEY

resend.api_key = RESEND_API_KEY

def send_email(to: str, code: str) -> bool:
	try:
		html_content = f"""
		<!DOCTYPE html>
		<html>
		<body>
			<h1>Your verification code is:</h1>
			<h2>{code}</h2>
			<p>This code expires in 15 minutes.</p>
		</body>
		</html>""" # Will create a better design later on

		params = {
		"from": "EasyRecipe <noreply@easyrecipe.online>", # This is my domain / the domain on hand that we will be using
		"to": [to],
		"subject": "Your Project-Pulse Verification Code",
		"html": html_content}
		resend.Emails.send(params)
		return True
	except Exception:
		return False
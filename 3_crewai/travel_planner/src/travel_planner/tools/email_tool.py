from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class EmailInput(BaseModel):
    """Input for the email tool"""
    subject: str = Field(description="The email subject line")
    body: str = Field(description="The full email body containing the travel plan")


class EmailTool(BaseTool):
    name: str = "Send Travel Plan Email"
    description: str = (
        "Use this tool to send the completed travel plan to the traveler via email. "
        "Call this once the full plan is compiled and ready to deliver."
    )
    args_schema: Type[BaseModel] = EmailInput

    def _run(self, subject: str, body: str) -> str:
        sender = os.getenv("EMAIL_ADDRESS")
        password = os.getenv("EMAIL_PASSWORD")
        recipient = os.getenv("RECIPIENT_EMAIL")

        print(f"\nSending travel plan email to {recipient}...")

        try:
            # Build the email
            msg = MIMEMultipart()
            msg['From'] = sender
            msg['To'] = recipient
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            # Send via Gmail SMTP
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(sender, password)
                server.sendmail(sender, recipient, msg.as_string())

            print(f"Email sent successfully to {recipient}")
            return '{"status": "sent", "recipient": "' + recipient + '"}'

        except Exception as e:
            print(f"Email failed: {e}")
            return f'{{"status": "failed", "error": "{str(e)}"}}'
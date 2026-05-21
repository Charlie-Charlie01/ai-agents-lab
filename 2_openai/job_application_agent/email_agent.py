import os
from typing import Dict
from agents import Agent, function_tool
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content


EMAIL_AGENT_INSTRUCTIONS = (
    "You are an expert professional email writer specializing in job applications. "
    "You will be given a tailored CV and a cover letter. "
    "Your job is to send a professional, well-formatted HTML email that presents "
    "the candidate's application in the best possible light.\n"
    "You should:\n"
    "1. Write a compelling, specific email subject line that includes the job title "
    "and company name — never generic like 'Job Application'\n"
    "2. Write a short, professional email body (5-8 sentences) that:\n"
    "   - Opens with the candidate's name and the role they are applying for\n"
    "   - Briefly highlights their strongest selling point (1-2 sentences)\n"
    "   - Mentions that the cover letter and tailored CV are included below\n"
    "   - Closes with a clear, confident call to action\n"
    "3. Append the full cover letter and tailored CV below the email body, "
    "clearly separated with headings\n"
    "4. Format the entire email in clean, professional HTML — use headings, "
    "dividers, and spacing to make it easy to read\n\n"
    "Important rules:\n"
    "- The subject line must be specific to the role and company\n"
    "- Keep the email body concise — the cover letter does the heavy lifting\n"
    "- The HTML must be clean, professional, and render well in any email client\n"
    "- Use your send_email tool exactly once to send the application"
)


@function_tool
def send_email(subject: str, html_body: str) -> Dict[str, str]:
    """Send a job application email with the given subject line and HTML body."""
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get("SENDGRID_API_KEY"))
    from_email = Email(os.environ.get("SENDER_EMAIL", "applications@yourdomain.com"))
    to_email = To(os.environ.get("RECIPIENT_EMAIL", "your@email.com"))
    content = Content("text/html", html_body)
    mail = Mail(from_email, to_email, subject, content).get()
    response = sg.client.mail.send.post(request_body=mail)
    print(f"Email response: {response.status_code}")
    if response.status_code == 202:
        return {"status": "success", "message": f"Application email sent successfully. Subject: {subject}"}
    return {"status": "failed", "message": f"Email failed with status code: {response.status_code}"}


email_agent = Agent(
    name="Email Agent",
    instructions=EMAIL_AGENT_INSTRUCTIONS,
    tools=[send_email],
    model="gpt-4o-mini",
)
import os.path
import base64
from email.mime.text import MIMEText
from typing import List

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import config
from rich import print as rprint
from rich.panel import Panel
from rich.console import Console

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
TOKEN_FILE = "token.json"
CREDENTIALS_FILE = "credentials.json"

class EmailDraft(BaseModel):
    headline: str = Field(description="A big, bold, and exciting headline for the email.")
    hook: str = Field(description="A compelling, attention-grabbing opening sentence for the email.")
    body_paragraphs: List[str] = Field(description="A list of 2-3 paragraphs for the main body of the email, elaborating on the key selling points in a benefit-oriented way.")
    call_to_action: str = Field(description="The button-like text for the call to action, e.g., 'Shop The New Collection Now'.")
    closing: str = Field(description="A warm, professional closing for the email, e.g., 'Best regards, The Team'.")

class EmailAPI:
    def __init__(self, model_name="gemini-1.5-flash-latest"):
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=getattr(config, "GOOGLE_EMAIL_API_KEY", None)
        )
        self.structured_llm = llm.with_structured_output(EmailDraft)
        self.service = self._get_gmail_service()
        if self.service:
            rprint(Panel.fit("✅ [green]EmailAPI Initialized: LangChain Gemini for drafting, Gmail for sending.[/green]"))
        else:
            rprint(Panel.fit("⚠️ [yellow]EmailAPI Warning: Drafting is ready, but Gmail sending is disabled. Check credentials.[/yellow]"))

    def _get_gmail_service(self):
        creds = None
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    rprint(Panel(f"[yellow]Could not refresh token: {e}. Please re-authenticate.[/yellow]", title="Token Refresh Failed"))
                    os.remove(TOKEN_FILE)
                    return self._get_gmail_service()
            else:
                if not os.path.exists(CREDENTIALS_FILE):
                    rprint(Panel(f"[bold red]CRITICAL ERROR:[/bold red] '{CREDENTIALS_FILE}' not found. Cannot send emails.", title="❌ Authentication Error"))
                    return None
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(TOKEN_FILE, "w") as token:
                token.write(creds.to_json())
        
        try:
            service = build("gmail", "v1", credentials=creds)
            return service
        except HttpError as error:
            rprint(Panel(f"[bold red]An error occurred building Gmail service: {error}[/bold red]", title="❌ API Error"))
            return None

    def _create_message(self, sender: str, to: List[str], subject: str, message_text: str):
        message = MIMEText(message_text, "html")
        message["to"] = ", ".join(to)
        message["from"] = sender
        message["subject"] = subject
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        return {"raw": raw_message}

    def send_email(self, recipient_emails: List[str], subject: str, body: str) -> dict:
        if not self.service:
            return {"error": "Gmail service not initialized. Cannot send email."}
        
        try:
            message = self._create_message("me", recipient_emails, subject, body)
            sent_message = self.service.users().messages().send(userId="me", body=message).execute()
            rprint(Panel(f"✅ Email sent successfully to [cyan]{', '.join(recipient_emails)}[/cyan].", title="📧 Email Sent"))
            return {"status": "success", "message_id": sent_message["id"]}
        except HttpError as error:
            rprint(Panel(f"[bold red]Failed to send email: {error}[/bold red]", title="❌ Sending Error"))
            return {"error": f"Failed to send email: {error}"}

    def draft_and_send_promotional_email(self, recipient_emails: List[str], subject_line: str, product_name: str, key_selling_points: list, call_to_action_url: str) -> dict:
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are Atelier AI, a world-class creative director. Your task is to generate the structured text components for a promotional email. Your output must be a perfectly formed JSON object matching the `EmailDraft` structure."),
            ("human", """
            **📧 CREATIVE BRIEF: PROMOTIONAL EMAIL CAMPAIGN 📧**
            **👤 ROLE & PERSONA:**
            Act as a world-class Creative Director specializing in direct-response email marketing for premium, artisanal brands. Your tone is persuasive yet authentic, aiming to build a strong brand connection while driving sales.
            **🧠 GUIDING PHILOSOPHY:**
            1.  **Benefit over Feature:** Always translate product features into tangible, emotional benefits for the customer.
            2.  **Create Exclusivity:** Make the reader feel like they are getting a special, insider opportunity.
            3.  **Clarity is King:** The message must be simple to understand and the call-to-action impossible to miss.
            **📋 CAMPAIGN DETAILS:**
            *   **Product/Offer:** {product_name}
            *   **Key Selling Points / Features:** {selling_points}
            *   **Call-to-Action URL:** {cta_url}
            **📜 MANDATORY EXECUTION DIRECTIVES:**
            -   **`headline`:** Craft a big, bold, and exciting headline for the email.
            -   **`hook`:** Craft an attention-grabbing opening sentence.
            -   **`body_paragraphs`:** Write 2-3 paragraphs for the main text, converting features into a compelling narrative.
            -   **`call_to_action`:** Create an urgent and benefit-driven text for the main CTA button.
            -   **`closing`:** Write a warm, professional closing.
            """)
        ])

        chain = prompt | self.structured_llm

        try:
            rprint(Panel(f"✍️ [cyan]Drafting structured email for '{product_name}'...[/cyan]", title="Email Generation"))
            points_str = ", ".join(key_selling_points)
            email_components = chain.invoke({
                "product_name": product_name,
                "selling_points": points_str,
                "cta_url": call_to_action_url
            })
            
            body_p_html = "".join([f'<p style="font-family: Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #333333; margin: 0 0 20px 0;">{p}</p>' for p in email_components.body_paragraphs])

            email_body_html = f"""
            <!DOCTYPE html>
            <html>
            <head><title>{subject_line}</title></head>
            <body style="margin: 0; padding: 0; background-color: #f4f4f4;">
                <table border="0" cellpadding="0" cellspacing="0" width="100%">
                    <tr>
                        <td style="padding: 20px 0 30px 0;">
                            <table align="center" border="0" cellpadding="0" cellspacing="0" width="600" style="border: 1px solid #cccccc; border-collapse: collapse; background-color: #ffffff;">
                                <tr>
                                    <td align="center" style="padding: 40px 0 30px 0; background-color: #333333; color: #ffffff; font-size: 28px; font-weight: bold; font-family: Arial, sans-serif;">
                                        {product_name}
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 40px 30px 40px 30px;">
                                        <h1 style="font-size: 24px; margin: 0; font-family: Arial, sans-serif; color: #333333;">{email_components.headline}</h1>
                                        <p style="font-family: Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #333333; margin: 20px 0 30px 0;">{email_components.hook}</p>
                                        {body_p_html}
                                        <table border="0" cellpadding="0" cellspacing="0" width="100%">
                                            <tr>
                                                <td align="center" style="border-radius: 8px;" bgcolor="#4CAF50">
                                                    <a href="{call_to_action_url}" target="_blank" style="font-size: 18px; font-family: Arial, sans-serif; color: #ffffff; text-decoration: none; display: inline-block; padding: 14px 25px; border-radius: 8px;">{email_components.call_to_action}</a>
                                                </td>
                                            </tr>
                                        </table>
                                        <p style="font-family: Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #333333; margin: 30px 0 0 0;">{email_components.closing}</p>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 20px 30px; background-color: #eeeeee; text-align: center; font-family: Arial, sans-serif; font-size: 12px; color: #666666;">
                                        &copy; 2025 Your Brand Name. All rights reserved.<br/>
                                        <a href="#" style="color: #666666;">Unsubscribe</a>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </body>
            </html>
            """
            
            rprint(Panel(f"[bold green]✅ Email draft completed and assembled into HTML. Now sending...[/bold green]", title="Drafting Success"))
            
            return self.send_email(
                recipient_emails=recipient_emails,
                subject=subject_line,
                body=email_body_html
            )
        except Exception as e:
            rprint(Panel(f"[bold red]❌ Failed during the draft & send process: {e}[/bold red]", title="Error"))
            return {"error": f"Failed to draft and send email: {e}"}

if __name__ == "__main__":
    console = Console()
    console.print(Panel("🚀 [bold green]Starting EmailAPI Full Test Suite (Well-Designed HTML Edition)[/bold green] 🚀"))

    email_tool = EmailAPI()
    
    if not email_tool.service:
        console.print(Panel("[bold red]Could not initialize Gmail service. Aborting test.[/bold red]"))
    else:
        console.rule("[bold]Test Case: Draft and Send a Promotional Email to Multiple Recipients[/bold]")
        
        subject = "✨ A Special Offer for Our Valued Customers!"
        product = "The 'Artisan's Choice' Signature Leather Wallet"
        points = ["Hand-stitched from full-grain leather.", "Develops a beautiful patina over time.", "A timeless design, guaranteed for life."]
        cta_url = "https://www.your-shop-url.com/products/signature-wallet"

        test_recipients = ["23je0543@iitism.ac.in"] 
        
        send_result = email_tool.draft_and_send_promotional_email(
            recipient_emails=test_recipients,
            subject_line=subject,
            product_name=product,
            key_selling_points=points,
            call_to_action_url=cta_url
        )

        if send_result.get("status") != "success":
            console.print(Panel(f"[bold red]Process failed.[/bold red]\nError: {send_result.get('error')}", title="❌ Error"))

    console.print(Panel("🏁 [bold green]EmailAPI Test Suite Finished[/bold green] 🏁"))
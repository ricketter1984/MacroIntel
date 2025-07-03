import os
from dotenv import load_dotenv

# Load environment variables from config/.env
load_dotenv(dotenv_path="config/.env")
from email_report import send_daily_report

def main():
    html_content = """
    <html>
    <body>
        <h1>Test Email from MacroIntel</h1>
        <p>This is a <b>test email</b> sent to confirm SMTP settings are working.</p>
        <p>If you see this, your email configuration is correct!</p>
    </body>
    </html>
    """
    print("Sending test email...")
    success = send_daily_report(html_content)
    if success:
        print("✅ Test email sent successfully!")
    else:
        print("❌ Test email failed to send.")

if __name__ == "__main__":
    main() 
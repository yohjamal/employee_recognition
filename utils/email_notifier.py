"""
email_notifier.py
-----------------
Handles automated email notifications:
  - Winner congratulations email
  - HR summary report email

Uses Python's built-in smtplib (Gmail SMTP by default).
For production, swap to SendGrid or AWS SES.
"""

import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime


# ------------------------------------------------------------
# EMAIL TEMPLATES
# ------------------------------------------------------------

def build_winner_email(winner_name: str, department: str, score: float, month: str) -> tuple[str, str]:
    """Returns (subject, html_body) for the winner notification."""
    subject = f"🏆 Congratulations! You're {month} Employee of the Month!"

    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f4f6f9; padding: 30px;">
      <div style="max-width: 600px; margin: auto; background: white; border-radius: 12px;
                  padding: 40px; box-shadow: 0 4px 20px rgba(0,0,0,0.08);">

        <div style="text-align: center; margin-bottom: 30px;">
          <div style="font-size: 60px;">🏆</div>
          <h1 style="color: #1B5E96; margin: 10px 0;">Employee of the Month</h1>
          <p style="color: #888; font-size: 14px; margin: 0;">{month}</p>
        </div>

        <p style="font-size: 18px; color: #333;">Dear <strong>{winner_name}</strong>,</p>

        <p style="color: #555; line-height: 1.7;">
          We are delighted to announce that you have been selected as the
          <strong style="color: #1B5E96;">Employee of the Month for {month}</strong>!
          This recognition reflects your outstanding performance, dedication, and the
          positive impact you have on the team in the <strong>{department}</strong> department.
        </p>

        <div style="background: linear-gradient(135deg, #1B5E96, #2E75B6);
                    border-radius: 8px; padding: 20px; text-align: center; margin: 25px 0;">
          <p style="color: white; margin: 0; font-size: 14px; opacity: 0.85;">Your Recognition Score</p>
          <p style="color: white; margin: 5px 0; font-size: 42px; font-weight: bold;">{score:.1f}</p>
          <p style="color: white; margin: 0; font-size: 13px; opacity: 0.75;">out of 100</p>
        </div>

        <p style="color: #555; line-height: 1.7;">
          Your achievement will be celebrated at the next all-hands meeting and
          featured on our internal recognition board. Thank you for everything you do —
          you are a true asset to this organisation.
        </p>

        <p style="color: #555;">With appreciation,<br>
        <strong>HR Department</strong></p>

        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
        <p style="color: #aaa; font-size: 12px; text-align: center;">
          This is an automated notification from the Employee Recognition System.
        </p>
      </div>
    </body>
    </html>
    """
    return subject, html


def build_hr_summary_email(winner_name: str, department: str, score: float,
                            month: str, total_employees: int) -> tuple[str, str]:
    """Returns (subject, html_body) for the HR manager summary."""
    subject = f"[HR System] Employee of the Month Report — {month}"

    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f4f6f9; padding: 30px;">
      <div style="max-width: 600px; margin: auto; background: white; border-radius: 12px;
                  padding: 40px; box-shadow: 0 4px 20px rgba(0,0,0,0.08);">

        <h2 style="color: #1B5E96; border-bottom: 2px solid #e0e0e0; padding-bottom: 10px;">
          HR Summary Report — {month}
        </h2>

        <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
          <tr style="background: #f0f7ff;">
            <td style="padding: 12px; font-weight: bold; color: #555; width: 40%;">Winner</td>
            <td style="padding: 12px; color: #1B5E96; font-weight: bold;">{winner_name}</td>
          </tr>
          <tr>
            <td style="padding: 12px; font-weight: bold; color: #555;">Department</td>
            <td style="padding: 12px;">{department}</td>
          </tr>
          <tr style="background: #f0f7ff;">
            <td style="padding: 12px; font-weight: bold; color: #555;">Composite Score</td>
            <td style="padding: 12px;">{score:.2f} / 100</td>
          </tr>
          <tr>
            <td style="padding: 12px; font-weight: bold; color: #555;">Employees Evaluated</td>
            <td style="padding: 12px;">{total_employees}</td>
          </tr>
          <tr style="background: #f0f7ff;">
            <td style="padding: 12px; font-weight: bold; color: #555;">Generated On</td>
            <td style="padding: 12px;">{datetime.now().strftime("%d %B %Y, %H:%M")}</td>
          </tr>
        </table>

        <p style="color: #555; font-size: 13px;">
          This report was automatically generated by the Employee Recognition System.
          Please log in to the dashboard to view full rankings and scoring breakdown.
        </p>
      </div>
    </body>
    </html>
    """
    return subject, html


# ------------------------------------------------------------
# SMTP SENDER
# ------------------------------------------------------------

def send_email(
    to_address: str,
    subject: str,
    html_body: str,
    smtp_host: str,
    smtp_port: int,
    sender_email: str,
    sender_password: str,
) -> tuple[bool, str]:
    """
    Send an HTML email via SMTP.
    Returns (success: bool, message: str).
    """
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = to_address
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_address, msg.as_string())

        return True, f"Email sent to {to_address}"
    except smtplib.SMTPAuthenticationError:
        return False, "Authentication failed. Check your email credentials."
    except smtplib.SMTPException as e:
        return False, f"SMTP error: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


# ------------------------------------------------------------
# HIGH-LEVEL DISPATCHER
# Called by the Streamlit app
# ------------------------------------------------------------

def notify_winner(
    winner,
    month: str,
    total_employees: int,
    smtp_config: dict,
    hr_email: str,
) -> list[dict]:
    """
    Send winner email + HR summary email.
    Returns list of result dicts with {recipient, success, message}.
    """
    results = []

    winner_subject, winner_html = build_winner_email(
        winner_name=winner["name"],
        department=winner["department"],
        score=winner["composite_score"],
        month=month,
    )

    hr_subject, hr_html = build_hr_summary_email(
        winner_name=winner["name"],
        department=winner["department"],
        score=winner["composite_score"],
        month=month,
        total_employees=total_employees,
    )

    for recipient, subject, html in [
        (winner["email"], winner_subject, winner_html),
        (hr_email, hr_subject, hr_html),
    ]:
        ok, msg = send_email(
            to_address=recipient,
            subject=subject,
            html_body=html,
            smtp_host=smtp_config["host"],
            smtp_port=smtp_config["port"],
            sender_email=smtp_config["sender_email"],
            sender_password=smtp_config["sender_password"],
        )
        results.append({"recipient": recipient, "success": ok, "message": msg})

    return results

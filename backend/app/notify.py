"""Submitter email notifications on approve/reject.

Provider-agnostic and entirely optional. Resolution order:
  1. RESEND_API_KEY  -> Resend
  2. SENDGRID_API_KEY -> SendGrid
  3. neither         -> log and skip (no-op)

A failed send never propagates — moderation must succeed regardless of email.
"""
import logging

import httpx

from .config import EMAIL_FROM, PUBLIC_BASE_URL, RESEND_API_KEY, SENDGRID_API_KEY

logger = logging.getLogger(__name__)


def _build_email(decision: str, entry: dict, reason: str):
    company = entry.get("company_name", "the company")
    person = entry.get("person_name", "")
    quote = entry.get("quote", "")
    if decision == "approved":
        slug = entry.get("slug", "")
        url = f"{PUBLIC_BASE_URL}/entry/{slug}" if slug else PUBLIC_BASE_URL
        subject = f"🚩 Your Red Flag about {company} is now live"
        text = (
            f"Good news — your submission about {person} at {company} has been "
            f"approved and is now public on dontworkhere.\n\n"
            f"View it: {url}\n\n"
            f"Thanks for keeping the working world honest."
        )
        html = (
            f"<p>Good news — your submission about <strong>{person}</strong> at "
            f"<strong>{company}</strong> has been approved and is now public on dontworkhere.</p>"
            f'<p><a href="{url}">View your Red Flag &raquo;</a></p>'
            f"<p>Thanks for keeping the working world honest. 🚩</p>"
        )
    else:
        subject = f"Your Red Flag submission about {company} wasn't approved"
        reason_line = f'Reason given: "{reason}"' if reason else "No specific reason was provided."
        appeal_url = f"{PUBLIC_BASE_URL}/submit"
        text = (
            f"Thanks for your submission about {person} at {company}. After review, a "
            f"moderator did not approve it for publication.\n\n"
            f"{reason_line}\n\n"
            f"If you have additional sources or context, you're welcome to resubmit: {appeal_url}"
        )
        html = (
            f"<p>Thanks for your submission about <strong>{person}</strong> at "
            f"<strong>{company}</strong>. After review, a moderator did not approve it "
            f"for publication.</p>"
            f"<p>{reason_line}</p>"
            f'<p>If you have additional sources or context, you\'re welcome to '
            f'<a href="{appeal_url}">resubmit</a>.</p>'
        )
    return subject, text, html


async def send_decision_email(to: str, decision: str, entry: dict, reason: str = "") -> dict:
    to = (to or "").strip()
    if not to:
        return {"sent": False, "reason": "no recipient"}

    subject, text, html = _build_email(decision, entry, reason)

    try:
        if RESEND_API_KEY:
            async with httpx.AsyncClient(timeout=10) as hc:
                r = await hc.post(
                    "https://api.resend.com/emails",
                    headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
                    json={"from": EMAIL_FROM, "to": [to], "subject": subject,
                          "html": html, "text": text},
                )
            r.raise_for_status()
            return {"sent": True, "provider": "resend"}

        if SENDGRID_API_KEY:
            async with httpx.AsyncClient(timeout=10) as hc:
                r = await hc.post(
                    "https://api.sendgrid.com/v3/mail/send",
                    headers={"Authorization": f"Bearer {SENDGRID_API_KEY}"},
                    json={
                        "personalizations": [{"to": [{"email": to}]}],
                        "from": {"email": EMAIL_FROM},
                        "subject": subject,
                        "content": [
                            {"type": "text/plain", "value": text},
                            {"type": "text/html", "value": html},
                        ],
                    },
                )
            r.raise_for_status()
            return {"sent": True, "provider": "sendgrid"}

        logger.info("[notify] no email provider configured; would send to %s: %s", to, subject)
        return {"sent": False, "reason": "no provider configured"}
    except Exception as e:  # network/provider error — log and move on
        logger.warning("[notify] failed to email %s: %s", to, e)
        return {"sent": False, "reason": str(e)}

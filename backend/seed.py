"""Seed the directory with fictional, satirical sample Red Flag entries.
Idempotent: re-running will not duplicate entries (matched by slug).
All companies and people below are FICTIONAL and for satire/demo purposes only.
"""
import asyncio
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

client = AsyncIOMotorClient(os.environ["MONGO_URL"])
db = client[os.environ["DB_NAME"]]


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


SAMPLES = [
    {
        "company_name": "HustleForge Labs", "company_domain": "hustleforge.io",
        "person_name": "Brad Vanterpool", "person_title": "Founder & CEO",
        "quote": "Sleep is a competitor. If you're sleeping eight hours, your rival who sleeps four is already eating your lunch.",
        "statement_date": "2023-09-14", "red_flag_score": 5,
        "sources": [{"label": "Podcast", "url": "https://example.com/hustleforge-podcast"}, {"label": "Twitter", "url": "https://twitter.com/example/status/1"}],
        "tags": ["Hustle Culture", "Anti-Sleep"],
    },
    {
        "company_name": "FamFirst Dynamics", "company_domain": "famfirst.co",
        "person_name": "Karen Mortlake", "person_title": "Chief People Officer",
        "quote": "We're not coworkers here, we're family. And family doesn't ask about overtime pay on a Sunday.",
        "statement_date": "2024-02-02", "red_flag_score": 4,
        "sources": [{"label": "LinkedIn", "url": "https://linkedin.com/posts/example"}],
        "tags": ["Fake Family", "Unpaid Overtime"],
    },
    {
        "company_name": "GrindCore Capital", "company_domain": "grindcore.fund",
        "person_name": "Derek Saulsbury", "person_title": "Managing Partner",
        "quote": "You need to bleed for this company. If your job isn't costing you your marriage, you're not committed enough.",
        "statement_date": "2022-11-30", "red_flag_score": 5,
        "sources": [{"label": "Interview", "url": "https://example.com/grindcore-interview"}, {"label": "Archive.org", "url": "https://web.archive.org/example"}],
        "tags": ["Hustle Culture", "Work Over Family"],
    },
    {
        "company_name": "Velocity Synergy", "company_domain": "velocitysynergy.com",
        "person_name": "Priya Hargrove", "person_title": "VP of Culture",
        "quote": "Work-life balance is a myth invented by people who don't want to win. Here, work IS the life.",
        "statement_date": "2023-06-21", "red_flag_score": 4,
        "sources": [{"label": "News Article", "url": "https://example.com/velocity-news"}],
        "tags": ["Anti-Work-Life-Balance"],
    },
    {
        "company_name": "NeverSleep AI", "company_domain": "neversleep.ai",
        "person_name": "Marcus Vandenberg", "person_title": "Co-Founder",
        "quote": "We expect 996 minimum. If you want to change the world, weekends are a luxury you haven't earned yet.",
        "statement_date": "2024-04-18", "red_flag_score": 5,
        "sources": [{"label": "Blog", "url": "https://example.com/neversleep-blog"}, {"label": "Twitter", "url": "https://twitter.com/example/status/2"}],
        "tags": ["996", "Hustle Culture"],
    },
    {
        "company_name": "Apex Grindhouse", "company_domain": "apexgrindhouse.com",
        "person_name": "Tonya Beckwith", "person_title": "CEO",
        "quote": "I don't believe in burnout. Burnout is just a story weak people tell themselves to justify quitting.",
        "statement_date": "2023-01-09", "red_flag_score": 4,
        "sources": [{"label": "Conference Talk", "url": "https://example.com/apex-talk"}],
        "tags": ["Burnout Denial"],
    },
    {
        "company_name": "Quantum Hustle Co", "company_domain": "quantumhustle.co",
        "person_name": "Roland Pierce", "person_title": "Founder",
        "quote": "If you can see your kids more than twice a week, you're stealing time from your true mission here.",
        "statement_date": "2022-08-12", "red_flag_score": 5,
        "sources": [{"label": "Memo", "url": "https://example.com/quantum-memo"}],
        "tags": ["Work Over Family"],
    },
    {
        "company_name": "Maximal Output Inc", "company_domain": "maximaloutput.com",
        "person_name": "Gwen Castellano", "person_title": "Head of Operations",
        "quote": "Vacation requests are basically a resignation letter you haven't finished writing yet.",
        "statement_date": "2024-01-25", "red_flag_score": 3,
        "sources": [{"label": "Slack Leak", "url": "https://example.com/maximal-slack"}, {"label": "News Article", "url": "https://example.com/maximal-news"}],
        "tags": ["Anti-Vacation"],
    },
]


async def main():
    inserted = 0
    for s in SAMPLES:
        year = s["statement_date"][:4]
        slug = slugify(f"{s['person_name']}-{s['company_name']}-{year}")
        if await db.entries.find_one({"slug": slug}):
            continue
        now = datetime.now(timezone.utc).isoformat()
        doc = {
            "id": str(uuid.uuid4()),
            "company_name": s["company_name"],
            "company_domain": s["company_domain"],
            "person_name": s["person_name"],
            "person_title": s["person_title"],
            "quote": s["quote"],
            "statement_date": s["statement_date"],
            "sources": s["sources"],
            "tags": s.get("tags", []),
            "submitter_email": "",
            "status": "approved",
            "red_flag_score": s["red_flag_score"],
            "slug": slug,
            "rejection_reason": None,
            "views": 0,
            "created_at": now,
            "approved_at": now,
        }
        await db.entries.insert_one(doc)
        inserted += 1
    print(f"Seed complete. Inserted {inserted} new entries.")
    client.close()


if __name__ == "__main__":
    asyncio.run(main())

"""Backend API tests for dontworkhere.xyz"""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://boss-receipts.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"
TOKEN = "test_session_qa"  # seeded session per /app/auth_testing.md
AUTH = {"Authorization": f"Bearer {TOKEN}"}


# ----------------- Public entries -----------------
class TestPublicEntries:
    def test_list_entries_returns_approved(self):
        r = requests.get(f"{API}/entries", timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert "total" in data and "items" in data
        assert isinstance(data["items"], list)
        assert data["total"] >= 8
        for it in data["items"]:
            assert it.get("slug"), "approved entries should have slug"
            # private fields stripped
            assert "submitter_email" not in it
            assert "status" not in it

    def test_search_by_keyword(self):
        # Search for 'sleep' should match the seeded entry containing 'sleep'
        r = requests.get(f"{API}/entries", params={"search": "sleep"}, timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 1
        joined = " ".join((i.get("quote", "") + i.get("company_name", "") + i.get("person_name", "")).lower() for i in data["items"])
        assert "sleep" in joined

    def test_get_entry_by_slug(self):
        # The review brief uses "boss-receipts" as an example slug, but the actual
        # seeded slugs follow person-company-year pattern. Use the first real one.
        listing = requests.get(f"{API}/entries", timeout=15).json()
        first_slug = listing["items"][0]["slug"]
        r = requests.get(f"{API}/entries/{first_slug}", timeout=15)
        assert r.status_code == 200, f"slug {first_slug} should exist (status {r.status_code})"
        data = r.json()
        assert data["slug"] == first_slug
        assert data.get("quote")
        assert data.get("red_flag_score") in [1, 2, 3, 4, 5]

    def test_get_entry_invalid_slug_404(self):
        r = requests.get(f"{API}/entries/does-not-exist-xyz", timeout=15)
        assert r.status_code == 404


# ----------------- Submissions -----------------
class TestSubmissions:
    def test_create_submission_pending(self):
        payload = {
            "company_name": "TEST_CompanyA",
            "person_name": "TEST Person",
            "person_title": "CEO",
            "quote": "Working weekends is the only path to glorious productivity and joy.",
            "statement_date": "2024-06-01",
            "sources": [{"label": "Tweet", "url": "https://example.com/tweet1"}],
            "submitter_email": "tester@example.com",
        }
        r = requests.post(f"{API}/submissions", json=payload, timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body.get("ok") is True
        assert "id" in body

        # Verify pending entries don't appear in public listing
        r2 = requests.get(f"{API}/entries", params={"search": "TEST_CompanyA"}, timeout=15)
        assert r2.status_code == 200
        assert r2.json()["total"] == 0, "pending submission should not appear publicly"

        # Verify visible via mod listing
        r3 = requests.get(f"{API}/mod/entries", params={"status": "pending"}, headers=AUTH, timeout=15)
        assert r3.status_code == 200
        ids = [e["id"] for e in r3.json()["items"]]
        assert body["id"] in ids

    def test_quote_too_short_422(self):
        payload = {
            "company_name": "Acme",
            "person_name": "Bob",
            "quote": "too short",
            "sources": [{"label": "x", "url": "https://example.com"}],
        }
        r = requests.post(f"{API}/submissions", json=payload, timeout=15)
        assert r.status_code == 422

    def test_missing_sources_422(self):
        payload = {
            "company_name": "Acme",
            "person_name": "Bob",
            "quote": "This is a valid length quote for testing purposes.",
            "sources": [],
        }
        r = requests.post(f"{API}/submissions", json=payload, timeout=15)
        assert r.status_code == 422

    def test_bad_source_url_422(self):
        payload = {
            "company_name": "Acme",
            "person_name": "Bob",
            "quote": "This is a valid length quote for testing purposes.",
            "sources": [{"label": "x", "url": "ftp://not-allowed.example"}],
        }
        r = requests.post(f"{API}/submissions", json=payload, timeout=15)
        assert r.status_code == 422


# ----------------- Auth Guard -----------------
class TestAuthGuard:
    def test_stats_requires_auth(self):
        r = requests.get(f"{API}/mod/stats", timeout=15)
        assert r.status_code == 401

    def test_mod_entries_requires_auth(self):
        r = requests.get(f"{API}/mod/entries", timeout=15)
        assert r.status_code == 401

    def test_invalid_token_401(self):
        r = requests.get(f"{API}/mod/stats", headers={"Authorization": "Bearer invalid_xxx"}, timeout=15)
        assert r.status_code == 401

    def test_auth_me(self):
        r = requests.get(f"{API}/auth/me", headers=AUTH, timeout=15)
        assert r.status_code == 200
        assert r.json()["email"] == "qa.mod@example.com"


# ----------------- Moderator Flows -----------------
class TestModeratorFlows:
    @pytest.fixture(scope="class")
    def submitted_id(self):
        payload = {
            "company_name": "TEST_ModFlow",
            "person_name": "TEST ModPerson",
            "person_title": "VP",
            "quote": "Rest is just a fancy word for falling behind everybody.",
            "statement_date": "2024-05-05",
            "sources": [{"label": "Blog", "url": "https://example.com/blog-mod"}],
        }
        r = requests.post(f"{API}/submissions", json=payload, timeout=15)
        assert r.status_code == 200
        return r.json()["id"]

    def test_stats(self):
        r = requests.get(f"{API}/mod/stats", headers=AUTH, timeout=15)
        assert r.status_code == 200
        d = r.json()
        for k in ["live", "pending", "total", "rejected"]:
            assert k in d
            assert isinstance(d[k], int)

    def test_list_pending(self, submitted_id):
        r = requests.get(f"{API}/mod/entries", params={"status": "pending"}, headers=AUTH, timeout=15)
        assert r.status_code == 200
        ids = [e["id"] for e in r.json()["items"]]
        assert submitted_id in ids

    def test_approve_creates_slug_and_publishes(self, submitted_id):
        r = requests.post(
            f"{API}/mod/entries/{submitted_id}/approve",
            json={"red_flag_score": 4},
            headers=AUTH, timeout=15,
        )
        assert r.status_code == 200, r.text

        # Now appears in public listing
        time.sleep(0.5)
        r2 = requests.get(f"{API}/entries", params={"search": "TEST_ModFlow"}, timeout=15)
        assert r2.status_code == 200
        assert r2.json()["total"] >= 1
        item = r2.json()["items"][0]
        assert item["red_flag_score"] == 4
        assert item["slug"]
        # Fetch by slug works
        r3 = requests.get(f"{API}/entries/{item['slug']}", timeout=15)
        assert r3.status_code == 200

    def test_edit_entry_persists(self, submitted_id):
        r = requests.put(
            f"{API}/mod/entries/{submitted_id}",
            json={"red_flag_score": 5, "person_title": "Chief Vibe Officer"},
            headers=AUTH, timeout=15,
        )
        assert r.status_code == 200
        # Verify
        r2 = requests.get(f"{API}/mod/entries", headers=AUTH, timeout=15)
        match = [e for e in r2.json()["items"] if e["id"] == submitted_id]
        assert match and match[0]["red_flag_score"] == 5
        assert match[0]["person_title"] == "Chief Vibe Officer"

    def test_unpublish_moves_to_pending(self, submitted_id):
        r = requests.post(f"{API}/mod/entries/{submitted_id}/unpublish", headers=AUTH, timeout=15)
        assert r.status_code == 200
        # No longer public
        r2 = requests.get(f"{API}/entries", params={"search": "TEST_ModFlow"}, timeout=15)
        assert r2.json()["total"] == 0

    def test_reject_with_reason(self, submitted_id):
        r = requests.post(
            f"{API}/mod/entries/{submitted_id}/reject",
            json={"rejection_reason": "TEST rejection"}, headers=AUTH, timeout=15,
        )
        assert r.status_code == 200
        r2 = requests.get(f"{API}/mod/entries", params={"status": "rejected"}, headers=AUTH, timeout=15)
        match = [e for e in r2.json()["items"] if e["id"] == submitted_id]
        assert match and match[0]["rejection_reason"] == "TEST rejection"


# ----------------- Moderator Management -----------------
class TestModeratorManagement:
    TEST_EMAIL = "test_invitee@example.com"

    def test_list_moderators_has_me(self):
        r = requests.get(f"{API}/mod/moderators", headers=AUTH, timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d["me"] == "qa.mod@example.com"
        assert any(m["email"] == "qa.mod@example.com" for m in d["items"])

    def test_add_moderator(self):
        # cleanup first
        requests.delete(f"{API}/mod/moderators/{self.TEST_EMAIL}", headers=AUTH, timeout=15)
        r = requests.post(f"{API}/mod/moderators", json={"email": self.TEST_EMAIL}, headers=AUTH, timeout=15)
        assert r.status_code in (200, 400), r.text  # 400 ok if cleanup left disabled record reactivated path
        # Verify appears
        r2 = requests.get(f"{API}/mod/moderators", headers=AUTH, timeout=15)
        emails = [m["email"] for m in r2.json()["items"] if m.get("active", True)]
        assert self.TEST_EMAIL in emails

    def test_cannot_remove_self(self):
        r = requests.delete(f"{API}/mod/moderators/qa.mod@example.com", headers=AUTH, timeout=15)
        assert r.status_code == 400

    def test_remove_added_moderator(self):
        r = requests.delete(f"{API}/mod/moderators/{self.TEST_EMAIL}", headers=AUTH, timeout=15)
        assert r.status_code == 200
        r2 = requests.get(f"{API}/mod/moderators", headers=AUTH, timeout=15)
        active = [m["email"] for m in r2.json()["items"] if m.get("active", True)]
        assert self.TEST_EMAIL not in active

    def test_unknown_moderator_delete_404(self):
        r = requests.delete(
            f"{API}/mod/moderators/ghost_{int(time.time())}@example.com", headers=AUTH, timeout=15
        )
        assert r.status_code == 404

    def test_reactivate_returns_flag(self):
        email = "reactivate_test@example.com"
        requests.delete(f"{API}/mod/moderators/{email}", headers=AUTH, timeout=15)
        r1 = requests.post(f"{API}/mod/moderators", json={"email": email}, headers=AUTH, timeout=15)
        assert r1.status_code == 200 and r1.json().get("reactivated") is False
        requests.delete(f"{API}/mod/moderators/{email}", headers=AUTH, timeout=15)
        r2 = requests.post(f"{API}/mod/moderators", json={"email": email}, headers=AUTH, timeout=15)
        assert r2.status_code == 200 and r2.json().get("reactivated") is True
        requests.delete(f"{API}/mod/moderators/{email}", headers=AUTH, timeout=15)  # cleanup


# ----------------- Browse extras: sort / tags / views / og / sitemap -----------------
class TestBrowseExtras:
    def test_sort_highest_is_descending(self):
        r = requests.get(f"{API}/entries", params={"sort": "highest", "limit": 9}, timeout=15)
        assert r.status_code == 200
        scores = [i["red_flag_score"] for i in r.json()["items"]]
        assert scores == sorted(scores, reverse=True)

    def test_tags_listing_and_filter(self):
        tags = requests.get(f"{API}/tags", timeout=15).json()["items"]
        assert tags, "expected at least one tag from seeded data"
        tag, count = tags[0]["tag"], tags[0]["count"]
        r = requests.get(f"{API}/entries", params={"tag": tag}, timeout=15)
        assert r.status_code == 200
        assert r.json()["total"] == count
        for it in r.json()["items"]:
            assert tag in it.get("tags", [])

    def test_tags_respect_search(self):
        # A search that matches no entry yields no tag facets.
        empty = requests.get(f"{API}/tags", params={"search": "zzzqqq_nomatch_xyz"}, timeout=15).json()["items"]
        assert empty == []
        # A search that matches some entries yields only that subset's tags, with
        # counts no larger than the global counts.
        global_counts = {t["tag"]: t["count"] for t in requests.get(f"{API}/tags", timeout=15).json()["items"]}
        scoped = requests.get(f"{API}/tags", params={"search": "sleep"}, timeout=15).json()["items"]
        assert scoped, "expected tags for entries matching 'sleep'"
        for t in scoped:
            assert t["count"] <= global_counts.get(t["tag"], 0)

    def test_view_count_increments(self):
        slug = requests.get(f"{API}/entries", timeout=15).json()["items"][0]["slug"]
        v1 = requests.get(f"{API}/entries/{slug}", timeout=15).json()["views"]
        v2 = requests.get(f"{API}/entries/{slug}", timeout=15).json()["views"]
        assert v2 == v1 + 1

    def test_og_image_is_png(self):
        slug = requests.get(f"{API}/entries", timeout=15).json()["items"][0]["slug"]
        r = requests.get(f"{API}/entries/{slug}/og.png", timeout=15)
        assert r.status_code == 200
        assert r.headers["content-type"] == "image/png"
        assert r.content[:8] == b"\x89PNG\r\n\x1a\n"

    def test_sitemap_xml(self):
        r = requests.get(f"{BASE_URL}/sitemap.xml", timeout=15)
        assert r.status_code == 200 and "urlset" in r.text
        assert requests.get(f"{API}/sitemap.xml", timeout=15).status_code == 200


# ----------------- Appeals + Audit log -----------------
class TestAppealsAndAudit:
    def test_appeal_surfaces_to_moderator(self):
        slug = requests.get(f"{API}/entries", timeout=15).json()["items"][0]["slug"]
        r = requests.post(
            f"{API}/entries/{slug}/appeal",
            json={"message": "TEST appeal — missing important context here", "email": "x@example.com"},
            timeout=15,
        )
        assert r.status_code == 200
        lst = requests.get(f"{API}/mod/appeals", headers=AUTH, timeout=15)
        assert lst.status_code == 200
        assert any(a["slug"] == slug and a["message"].startswith("TEST appeal") for a in lst.json()["items"])

    def test_appeal_short_message_422(self):
        slug = requests.get(f"{API}/entries", timeout=15).json()["items"][0]["slug"]
        r = requests.post(f"{API}/entries/{slug}/appeal", json={"message": "short"}, timeout=15)
        assert r.status_code == 422

    def test_audit_records_approve_with_actor(self):
        payload = {
            "company_name": "TEST_Audit",
            "person_name": "TEST Auditor",
            "quote": "Auditing every keystroke builds a culture of glorious trust.",
            "sources": [{"label": "Memo", "url": "https://example.com/audit-memo"}],
            "tags": ["TEST_Tag"],
        }
        eid = requests.post(f"{API}/submissions", json=payload, timeout=15).json()["id"]
        requests.post(f"{API}/mod/entries/{eid}/approve", json={"red_flag_score": 2}, headers=AUTH, timeout=15)

        audit = requests.get(f"{API}/mod/audit", headers=AUTH, timeout=15).json()["items"]
        match = [x for x in audit if x["action"] == "approve" and x["target_id"] == eid]
        assert match, "approve action should be in the audit log"
        assert match[0]["actor"] == "qa.mod@example.com"

        # cleanup: remove from public listing
        requests.post(f"{API}/mod/entries/{eid}/reject", json={"rejection_reason": "test cleanup"}, headers=AUTH, timeout=15)

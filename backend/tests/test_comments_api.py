"""Backend tests for Social Comment Reply Manager."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://comment-auto-reply-1.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"


@pytest.fixture(scope="module")
def client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module", autouse=True)
def ensure_seeded(client):
    # Idempotent seed
    client.post(f"{API}/seed-demo", timeout=20)


# ─── Root/Stats/Platforms ───
class TestRoot:
    def test_root(self, client):
        r = client.get(f"{API}/", timeout=15)
        assert r.status_code == 200
        assert "message" in r.json()

    def test_stats_structure(self, client):
        r = client.get(f"{API}/stats", timeout=15)
        assert r.status_code == 200
        data = r.json()
        for key in ["total_pending", "total_approved_today", "total_accounts", "total_skipped"]:
            assert key in data
            assert isinstance(data[key], int)
        assert data["total_accounts"] >= 4

    def test_platforms(self, client):
        r = client.get(f"{API}/platforms", timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 4
        names = {p["platform"] for p in data}
        assert names == {"youtube", "instagram", "facebook", "tiktok"}
        for p in data:
            assert "configured" in p and "accounts" in p


# ─── Comments ───
class TestComments:
    def test_get_pending_comments(self, client):
        r = client.get(f"{API}/comments", params={"status": "pending"}, timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) > 0
        c = data[0]
        for key in ["id", "account_id", "platform", "commenter_name", "comment_text", "ai_draft", "status"]:
            assert key in c
        assert c["status"] == "pending"

    def test_filter_by_account(self, client):
        r = client.get(f"{API}/comments", params={"account_id": "demo-yt-1", "status": "pending"}, timeout=15)
        assert r.status_code == 200
        for c in r.json():
            assert c["account_id"] == "demo-yt-1"

    def test_edit_draft_and_persist(self, client):
        r = client.get(f"{API}/comments", params={"status": "pending"}, timeout=15)
        comments = r.json()
        assert len(comments) > 0
        cid = comments[0]["id"]
        new_text = "TEST_EDITED_DRAFT_" + cid[:6]
        e = client.put(f"{API}/comments/{cid}/edit", json={"draft": new_text}, timeout=15)
        assert e.status_code == 200
        # Verify persist
        g = client.get(f"{API}/comments", params={"status": "pending"}, timeout=15)
        found = next((c for c in g.json() if c["id"] == cid), None)
        assert found is not None
        assert found["ai_draft"] == new_text

    def test_skip_comment(self, client):
        r = client.get(f"{API}/comments", params={"status": "pending", "account_id": "demo-ig-1"}, timeout=15)
        comments = r.json()
        if not comments:
            pytest.skip("no pending for demo-ig-1")
        cid = comments[0]["id"]
        s = client.post(f"{API}/comments/{cid}/skip", timeout=15)
        assert s.status_code == 200
        # Verify no longer in pending
        g = client.get(f"{API}/comments", params={"status": "pending"}, timeout=15)
        assert all(c["id"] != cid for c in g.json())
        # Verify in skipped
        sk = client.get(f"{API}/comments", params={"status": "skipped"}, timeout=15)
        assert any(c["id"] == cid for c in sk.json())

    def test_approve_comment(self, client):
        r = client.get(f"{API}/comments", params={"status": "pending", "account_id": "demo-fb-1"}, timeout=15)
        comments = r.json()
        if not comments:
            pytest.skip("no pending for demo-fb-1")
        cid = comments[0]["id"]
        a = client.post(f"{API}/comments/{cid}/approve", timeout=30)
        assert a.status_code == 200
        assert a.json().get("success") is True
        g = client.get(f"{API}/comments", params={"status": "approved"}, timeout=15)
        assert any(c["id"] == cid for c in g.json())

    def test_regenerate_no_groq(self, client):
        r = client.get(f"{API}/comments", params={"status": "pending"}, timeout=15)
        comments = r.json()
        if not comments:
            pytest.skip("no pending")
        cid = comments[0]["id"]
        rg = client.post(f"{API}/comments/{cid}/regenerate", timeout=30)
        # Even without GROQ key, endpoint should return 200 with placeholder
        assert rg.status_code == 200
        assert "new_draft" in rg.json()

    def test_approve_all(self, client):
        # Approve all pending for demo-tt-1
        r = client.post(f"{API}/comments/approve-all", params={"account_id": "demo-tt-1"}, timeout=30)
        assert r.status_code == 200
        assert "approved_count" in r.json()
        # Verify none pending for that account
        g = client.get(f"{API}/comments", params={"status": "pending", "account_id": "demo-tt-1"}, timeout=15)
        assert g.json() == []

    def test_seed_idempotent(self, client):
        r = client.post(f"{API}/seed-demo", timeout=15)
        assert r.status_code == 200
        assert r.json().get("seeded") is False

    def test_404_approve_invalid_id(self, client):
        r = client.post(f"{API}/comments/nonexistent-id-xxx/approve", timeout=15)
        assert r.status_code == 404

    def test_404_edit_invalid_id(self, client):
        r = client.put(f"{API}/comments/nonexistent-id-xxx/edit", json={"draft": "x"}, timeout=15)
        assert r.status_code == 404

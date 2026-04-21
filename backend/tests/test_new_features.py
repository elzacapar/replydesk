"""Iteration 3: tone presets, auto_liked/sentiment, toggle-like, ReplyDesk rename, async Groq sentiment."""
import os
import asyncio
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://comment-auto-reply-1.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"


@pytest.fixture(scope="module")
def client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    s.post(f"{API}/seed-demo", timeout=20)
    return s


# ─── Rename to ReplyDesk ───
class TestReplyDeskRename:
    def test_root_returns_replydesk(self, client):
        r = client.get(f"{API}/", timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert data.get("message") == "ReplyDesk API"


# ─── Tone Preset endpoint ───
class TestTonePreset:
    def test_platforms_expose_tone_preset(self, client):
        r = client.get(f"{API}/platforms", timeout=15)
        assert r.status_code == 200
        for p in r.json():
            for a in p["accounts"]:
                assert "tone_preset" in a
                assert a["tone_preset"] in ["casual", "professional", "witty", "warm"]

    def test_update_tone_valid(self, client):
        r = client.put(f"{API}/accounts/demo-yt-1/tone", json={"tone_preset": "witty"}, timeout=15)
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert body["tone_preset"] == "witty"
        p = client.get(f"{API}/platforms", timeout=15).json()
        yt = next(x for x in p if x["platform"] == "youtube")
        acct = next(a for a in yt["accounts"] if a["id"] == "demo-yt-1")
        assert acct["tone_preset"] == "witty"

    def test_update_tone_all_presets(self, client):
        for tone in ["casual", "professional", "witty", "warm"]:
            r = client.put(f"{API}/accounts/demo-ig-1/tone", json={"tone_preset": tone}, timeout=15)
            assert r.status_code == 200
            assert r.json()["tone_preset"] == tone

    def test_update_tone_invalid(self, client):
        r = client.put(f"{API}/accounts/demo-yt-1/tone", json={"tone_preset": "sarcastic"}, timeout=15)
        assert r.status_code == 400
        assert "Invalid tone" in r.json().get("detail", "")

    def test_update_tone_account_not_found(self, client):
        r = client.put(f"{API}/accounts/does-not-exist/tone", json={"tone_preset": "warm"}, timeout=15)
        assert r.status_code == 404


# ─── Auto-like / Sentiment fields ───
class TestAutoLikeSentiment:
    def test_comments_have_auto_liked_and_sentiment(self, client):
        r = client.get(f"{API}/comments", params={"status": "pending"}, timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert len(data) > 0
        for c in data:
            assert "auto_liked" in c
            assert "sentiment" in c
            assert isinstance(c["auto_liked"], bool)
            assert c["sentiment"] in ["positive", "negative", "neutral", ""]

    def test_demo_comments_positive(self, client):
        r = client.get(f"{API}/comments", params={"status": "pending"}, timeout=15)
        data = r.json()
        demo = [c for c in data if c["account_id"].startswith("demo-")]
        assert len(demo) > 0
        for c in demo:
            assert c["auto_liked"] is True
            assert c["sentiment"] == "positive"


# ─── Toggle-Like endpoint (new in iteration 3) ───
class TestToggleLike:
    def _get_demo_comment_id(self, client):
        r = client.get(f"{API}/comments", params={"status": "pending"}, timeout=15)
        comments = r.json()
        demo = [c for c in comments if c["account_id"].startswith("demo-")]
        assert demo, "No demo pending comments to test toggle-like"
        return demo[0]["id"], demo[0]["auto_liked"]

    def test_toggle_like_flips_value(self, client):
        cid, initial_liked = self._get_demo_comment_id(client)
        # Toggle 1
        r1 = client.post(f"{API}/comments/{cid}/toggle-like", timeout=15)
        assert r1.status_code == 200
        body1 = r1.json()
        assert body1["success"] is True
        assert body1["auto_liked"] == (not initial_liked)

        # Verify persisted via GET
        g = client.get(f"{API}/comments", params={"status": "pending"}, timeout=15).json()
        found = next((c for c in g if c["id"] == cid), None)
        assert found is not None
        assert found["auto_liked"] == (not initial_liked)

        # Toggle 2 - should flip back
        r2 = client.post(f"{API}/comments/{cid}/toggle-like", timeout=15)
        assert r2.status_code == 200
        body2 = r2.json()
        assert body2["auto_liked"] == initial_liked

        # Verify persisted
        g2 = client.get(f"{API}/comments", params={"status": "pending"}, timeout=15).json()
        found2 = next((c for c in g2 if c["id"] == cid), None)
        assert found2["auto_liked"] == initial_liked

    def test_toggle_like_404_for_nonexistent(self, client):
        r = client.post(f"{API}/comments/nonexistent-id-xxx/toggle-like", timeout=15)
        assert r.status_code == 404


# ─── detect_sentiment is async and uses Groq (falls back to 'positive' when no key) ───
class TestSentimentFn:
    def test_detect_sentiment_is_async_and_returns_valid(self):
        import sys, pathlib, inspect
        sys.path.insert(0, str(pathlib.Path("/app/backend")))
        from services.groq_service import detect_sentiment, TONE_PRESETS

        # Must be a coroutine function (async)
        assert inspect.iscoroutinefunction(detect_sentiment), "detect_sentiment must be async"

        # Call it with await
        result = asyncio.get_event_loop().run_until_complete(detect_sentiment("Amazing work, loved it!"))
        assert result in ("positive", "neutral", "negative")

        # TONE_PRESETS still present with expected keys
        assert set(TONE_PRESETS.keys()) == {"casual", "professional", "witty", "warm"}

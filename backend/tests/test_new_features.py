"""Iteration 2: Tests for tone presets + auto_liked/sentiment fields."""
import os
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
        # set to witty
        r = client.put(f"{API}/accounts/demo-yt-1/tone", json={"tone_preset": "witty"}, timeout=15)
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert body["tone_preset"] == "witty"
        # Verify persist via platforms
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


# ─── Auto-like / Sentiment ───
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
            assert c["sentiment"] in ["positive", "negative", ""]

    def test_demo_comments_positive(self, client):
        # All seeded demo comments should be auto_liked with positive sentiment
        r = client.get(f"{API}/comments", params={"status": "pending"}, timeout=15)
        data = r.json()
        demo = [c for c in data if c["account_id"].startswith("demo-")]
        assert len(demo) > 0
        for c in demo:
            assert c["auto_liked"] is True
            assert c["sentiment"] == "positive"


# ─── Sentiment detection unit-ish via module import ───
class TestSentimentFn:
    def test_detect_negative_and_positive(self):
        import sys, pathlib
        sys.path.insert(0, str(pathlib.Path("/app/backend")))
        from services.groq_service import detect_sentiment, TONE_PRESETS, NEGATIVE_KEYWORDS
        assert detect_sentiment("I hate this video, it sucks") == "negative"
        assert detect_sentiment("This is awful, total garbage") == "negative"
        assert detect_sentiment("Amazing work, loved it!") == "positive"
        assert set(TONE_PRESETS.keys()) == {"casual", "professional", "witty", "warm"}
        assert "hate" in NEGATIVE_KEYWORDS

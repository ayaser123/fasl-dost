"""End-to-end through FastAPI with a scripted fake model (no network, no API key)."""
from types import SimpleNamespace as NS

from fastapi.testclient import TestClient

from server import advisor, main, weather


def block(name, inp, id_="t1"):
    return NS(type="tool_use", name=name, input=inp, id=id_)


def script(*turns):
    it = iter(turns)

    async def fake(**kw):
        return NS(stop_reason="tool_use", content=next(it))
    return fake


async def no_weather(loc):
    return None


def setup(monkeypatch, *turns):
    monkeypatch.setattr(advisor, "_create", script(*turns))
    monkeypatch.setattr(weather, "get_weather", no_weather)
    main.SESSIONS.clear()
    return TestClient(main.app)


def test_ask_then_advise(monkeypatch):
    ask = {"action": "ask", "language": "ur", "confidence": "low", "spoken_summary": "کیا دھبے لکیروں میں ہیں؟",
           "questions": ["کیا دھبے لکیروں میں ہیں؟"]}
    advise = {"action": "advise", "language": "ur", "confidence": "medium", "spoken_summary": "زرد کنگی",
              "likely_issue": "زرد کنگی", "steps": [{"title": "معائنہ", "detail": "10 پودے دیکھیں"}],
              "sources": ["wheat-yellow-rust", "not-retrieved"]}
    c = setup(monkeypatch,
              [block("respond", ask)],
              [block("search_guidance", {"query": "yellow stripes wheat"}, "a"),
               block("get_weather", {"location": "Multan"}, "b")],
              [block("respond", advise, "c")])
    r1 = c.post("/api/advise", data={"text": "گندم کے پتوں پر پیلے دھبے", "crop": "Wheat"}).json()
    assert r1["action"] == "ask" and len(r1["questions"]) == 1
    r2 = c.post("/api/advise", data={"session_id": r1["session_id"], "text": "ہاں لکیروں میں"}).json()
    assert r2["action"] == "advise"
    assert r2["sources"] == ["wheat-yellow-rust"]  # invented citation dropped


def test_unretrieved_advice_becomes_referral(monkeypatch):
    advise = {"action": "advise", "language": "pa", "confidence": "high", "spoken_summary": "x",
              "steps": [{"title": "a", "detail": "b"}], "sources": ["wheat-yellow-rust"]}
    c = setup(monkeypatch, [block("respond", advise)])  # never searched
    r = c.post("/api/advise", data={"text": "پتے پیلے"}).json()
    assert r["action"] == "refer" and r["language"] == "pa" and "ایکسٹینشن" in r["spoken_summary"]


def test_model_refusal_refers(monkeypatch):
    async def refuse(**kw):
        return NS(stop_reason="refusal", content=[])
    monkeypatch.setattr(advisor, "_create", refuse)
    main.SESSIONS.clear()
    r = TestClient(main.app).post("/api/advise", data={"text": "x"}).json()
    assert r["action"] == "refer"


def test_empty_input(monkeypatch):
    assert setup(monkeypatch).post("/api/advise", data={}).json()["error"] == "empty"

from server import knowledge
from server.guardrails import enforce


def test_retrieval_rust():
    hits = knowledge.search("yellow stripes powder on wheat leaves rust", "wheat")
    assert hits[0]["id"] == "wheat-yellow-rust"


def test_retrieval_crop_filter():
    assert all(h["id"].startswith(("wheat", "general")) for h in knowledge.search("leaf", "wheat"))


def adv(**k):
    return {"action": "advise", "language": "ur", "confidence": "high", "spoken_summary": "x",
            "steps": [{"title": "t", "detail": "d"}], "sources": ["wheat-yellow-rust"], **k}


def test_advice_ok():
    assert enforce(adv(), {"wheat-yellow-rust"}, 0)["action"] == "advise"


def test_uncited_or_invented_source_refers():
    assert enforce(adv(), set(), 0)["action"] == "refer"


def test_low_confidence_refers():
    assert enforce(adv(confidence="low"), {"wheat-yellow-rust"}, 0)["action"] == "refer"


def test_clarify_limit():
    r = {"action": "ask", "language": "pa", "questions": ["a", "b", "c"]}
    assert enforce(r, set(), 1)["questions"] == ["a", "b"]
    assert enforce(r, set(), 2)["action"] == "refer"

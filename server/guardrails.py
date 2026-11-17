"""Deterministic checks applied AFTER the model answers.

The model is never the only safeguard against over-confident advice.
"""

MAX_CLARIFY_ROUNDS = 2

REFER = {
    "ur": "میں تصویر اور تفصیل سے مسئلے کی پکی پہچان نہیں کر سکتا۔ اندازے سے دوا چھڑکنے کی بجائے براہِ کرم اپنے علاقے کے زرعی توسیعی کارکن (ایکسٹینشن ورکر) سے رابطہ کریں اور ممکن ہو تو پودے کا نمونہ ساتھ لے جائیں۔",
    "pa": "میں تصویر تے دسی گئی گل توں مسئلے دی پکی پچھان نہیں کر سکدا۔ اندازے نال سپرے کرن دی بجائے مہربانی کر کے اپنے علاقے دے زرعی توسیعی کارکن (ایکسٹینشن ورکر) نال رابطہ کرو تے ہو سکے تے پودے دا نمونہ نال لے جاؤ۔",
}


def enforce(result: dict, retrieved_ids: set, clarify_rounds: int) -> dict:
    """Return a safe version of the model's structured answer."""
    r = dict(result)
    lang = r.get("language") if r.get("language") in REFER else "ur"
    r["language"] = lang
    # only citations that were actually retrieved this turn
    r["sources"] = [s for s in r.get("sources", []) if s in retrieved_ids]
    r["questions"] = (r.get("questions") or [])[:2]

    if r.get("action") == "ask":
        if clarify_rounds >= MAX_CLARIFY_ROUNDS or not r["questions"]:
            return _refer(r, lang, "clarification limit reached")
        return r

    if r.get("action") == "advise":
        if not r["sources"]:
            return _refer(r, lang, "no trusted guidance matched")
        if r.get("confidence") not in ("high", "medium"):
            return _refer(r, lang, "low confidence")
        if not r.get("steps"):
            return _refer(r, lang, "no actionable steps")
        return r

    return _refer(r, lang, r.get("refer_reason") or "model referred")


def _refer(r: dict, lang: str, why: str) -> dict:
    keep = r.get("spoken_summary") if r.get("action") == "refer" and r.get("spoken_summary") else REFER[lang]
    return {"action": "refer", "language": lang, "spoken_summary": keep,
            "refer_reason": why, "confidence": "low", "steps": [], "questions": [],
            "likely_issue": "", "safety_note": "", "sources": r.get("sources", [])}

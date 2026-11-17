# Fasl Dost (فصل دوست) — voice-first crop advisor

Farmer sends a voice note (Urdu/Punjabi) and optionally a photo → assistant asks up to 2 clarifying
questions → checks local guidance + weather → replies briefly, in the same language, as text and audio.
If it can't identify the problem reliably it says so and refers the farmer to an agriculture extension worker.

## Run

```
pip install -r requirements.txt
set ANTHROPIC_API_KEY=...        # or `ant auth login`
python -m uvicorn server.main:app --port 8000
# open http://localhost:8000
```

Env: `FASL_MODEL` (default `claude-opus-5-5`), `FASL_FALLBACKS=0` to disable the server-side refusal
fallback beta, `FASL_WHISPER` (faster-whisper size, default `small`).
Tests (no network/API key needed): `python -m pytest`.

## Flow

```
mic/photo/text → /api/advise
   faster-whisper (ur/pa) ──► transcript
   Claude tool loop: search_guidance (local KB) · get_weather (Open-Meteo) · respond
   guardrails.enforce()  ──► ask | advise | refer
   /api/tts (edge-tts, ur-PK voice) ──► audio
```

## Safety design

- Advice must cite guidance ids that were **actually retrieved** this turn; invented citations are dropped, and
  advice with no valid citation, low confidence, or no steps is converted to a **referral** in code
  (`server/guardrails.py`), not just by prompt.
- Max 2 clarification rounds, then advise or refer.
- No pesticide dose/brand from memory: points to label and extension office.
- Transcript and photo are treated as data, not instructions. Refusals fall back to a referral.
- The UI shows the transcript so a mis-heard voice note is visible.

## Before real farmers use it (important)

1. **The knowledge base is a draft.** `server/knowledge/*.md` is written from general agronomy and marked
   `status: draft-needs-expert-review` with placeholder sources. Replace with excerpts of official bulletins
   (PARC/NARC, provincial agriculture departments) and have an agronomist review it. Set the helpline number
   in the UI footer (currently a placeholder link).
2. **Measure ASR on real farmer audio** (Whisper is weaker on Urdu and especially Punjabi, noisy fields,
   dialects). Build a small labeled set and evaluate transcript + end-to-end referral rate.
3. **TTS:** no Pakistani-Punjabi neural voice exists; Punjabi replies use the Urdu voice.
4. Add an eval set of cases that must refer (blurry photo, unlisted crop, conflicting symptoms).
5. Sessions are in memory; add persistence/rate limiting/auth before deploying. Delivery via WhatsApp/IVR is a
   natural next channel (the `/api/advise` contract is channel-agnostic).

import edge_tts

# No Pakistani-Punjabi neural voice exists; Urdu voice is the closest intelligible fallback.
VOICES = {"ur": "ur-PK-UzmaNeural", "pa": "ur-PK-UzmaNeural"}


async def synth(text: str, lang: str) -> bytes:
    out = b""
    async for ch in edge_tts.Communicate(text, VOICES.get(lang, VOICES["ur"])).stream():
        if ch["type"] == "audio":
            out += ch["data"]
    return out

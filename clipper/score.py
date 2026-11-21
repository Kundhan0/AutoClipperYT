"""Stage 2 - the editor. Calls your local Claude gateway to pick the best moments."""
from __future__ import annotations
import json
import os
import requests
from .config import Config

# ── Gateway wiring ────────────────────────────────────────────────────────────
# Your gateway speaks Anthropic Messages API at http://127.0.0.1:8000/v1/messages
# Set GATEWAY_URL / GATEWAY_MODEL in .env to override.
_GATEWAY_URL   = os.environ.get("GATEWAY_URL",   "http://127.0.0.1:8000")
_GATEWAY_MODEL = os.environ.get("GATEWAY_MODEL", "claude-sonnet-4-5")

_SYSTEM = (
    "You are a sharp short-form video editor. You are given a timestamped transcript. "
    "Pick the {n} strongest standalone moments to cut as vertical shorts. "
    "Each clip must START and END on a natural sentence boundary, make sense without "
    "surrounding context, and run between {lo:.0f} and {hi:.0f} seconds. Favor a strong "
    "hook in the first seconds, a complete thought, and a clear payoff. "
    "Also write a punchy <=8 word on-screen headline ('hook') and a 'score' from 0-100 "
    "predicting its short-form virality. "
    "Return STRICT JSON only, no prose, in this exact shape:\n"
    '{{"clips":[{{"start":<seconds>,"end":<seconds>,"title":"<=6 words",'
    '"hook":"<=8 words","reason":"why it lands","score":<integer 0-100>}}]}}'
)


def _timed_block(words: list[dict], chunk: int = 12) -> str:
    """Compact timestamped transcript: each line prefixed with its start time."""
    lines, buf, t0 = [], [], None
    for w in words:
        if t0 is None:
            t0 = w["start"]
        buf.append(w["word"])
        if len(buf) >= chunk:
            lines.append(f"[{t0:7.2f}] {' '.join(buf)}")
            buf, t0 = [], None
    if buf:
        lines.append(f"[{t0:7.2f}] {' '.join(buf)}")
    return "\n".join(lines)


def _coerce(raw: str) -> list[dict]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        start, end = raw.find("{"), raw.rfind("}")
        if start == -1 or end == -1:
            return []
        try:
            data = json.loads(raw[start:end + 1])
        except json.JSONDecodeError:
            return []
    return data.get("clips", []) if isinstance(data, dict) else []


def _clean(clips: list[dict], duration: float, cfg: Config) -> list[dict]:
    out = []
    for c in clips:
        try:
            s, e = float(c["start"]), float(c["end"])
        except (KeyError, TypeError, ValueError):
            continue
        s, e = max(0.0, s), min(duration, e)
        if e - s < cfg.min_clip_s:
            continue
        if e - s > cfg.max_clip_s:
            e = s + cfg.max_clip_s
        try:
            sc = int(float(c.get("score", 50)))
        except (TypeError, ValueError):
            sc = 50
        sc = max(0, min(100, sc))
        title = str(c.get("title", "Clip"))[:60]
        hook = str(c.get("hook") or title)[:80]
        out.append({"start": round(s, 2), "end": round(e, 2),
                    "title": title, "hook": hook,
                    "reason": str(c.get("reason", ""))[:200], "score": sc})
    out.sort(key=lambda c: c["start"])
    # drop overlaps, keep the earlier
    deduped: list[dict] = []
    for c in out:
        if deduped and c["start"] < deduped[-1]["end"]:
            continue
        deduped.append(c)
    deduped.sort(key=lambda c: c["score"], reverse=True)
    return deduped[: cfg.num_clips]


def score(transcript: dict, cfg: Config) -> list[dict]:
    """Call your local Claude gateway (Anthropic Messages API) to pick the best clips."""
    system_msg = _SYSTEM.format(n=cfg.num_clips, lo=cfg.min_clip_s, hi=cfg.max_clip_s)
    user_msg   = "TRANSCRIPT:\n" + _timed_block(transcript["words"])

    last_err = None
    for attempt in range(2):
        try:
            resp = requests.post(
                f"{_GATEWAY_URL}/v1/messages",
                headers={"Content-Type": "application/json",
                         "anthropic-version": "2023-06-01",
                         "x-api-key": "local"},
                json={
                    "model":      _GATEWAY_MODEL,
                    "max_tokens": 2048,
                    "system":     system_msg,
                    "messages":   [{"role": "user", "content": user_msg}],
                },
                timeout=900,
            )
            resp.raise_for_status()
            # Anthropic response: {"content": [{"type": "text", "text": "..."}], ...}
            content_blocks = resp.json().get("content", [])
            raw_text = " ".join(
                blk.get("text", "") for blk in content_blocks
                if isinstance(blk, dict) and blk.get("type") == "text"
            )
            clips = _clean(_coerce(raw_text), transcript["duration"], cfg)
            if clips:
                return clips
        except requests.RequestException as exc:
            last_err = exc
    if last_err:
        raise RuntimeError(
            f"Could not reach gateway at {_GATEWAY_URL}: {last_err}\n"
            "Make sure your gateway is running: python claude_gateway/gateway.py"
        )
    return []

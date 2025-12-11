# bot/summarize.py
import os
os.environ["TRANSFORMERS_NO_TF"] = "1"
os.environ["USE_TF"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

from transformers import pipeline

# Light, fast model; you can swap to "facebook/bart-large-cnn" later
_sum_pipe = pipeline(
    "summarization",
    model="sshleifer/distilbart-cnn-12-6",
    framework="pt",
    device=-1
)

def _len_cfg(length: str):
    length = (length or "medium").lower()
    if length == "short":
        return dict(map_len=140, map_min=50, reduce_len=160, reduce_min=60)
    if length == "long":
        return dict(map_len=260, map_min=100, reduce_len=320, reduce_min=120)
    return dict(map_len=220, map_min=80, reduce_len=250, reduce_min=90)

def _summarize_once(text: str, max_len: int, min_len: int) -> str:
    text = (text or "").strip()
    if not text:
        return ""
    out = _sum_pipe(text, max_length=max_len, min_length=min_len, do_sample=False)[0]["summary_text"]
    return out.strip()

def chunk_messages(msgs: list[str], target_chars: int = 1000) -> list[str]:
    """
    Build chunks close to target_chars, respecting message boundaries
    so multiple topics don't get smashed together.
    """
    chunks, cur, curlen = [], [], 0
    for m in msgs:
        L = len(m) + 1
        if curlen and curlen + L > target_chars:
            chunks.append("\n".join(cur))
            cur, curlen = [], 0
        cur.append(m)
        curlen += L
    if cur:
        chunks.append("\n".join(cur))
    return chunks

async def summarize_messages_hierarchical(msgs: list[str], length: str = "medium") -> str:
    """
    Map-reduce summary over message windows, then ask the reducer to
    explicitly cover ALL topics + produce structured output.
    """
    cfg = _len_cfg(length)
    # 1) map over message windows
    chunks = chunk_messages(msgs, target_chars=1000)
    partials = []
    for ch in chunks:
        partials.append(_summarize_once(ch, max_len=cfg["map_len"], min_len=cfg["map_min"]))
    # 2) reduce with a stronger instruction so it keeps all themes
    if partials:
        # SIMPLIFIED - no verbose instructions
        combined_summaries = "\n".join([f"- {p}" for p in partials if p.strip()])
        reduce_prompt = f"Combine these points into one concise summary:\n{combined_summaries}"
        final = _summarize_once(reduce_prompt, max_len=cfg["reduce_len"], min_len=cfg["reduce_min"])
    else:
        final = "No content to summarize."
    return final
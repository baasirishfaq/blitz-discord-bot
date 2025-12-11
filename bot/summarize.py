# bot/summarize.py
import os
import requests
import asyncio

# Hugging Face Inference API
HF_API_URL = "https://api-inference.huggingface.co/models/sshleifer/distilbart-cnn-12-6"

def _summarize_once(text: str, max_len: int, min_len: int) -> str:
    """Call Hugging Face API for summarization."""
    text = (text or "").strip()
    if not text or len(text) < 30:
        return ""
    
    # Get API key from environment
    api_key = os.getenv("HF_TOKEN", "")
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    
    try:
        response = requests.post(
            HF_API_URL,
            headers=headers,
            json={
                "inputs": text,
                "parameters": {
                    "max_length": max_len,
                    "min_length": min_len,
                    "do_sample": False
                }
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0]['summary_text'].strip()
        
        # If API fails, return original or truncated text
        if len(text) > 200:
            return text[:197] + "..."
        return text
        
    except Exception:
        # Fallback if API is down
        if len(text) > 150:
            return text[:147] + "..."
        return text

def _len_cfg(length: str):
    """Configure summary length parameters."""
    length = (length or "medium").lower()
    if length == "short":
        return dict(map_len=120, map_min=40, reduce_len=140, reduce_min=50)
    if length == "long":
        return dict(map_len=200, map_min=80, reduce_len=250, reduce_min=90)
    return dict(map_len=180, map_min=60, reduce_len=200, reduce_min=70)

def chunk_messages(msgs: list[str], target_chars: int = 800) -> list[str]:
    """
    Build chunks respecting message boundaries.
    Smaller target for API limits.
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
    Map-reduce summary using Hugging Face API.
    Optimized for API rate limits.
    """
    if not msgs:
        return "No messages to summarize."
    
    # If very short, summarize directly
    total_chars = sum(len(m) for m in msgs)
    if total_chars < 400:
        combined = "\n".join(msgs)
        cfg = _len_cfg(length)
        return _summarize_once(combined, max_len=cfg["reduce_len"], min_len=cfg["reduce_min"])
    
    cfg = _len_cfg(length)
    chunks = chunk_messages(msgs, target_chars=800)
    
    # Process chunks with small delay to respect API limits
    partials = []
    for i, ch in enumerate(chunks):
        if ch.strip():
            summary = _summarize_once(ch, max_len=cfg["map_len"], min_len=cfg["map_min"])
            if summary and summary.strip():
                partials.append(summary)
            # Small delay between API calls
            if i < len(chunks) - 1:
                await asyncio.sleep(0.5)
    
    if not partials:
        return "Could not generate summary."
    
    if len(partials) == 1:
        return partials[0]
    
    # Combine partial summaries
    combined = " ".join(partials)
    if len(combined) > 1000:
        combined = combined[:997] + "..."
    
    final = _summarize_once(combined, max_len=cfg["reduce_len"], min_len=cfg["reduce_min"])
    return final if final else " ".join(partials[:2])  # Fallback
import datetime as dt
import discord

async def collect_messages_text(channel: discord.abc.Messageable, hours_back: int = 24, max_messages: int = 1500):
    """(legacy) Return one big string."""
    msgs = await collect_messages(channel, hours_back=hours_back, max_messages=max_messages)
    return "\n".join(msgs)

async def collect_messages(channel: discord.abc.Messageable, hours_back: int = 24, max_messages: int = 1500):
    """
    Return a list[str] of messages as 'author: content', oldest→newest.
    This preserves boundaries so summarizer can window them.
    """
    if not hasattr(channel, "history"):
        return []
    after = dt.datetime.utcnow() - dt.timedelta(hours=hours_back)
    items = []
    async for m in channel.history(after=after, limit=None, oldest_first=True):
        if m.author.bot:
            continue
        content = (m.content or "").replace("\r", "").strip()
        if not content:
            continue
        items.append(f"{m.author.display_name}: {content}")
        if len(items) >= max_messages:
            break
    return items

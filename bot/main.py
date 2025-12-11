# bot/main.py
import os
import time
import asyncio
from collections import defaultdict
import discord
from discord import app_commands
from dotenv import load_dotenv

from collectors import collect_messages
from summarize import summarize_messages_hierarchical
from formatters import format_summary
from keep_alive import keep_alive

# Load environment variables FIRST
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", "0"))

# Rate limiting setup
user_cooldown = defaultdict(float)
COOLDOWN_SECONDS = 60

def check_rate_limit(user_id: int) -> bool:
    now = time.time()
    if now - user_cooldown[user_id] < COOLDOWN_SECONDS:
        return False
    user_cooldown[user_id] = now
    return True

# Discord setup
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

class SummarizerClient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        if GUILD_ID:
            guild = discord.Object(id=GUILD_ID)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()

client = SummarizerClient()

DETAIL_CHOICES = [
    app_commands.Choice(name="short", value="short"),
    app_commands.Choice(name="medium", value="medium"),
    app_commands.Choice(name="long", value="long"),
]

@client.tree.command(name="summarize", description="Summarize recent chat")
@app_commands.describe(hours="How many hours back (default 24)", detail="Summary length")
@app_commands.choices(detail=DETAIL_CHOICES)
async def summarize(interaction: discord.Interaction, hours: int = 24, detail: app_commands.Choice[str] = None):
    # Rate limit check
    if not check_rate_limit(interaction.user.id):
        await interaction.response.send_message("Please wait 60 seconds before using this command again.", ephemeral=True)
        return
    
    await interaction.response.defer(thinking=True, ephemeral=False)
    channel = interaction.channel
    length = (detail.value if detail else "medium")

    try:
        msgs = await collect_messages(channel, hours_back=hours, max_messages=1500)
        if not msgs:
            await interaction.followup.send("No messages found in that window.")
            return

        # Add timeout for summarization
        try:
            summary = await asyncio.wait_for(
                summarize_messages_hierarchical(msgs, length=length),
                timeout=45.0
            )
        except asyncio.TimeoutError:
            await interaction.followup.send("❌ Summary took too long. Try fewer hours or a less busy channel.", ephemeral=True)
            return

        reply = format_summary(summary) + f"\n\n_(processed {len(msgs)} messages)_"
        await interaction.followup.send(reply)
    except discord.Forbidden:
        await interaction.followup.send("I don't have permission to read this channel.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"Error: {type(e).__name__}", ephemeral=True)

@client.tree.command(name="summarize_text", description="Summarize pasted text (multi-topic friendly)")
@app_commands.describe(text="Paste text (use blank lines between topics)", detail="Summary length")
@app_commands.choices(detail=DETAIL_CHOICES)
async def summarize_text_cmd(interaction: discord.Interaction, text: str, detail: app_commands.Choice[str] = None):
    # Rate limit check for this command too
    if not check_rate_limit(interaction.user.id):
        await interaction.response.send_message("Please wait 60 seconds before using this command again.", ephemeral=True)
        return
    
    await interaction.response.defer(thinking=True, ephemeral=False)
    length = (detail.value if detail else "medium")

    # split on blank lines so each topic becomes its own 'message'
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paras:
        await interaction.followup.send("Nothing to summarize.")
        return

    msgs = [f"user: {p}" for p in paras]
    
    # Add timeout for summarization
    try:
        summary = await asyncio.wait_for(
            summarize_messages_hierarchical(msgs, length=length),
            timeout=45.0
        )
    except asyncio.TimeoutError:
        await interaction.followup.send("❌ Summary took too long. Try shorter text.", ephemeral=True)
        return
    
    await interaction.followup.send(format_summary(summary) + f"\n\n_(processed {len(msgs)} sections)_")

@client.event
async def on_ready():
    print("Logged in as", client.user)
    print("Guilds:", [g.name for g in client.guilds])

if __name__ == "__main__":
    if not TOKEN:
        raise RuntimeError("Missing DISCORD_TOKEN in .env")
    keep_alive()  # Start the web server
    client.run(TOKEN)
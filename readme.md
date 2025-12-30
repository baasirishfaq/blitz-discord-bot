# 🤖 Discord AI Summarizer Bot

An intelligent Discord bot that summarizes conversations using **Hugging Face’s DistilBART model** via API. Built with **Python** and **discord.py**, featuring topic-aware and hierarchical summarization.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Discord.py](https://img.shields.io/badge/discord.py-2.0+-7289DA.svg)
![Hugging Face](https://img.shields.io/badge/🤗%20Hugging%20Face-API-FFD166.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

## ✨ Features

- 📝 **AI-Powered Summarization** using DistilBART-CNN-12-6  
- 🗣️ **Conversation-Aware** (preserves topic boundaries)  
- ⚡ **Slash Commands** (`/summarize`, `/summarize_text`)  
- 📊 **Adjustable Detail** (short / medium / long)  
- 🔒 **Rate Limiting** (60s per user)  
- 🌐 **API-Based** (no local model storage)  
- 🚀 **24/7 Deployment** on Replit  

---

## 🤖 Commands

### `/summarize`
Summarize recent messages in the current channel.

**Options**
- `hours` (1–24, default 12)
- `detail` (`short`, `medium`, `long`)

```

/summarize hours:6 detail:short

```

### `/summarize_text`
Summarize pasted text (supports multi-topic input).

```

/summarize_text text:First topic...

Second topic...
detail:long

```

---

## 🏗️ Project Structure

```

bot/
├── main.py          # Discord client & commands
├── summarize.py     # Hierarchical summarization
├── collectors.py    # Message fetching
├── formatters.py    # Output formatting
├── keep_alive.py    # Replit uptime
requirements.txt
.env.example

````

---

## 🚀 Quick Start

### 1. Clone
```bash
git clone https://github.com/baasirishfaq/blitz-discord-bot.git
cd blitz-discord-bot
````

### 2. Install

```bash
pip install -r requirements.txt
```

### 3. Environment Variables

Create `.env`:

```env
DISCORD_TOKEN=your_discord_bot_token
HF_TOKEN=your_huggingface_api_token
GUILD_ID=optional_server_id
```

### 4. Run

```bash
python bot/main.py
```

---

## 🌐 Deployment (Replit)

1. Import repo into Replit
2. Add Secrets:

   * `DISCORD_TOKEN`
   * `HF_TOKEN`

3. **Run**
---

## ⚙️ Tech Stack

* **Python 3.8+**
* **discord.py 2.0+**
* **Hugging Face Inference API**
* **DistilBART-CNN-12-6**

---

## 📊 Example Output

```
TL;DR:
The team discussed project deadlines and task ownership.
Backend, frontend, and documentation responsibilities were assigned,
with testing planned before Friday.

(processed 47 messages from last 6 hours)

----
## 📈 Future Improvements

* Thread summarization
* Scheduled daily/weekly summaries
* Multi-language support
* Sentiment analysis
* Web dashboard

---

**Star this repo if you find it useful**
Built by **Baasir Ishfaq**


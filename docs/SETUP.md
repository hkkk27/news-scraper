# Setup guide

Everything is optional except step 1; each feature switches on when its secret is added.
Secrets go in **GitHub → repository → Settings → Secrets and variables → Actions → New
repository secret**. For local runs, put the same names in a `.env` file (see `.env.example`).

| Step | What you get | Time |
|---|---|---|
| 1. Local run | Reports and dashboard on your computer | 10 min |
| 2. Telegram bot | Morning brief, training buttons, forward-to-add | 10 min |
| 3. Email | Brief to leadership, digest + Excel to analysts | 10 min |
| 4. Dashboard online | Private dashboard with email login | 20 min |
| 5. AI relevance (OpenRouter, free) | The AI settles items the rules are unsure about | 5 min |

The scheduled pipeline (`.github/workflows/tracker.yml`) is already live on GitHub. It runs
every 2 hours even before any secrets exist.

---

## 1. Run it locally

Requires Python 3.11 or newer.

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt       # Windows; on macOS/Linux: .venv/bin/pip
.venv/Scripts/python -m tracker run                 # watch pages, collect, tag, score, cluster, dashboard
.venv/Scripts/python -m tracker report daily        # brief, digest, Excel, Telegram text → output/reports/
```

Open `output/site/index.html` (dashboard) and `output/reports/daily-<date>/executive-brief.html`.

Other useful commands:

| Command | Does |
|---|---|
| `python -m tracker sources check` | Test every feed (ok / quiet / failing) |
| `python -m tracker watch` | Check the government notice pages only |
| `python -m tracker train` | Retrain the relevance model from feedback |
| `python -m tracker report weekly` | Weekly report with Excel |
| `python -m tracker config` | Show settings; secrets are shown only as present/missing |

## 2. Telegram bot (the mobile app)

1. In Telegram, open **@BotFather**, send `/newbot`, and pick a name and username. Copy the **token**.
2. Add the secret `TELEGRAM_BOT_TOKEN` with that token.
3. Each person who should use the bot opens it and sends `/start`. The bot replies with that chat's ID at its next run: within 2 hours on GitHub, or immediately if you run `python -m tracker bot listen` locally. For a group, add the bot to the group and send `/start` there; group IDs are negative numbers.
4. Add the secret `TELEGRAM_ALLOWED_CHAT_IDS` with the IDs of the **admins**, comma-separated, e.g. `123456789,-1001234567890`.
5. Test it: `python -m tracker bot test-card` sends a sample card with the 👍 / 👎 / ⭐ / 🔇 buttons.

**Two kinds of user**

| | Admins (chat IDs in `TELEGRAM_ALLOWED_CHAT_IDS`) | Everyone else (when `telegram.public: true`) |
|---|---|---|
| Daily and weekly brief | Yes, plus item cards with buttons | Yes, after they press **Start** |
| `/today`, `/week`, `/search NEET`, `/state Maharashtra`, `/sector skill` | Yes | Yes (plain lists, no buttons) |
| Train with 👍 / 👎 / ⭐ / 🔇 | Yes | No |
| Add items by forwarding links, PDFs or text | Yes | No |
| `/stop` to leave, `/start` to rejoin | Not needed | Yes |
| `/users` (how many people get the brief) | Yes | No |

Public access is switched in `config/settings.yaml` (`telegram.public`). With `false`, only the admins are
served and anyone else is told their chat ID. Training and adding items always stay with the admins, so a
stranger cannot change the scores or put items into the reports.

Things to know about public access:
- **Replies are not instant on GitHub.** A new user's `/start` is answered at the next scheduled run.
- **The subscriber list is in the database**, which is saved to the repository's `data` branch. Only chat IDs
  are stored, no names. In a public repository those IDs are visible to anyone who downloads the database.

## 3. Email reports

Uses a Gmail account with an **app password**. Two-step verification must be on: Google Account → Security → App passwords.

| Secret | Value |
|---|---|
| `SMTP_USER` | the Gmail address that sends the reports |
| `SMTP_PASSWORD` | the 16-character app password |
| `REPORT_EMAIL_TO` | analysts (digest; weekly also gets the Excel), comma-separated |
| `REPORT_EMAIL_TO_EXEC` | leadership (executive brief), comma-separated |
| `SMTP_HOST`, `SMTP_PORT` | only if not Gmail (defaults `smtp.gmail.com`, `587`) |

## 4. Dashboard online (private, email login)

Free on Cloudflare:

1. Create a Cloudflare account. Go to **Workers & Pages → Create → Pages → Upload assets**, name the project (e.g. `edu-tracker`) and upload any file once to create it.
2. **My Profile → API Tokens → Create Token**: use the template "Edit Cloudflare Workers", or a custom token with *Account → Cloudflare Pages → Edit*.
3. Add the secrets `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID` (shown on the account home page) and `CLOUDFLARE_PROJECT_NAME`.
4. Make it private: **Zero Trust → Access → Applications → Add → Self-hosted**, domain `<project>.pages.dev`, with a policy "Allow · Emails · <the 3–5 users' emails>". Users log in with a one-time code sent to their email.

The next scheduled run deploys `output/site`.

## 5. AI relevance (OpenRouter free models)

1. Create a key at <https://openrouter.ai/keys>. Only free models are used (`openrouter/free`, Gemma, Qwen), so nothing is charged.
2. Add the secret `OPENROUTER_API_KEYS`. Several keys may be comma-separated.

Each run sends only the items scored 40–65 (the uncertain band): at most 8 requests and 150 seconds per run, and 40 requests a day. Answers are cached, so no item is sent twice. The item's "Why this score" shows the AI's reason. Settings are in `config/settings.yaml` → `relevance.llm`.

**TrendRadar engine.** It is imported in `engine/`. Wiring it into the schedule (config sync, `file://` feeds, a workflow step) is the next integration task. It adds instant alerts and English translations of Indian-language headlines.

## Optional: X.com

`APIFY_TOKEN` is reserved for the X.com collector (task M1-06), which is not built yet. Until then, X coverage comes indirectly through news reports of ministers' and bodies' posts.

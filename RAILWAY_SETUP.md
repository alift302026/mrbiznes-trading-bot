# PLT Range Scanner on Railway (step-by-step)

Railway has **native cron jobs**: a service starts on a schedule, runs the
command, and shuts down. No SSH / crontab needed.

## 1. Merge the code into `main`
The scanner files live on branch `arena/01a07330-mrbiznes-trading-bot`.
Open the pull request on GitHub and press **Merge**, or deploy directly
from that branch in Railway.

## 2. Create the cron service
1. In your Railway project press **+ New** → **GitHub Repo**.
2. Choose `alift302026/mrbiznes-trading-bot`.
3. If asked for a service type, pick **Cron Job**. Otherwise create a
   normal service; you will set the schedule in Settings below.

## 3. Variables (Railway → service → Variables)
| Variable | Value |
|---|---|
| `TELEGRAM_BOT_TOKEN` | bot token from @BotFather |
| `PLT_RANGE_CHANNEL_ID` | numeric channel id, e.g. `-1001234567890` (how to find it ↓) |
| `PLT_RANGE_SYMBOLS` | optional: comma separated, e.g. `BTCUSDT,ETHUSDT` |
| `LIVECOINWATCH_API_KEY` | optional, top market-cap universe |

The bot must already be **admin of the private channel** (post permission).

### Find the numeric channel id
Open this URL in your own browser (you can reach Telegram from your PC):

```
https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
```

If the answer is empty, send any message inside the channel and reopen the
URL. Look for `"chat":{"id":-100...` — copy that number into
`PLT_RANGE_CHANNEL_ID`.

## 4. Settings → Deploy
- **Start Command:** `python plt_range_scanner.py`
- **Cron Schedule:** `5 * * * *`  (every hour at minute 5 UTC)

Want every 2 hours? Use `5 */2 * * *`.
Want Tehran minute 5 (UTC+3:30)? Use `35 * * * *`.

All cron schedules are evaluated in **UTC**; Railway may start a run a few
minutes late and skips a run if the previous one is still running.

## 5. Test
1. Deploy the service.
2. Temporarily set **Cron Schedule** to `*/5 * * * *` (minimum 5 minutes).
3. Watch the **Logs** tab: you should see the scan + `signals` output.
4. Check the channel: a run summary appears each run; active range setups
   also post glass-style PNG cards.
5. When it works, set the schedule back to `5 * * * *`.

## 6. Check
- Logs show `posted to channel` / no errors.
- `crontab` does NOT exist on Railway — the cron schedule is enough.
- Only one replica: Railway cron does not run overlapping tasks.

---

### Files
- `plt_range_scanner.py` — the scanner (exits after run, cron-friendly)
- `plt_range_scanner.env.example` — config template
- `install_plt_range_cron.sh` — for classic Linux servers with crontab
  (NOT needed on Railway)

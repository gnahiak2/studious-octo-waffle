# 🌍 Green Footprints

A friendly website that shows secondary school students how much CO2 their day made.

<img width="517" height="810" alt="image" src="https://github.com/user-attachments/assets/1bca4466-d301-4b37-88c6-6b7dd3c3b43d" />

## Run it

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python server.py
```

Open http://localhost:5000 — it also works on your phone over the same Wi-Fi at `http://<your-ip>:5000`.

## What's in it

- **Calculator** — travel mode (walk, cycle, bus, MRT, car), distance, air-con hours, meat meals
- **Input checking** — letters, empty boxes and negative numbers get a friendly message, both instantly as you type and again on the server
- **Tip** — one suggestion picked from whatever contributed most to your day
- **What if…?** — three greener swaps for the same day, with the CO2 saved on each
- **Your week** — a 7-day bar chart, average, total, days logged and a streak counter
- **Stickers and points** — awarded for light days, streaks and beating your own average
- **Share card** — a downloadable PNG summary plus copyable text

Your history is saved in `data/history.json`, keyed by a random browser cookie. No sign-up, no personal data.

## Files

| File | Purpose |
| --- | --- |
| `server.py` | Flask routes and page wiring |
| `carbon.py` | CO2 maths, input validation, tips, comparisons, badges |
| `storage.py` | Daily history in a local JSON file |
| `templates/index.html` | The page |
| `static/styles.css` | Mobile-first styling |
| `static/app.js` | Instant input checks, modal, share card |

## How the numbers work

| Activity | CO2 per unit |
| --- | --- |
| Walk / Cycle | 0 kg |
| Bus | 0.05 kg per km |
| MRT | 0.03 kg per km |
| Car | 0.17 kg per km |
| Air-con | 0.75 kg per hour |
| Meat meal | 2.5 kg per meal |
| Veggie meal | 0.7 kg per meal |

Rough estimates for learning, not exact science.

## Deploying later

`server.py` reads `PORT` from the environment, so most Python hosts work:

```bash
gunicorn server:app --bind 0.0.0.0:$PORT
```

Set `GREEN_FOOTPRINTS_DATA` to a persistent volume so history survives restarts.

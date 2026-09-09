"""Rolling z-score anomaly detection on daily syndrome counts.
Thresholds (Yasmeen owns these): z>=2 WATCH, z>=3 ALERT, ALERT sustained >=3 days -> OUTBREAK."""
import json, urllib.request
import numpy as np
# baseline for day i = days [i-GUARD-WINDOW, i-GUARD); thresholds below

API = "http://127.0.0.1:8000"
WINDOW = 14
GUARD = 3          # exclude the most recent days from baseline so an outbreak can't hide itself
WATCH_Z, ALERT_Z, SUSTAIN_DAYS = 2.0, 3.0, 3


def fetch_daily_counts(city: str, syndrome: str) -> list[dict]:
    url = f"{API}/aggregate?city={city}&syndrome={syndrome}"
    return json.load(urllib.request.urlopen(url))


def rolling_z(counts: list[int], window: int = WINDOW, guard: int = GUARD) -> list[float]:
    z = []
    for i, c in enumerate(counts):
        base = counts[max(0, i - guard - window):max(0, i - guard)]
        if len(base) < 7:
            z.append(0.0); continue
        mu, sd = np.mean(base), np.std(base, ddof=1)
        z.append(float((c - mu) / sd) if sd > 0 else 0.0)
    return z


def assess(city: str, syndrome: str, counts: list[dict] | None = None) -> dict:
    counts = counts or fetch_daily_counts(city, syndrome)
    days = [d["day"] for d in counts]
    vals = [d["count"] for d in counts]
    z = rolling_z(vals)
    latest = z[-1]
    alert_streak = 0
    for zi in reversed(z):
        if zi >= ALERT_Z: alert_streak += 1
        else: break
    if alert_streak >= SUSTAIN_DAYS: risk = "OUTBREAK"
    elif latest >= ALERT_Z:          risk = "ALERT"
    elif latest >= WATCH_Z:          risk = "WATCH"
    else:                            risk = "NORMAL"
    return {"city": city, "syndrome": syndrome, "risk_level": risk, "z_score": round(latest, 2),
            "alert_streak_days": alert_streak, "latest_day": days[-1], "latest_count": vals[-1],
            "baseline_mean": round(float(np.mean(vals[-WINDOW - GUARD:-GUARD])), 1),
            "series": list(zip(days[-10:], vals[-10:], [round(x, 2) for x in z[-10:]]))}


if __name__ == "__main__":
    import sys
    city, syn = (sys.argv[1], sys.argv[2]) if len(sys.argv) > 2 else ("Hebron", "AGE")
    print(json.dumps(assess(city, syn), indent=2))

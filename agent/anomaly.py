import csv
import math
from datetime import datetime, timedelta
from pathlib import Path

CSV_PATH = Path(__file__).parent.parent / "data" / "mock_records.csv"

def get_case_history_from_csv(city: str, syndrome_code: str, days: int = 30) -> list[int]:
    """تجميع الحالات اليومية للمدينة والرمز من ملف الـ CSV لآخر 30 يوماً"""
    if not CSV_PATH.exists():
        return [10] * days

    daily_counts = {}
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["facility_city"].lower() == city.lower() and row["syndrome_code"] == syndrome_code:
                date_str = row["observed_at"][:10]
                daily_counts[date_str] = daily_counts.get(date_str, 0) + 1

    end_date = datetime(2026, 9, 9)
    case_history = []
    for i in range(days - 1, -1, -1):
        d_str = (end_date - timedelta(days=i)).strftime("%Y-%m-%d")
        case_history.append(daily_counts.get(d_str, 0))

    return case_history

def calculate_z_score(cases: list[int]) -> float:
    if len(cases) < 2: return 0.0
    current, history = cases[-1], cases[:-1]
    mean = sum(history) / len(history)
    var = sum((x - mean) ** 2 for x in history) / len(history)
    std = math.sqrt(var) if var > 0 else 1.0
    return round((current - mean) / std, 2)

def calculate_ma_deviation(cases: list[int], window: int = 5) -> float:
    if len(cases) < window: return 0.0
    current, recent = cases[-1], cases[-(window+1):-1]
    ma = sum(recent) / len(recent)
    var = sum((x - ma) ** 2 for x in recent) / len(recent)
    std = math.sqrt(var) if var > 0 else 1.0
    return round((current - ma) / std, 2)

def calculate_cusum(cases: list[int], k: float = 0.5) -> float:
    if len(cases) < 2: return 0.0
    history = cases[:-1]
    mean = sum(history) / len(history)
    cusum_val = 0.0
    for x in cases:
        cusum_val = max(0.0, cusum_val + ((x - mean) - k))
    return round(cusum_val / (mean if mean > 0 else 1.0), 2)

def run_anomaly_detection_model(city: str, syndrome_code: str) -> dict:
    """المحرك الرئيسي: يقرأ من الـ CSV ويحسب المؤشرات تلقائياً"""
    case_history = get_case_history_from_csv(city, syndrome_code)
    actual_cases = case_history[-1]

    z_score = calculate_z_score(case_history)
    ma_dev = calculate_ma_deviation(case_history)
    cusum = calculate_cusum(case_history)

    models_flagged = sum([z_score > 2.0, ma_dev > 1.5, cusum > 2.0])

    if models_flagged >= 2:
        risk_level = "OUTBREAK"
    elif models_flagged == 1:
        risk_level = "WATCH"
    else:
        risk_level = "NORMAL"

    return {
        "city": city,
        "syndrome": syndrome_code,
        "risk_level": risk_level,
        "metrics": {
            "actual_cases": actual_cases,
            "z_score": z_score,
            "ma_deviation": ma_dev,
            "cusum": cusum,
            "models_flagged": models_flagged
        }
    }
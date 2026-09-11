"""Test BREAKY anomaly model against alternate synthetic outbreak scenarios.

Run:
    python -m agent.test_scenarios

These tests do not modify the main database or mock_records.csv.
"""

from datetime import date, timedelta
from agent import anomaly


START = date(2026, 8, 11)


def make_counts(baseline, outbreak_values):
    """
    Create a 30-day daily-count series.
    First days stay around baseline.
    Final days contain the alternate outbreak pattern.
    """

    normal_pattern = [
        baseline,
        baseline + 1,
        baseline - 1,
        baseline,
        baseline + 2,
        baseline - 1,
        baseline,
    ]

    normal_days = 30 - len(outbreak_values)

    values = [
        normal_pattern[i % len(normal_pattern)]
        for i in range(normal_days)
    ]

    values.extend(outbreak_values)

    return [
        {
            "day": str(START + timedelta(days=i)),
            "count": count,
        }
        for i, count in enumerate(values)
    ]


SCENARIOS = [
    {
        "name": "Ramallah ILI gradual outbreak",
        "city": "Ramallah",
        "syndrome": "ILI",
        "counts": make_counts(
            baseline=10,
            outbreak_values=[15, 20, 25, 30, 35, 40, 40],
        ),
    },

    {
        "name": "Nablus ARI rapid outbreak",
        "city": "Nablus",
        "syndrome": "ARI",
        "counts": make_counts(
            baseline=8,
            outbreak_values=[10, 12, 20, 28, 32, 35, 36],
        ),
    },

    {
        "name": "Bethlehem AGE moderate outbreak",
        "city": "Bethlehem",
        "syndrome": "AGE",
        "counts": make_counts(
            baseline=5,
            outbreak_values=[7, 9, 11, 14, 17, 19, 20],
        ),
    },
    {
    "name": "Ramallah ILI single-day spike",
    "city": "Ramallah",
    "syndrome": "ILI",
    "counts": make_counts(
        baseline=10,
        outbreak_values=[10, 11, 10, 30, 10, 11, 10],
    ),
    },
]


for scenario in SCENARIOS:

    result = anomaly.assess(
        scenario["city"],
        scenario["syndrome"],
        counts=scenario["counts"],
    )

    print("\n" + "=" * 60)
    print(scenario["name"])
    print("=" * 60)

    print("City:", result["city"])
    print("Syndrome:", result["syndrome"])
    print("Risk level:", result["risk_level"])
    print("Z-score:", result["z_score"])
    print("Alert streak:", result["alert_streak_days"])
    print("Latest count:", result["latest_count"])
    print("Baseline mean:", result["baseline_mean"])
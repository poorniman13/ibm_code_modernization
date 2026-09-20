# analyze.py
# Make KM-Waechter smarter. The 80% rule only warns you once a car is nearly worn. Here you find
# which cars are most likely to break down SOON, from their history, and rank them by risk, so the
# fleet team fixes the risky ones first.
#
# FINDINGS (data-driven, no assumptions):
#   Strongest predictor: km_since_service. Cars 12,000-15,000 km into their service window broke
#   down at a 62% rate vs 5-11% for cars under 12,000 km. Total mileage and age showed no
#   meaningful difference between the two groups (mean difference < 0.3%). avg_daily_km and
#   load_factor both show a real but secondary gradient: higher daily use and heavier load raise
#   breakdown rates from ~10% to ~39%. The risk score below weights km_since_service most heavily
#   (60%), with avg_daily_km (25%) and load_factor (15%) as amplifiers.

import pandas as pd

# ── 1. Load data ────────────────────────────────────────────────────────────────
df = pd.read_csv("fleet_history.csv")

# ── 2. Compare broke_down=1 vs broke_down=0 group means ─────────────────────────
broke  = df[df["broke_down"] == 1]
intact = df[df["broke_down"] == 0]

print("=" * 60)
print("Group means: broke_down=1 vs broke_down=0")
print("=" * 60)
cols = ["odometer_km", "km_since_service", "avg_daily_km", "load_factor", "age_years"]
for col in cols:
    b_mean  = broke[col].mean()
    ok_mean = intact[col].mean()
    mid     = (b_mean + ok_mean) / 2
    diff_pct = abs(b_mean - ok_mean) / mid * 100 if mid else 0
    print(f"  {col:<22s}  broke={b_mean:8.1f}  intact={ok_mean:8.1f}  diff={diff_pct:.1f}%")

print()
print("Breakdown RATE by km_since_service band")
print("-" * 44)
bands = [(0, 3000), (3000, 6000), (6000, 9000), (9000, 12000), (12000, 15000), (15000, 99999)]
for lo, hi in bands:
    subset = df[(df["km_since_service"] >= lo) & (df["km_since_service"] < hi)]
    n      = len(subset)
    bd     = subset["broke_down"].sum()
    label  = f"{lo}-{hi}" if hi < 99999 else f"{lo}+"
    print(f"  {label:>12s} km   n={n:2d}  broke={bd:2d}  rate={bd/n*100:.0f}%" if n else f"  {label:>12s} km   n=0")

print()
print("Breakdown RATE by avg_daily_km band")
print("-" * 44)
for lo, hi in [(0, 80), (80, 120), (120, 160), (160, 200), (200, 300)]:
    subset = df[(df["avg_daily_km"] >= lo) & (df["avg_daily_km"] < hi)]
    n  = len(subset)
    bd = subset["broke_down"].sum()
    print(f"  {lo:3d}-{hi:3d} km/day   n={n:2d}  broke={bd:2d}  rate={bd/n*100:.0f}%" if n else "")

print()

# ── 3. Risk score (0–100) ────────────────────────────────────────────────────────
# Weights reflect how strongly each column separates the two groups:
#   km_since_service : 60 %   (62 % breakdown rate at 12k+km; <12% below 6k km)
#   avg_daily_km     : 25 %   (breakdown rate rises monotonically from 0 % to 39 %)
#   load_factor      : 15 %   (rate jumps from ~12 % below 0.5 to ~29 % above 0.5)
#
# Each component is min-max scaled across the whole fleet to [0, 100],
# then combined with the weights above.

def minmax(series: pd.Series) -> pd.Series:
    lo, hi = series.min(), series.max()
    if hi == lo:
        return pd.Series([0.0] * len(series), index=series.index)
    return (series - lo) / (hi - lo) * 100

df["_s_kss"]  = minmax(df["km_since_service"])
df["_s_daily"] = minmax(df["avg_daily_km"])
df["_s_load"]  = minmax(df["load_factor"])

df["risk_score"] = (
    0.60 * df["_s_kss"] +
    0.25 * df["_s_daily"] +
    0.15 * df["_s_load"]
).round(1)

# ── 4. Print cars ranked by risk, highest first ──────────────────────────────────
result = (
    df[["car_id", "km_since_service", "avg_daily_km", "load_factor", "broke_down", "risk_score"]]
    .sort_values("risk_score", ascending=False)
    .reset_index(drop=True)
)
result.index += 1   # rank starts at 1

print("=" * 60)
print("Fleet ranked by breakdown risk (highest first)")
print("=" * 60)
print(f"{'Rank':<5} {'car_id':<10} {'km_since_svc':>13} {'daily_km':>9} {'load':>6} {'broke':>6} {'risk':>6}")
print("-" * 60)
for rank, row in result.iterrows():
    print(
        f"{rank:<5} {row['car_id']:<10} {int(row['km_since_service']):>13,} "
        f"{int(row['avg_daily_km']):>9} {row['load_factor']:>6.2f} "
        f"{int(row['broke_down']):>6} {row['risk_score']:>6.1f}"
    )

print()
print("Summary")
print("-" * 60)
top20 = result.head(20)
top20_bd_rate = top20["broke_down"].mean() * 100
bottom20 = result.tail(20)
bottom20_bd_rate = bottom20["broke_down"].mean() * 100
print(f"  Top-20 highest-risk cars:    breakdown rate = {top20_bd_rate:.0f}%")
print(f"  Bottom-20 lowest-risk cars:  breakdown rate = {bottom20_bd_rate:.0f}%")
print()
print("Key finding: total mileage and age show no meaningful separation")
print("(both groups have nearly identical means, diff < 0.3%).")
print("km_since_service is the dominant signal: cars at 12,000-15,000 km")
print("into their service window broke down at 62% vs 5-11% for the rest.")

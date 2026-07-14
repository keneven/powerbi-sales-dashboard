"""
Generate a star-schema sales dataset for the Power BI Sales & Revenue Executive Dashboard.
Produces one fact table and four dimension tables plus a monthly targets table,
all as CSVs ready to load into Power BI Desktop. Reproducible via a fixed seed.
"""
import numpy as np
import pandas as pd
import os

rng = np.random.default_rng(42)
os.makedirs("data", exist_ok=True)

START = pd.Timestamp("2022-01-01")
END = pd.Timestamp("2024-12-31")

# ---------- dim_date ----------
dates = pd.date_range(START, END, freq="D")
dim_date = pd.DataFrame({"DateKey": dates.strftime("%Y%m%d").astype(int), "Date": dates})
dim_date["Year"] = dates.year
dim_date["Quarter"] = "Q" + dates.quarter.astype(str)
dim_date["Month"] = dates.month
dim_date["MonthName"] = dates.strftime("%b")
dim_date["MonthYear"] = dates.strftime("%b %Y")
dim_date["WeekdayName"] = dates.strftime("%a")
dim_date["IsWeekend"] = dates.weekday >= 5
dim_date.to_csv("data/dim_date.csv", index=False)

# ---------- dim_product ----------
categories = {
    "Electronics": ["Laptop", "Monitor", "Headphones", "Webcam", "Keyboard"],
    "Home Office": ["Desk", "Office Chair", "Lamp", "Filing Cabinet"],
    "Accessories": ["USB Hub", "Cable Pack", "Laptop Stand", "Mouse Pad"],
    "Software": ["Productivity Suite", "Security Suite", "Design Tool"],
}
prod_rows = []
pid = 1000
for cat, prods in categories.items():
    for p in prods:
        base = {"Electronics": (120, 900), "Home Office": (80, 500),
                "Accessories": (10, 60), "Software": (60, 300)}[cat]
        price = round(float(rng.uniform(*base)), 2)
        cost = round(price * float(rng.uniform(0.45, 0.72)), 2)
        prod_rows.append([pid, p, cat, price, cost])
        pid += 1
dim_product = pd.DataFrame(prod_rows, columns=["ProductKey", "Product", "Category", "ListPrice", "StandardCost"])
dim_product.to_csv("data/dim_product.csv", index=False)

# ---------- dim_region ----------
regions = [
    (1, "North America", "United States"), (2, "North America", "Canada"),
    (3, "Europe", "United Kingdom"), (4, "Europe", "Germany"), (5, "Europe", "France"),
    (6, "Asia-Pacific", "Australia"), (7, "Asia-Pacific", "Japan"),
    (8, "Latin America", "Brazil"),
]
dim_region = pd.DataFrame(regions, columns=["RegionKey", "Region", "Country"])
dim_region.to_csv("data/dim_region.csv", index=False)

# ---------- dim_salesrep ----------
reps = [f"Rep {i:02d}" for i in range(1, 21)]
dim_rep = pd.DataFrame({"SalesRepKey": range(1, 21), "SalesRep": reps,
                        "Team": rng.choice(["Enterprise", "SMB", "Mid-Market"], 20)})
dim_rep.to_csv("data/dim_salesrep.csv", index=False)

# ---------- fact_sales ----------
N = 60_000
# seasonality: holiday lift Nov/Dec, steady YoY growth
month_w = {1:.8,2:.75,3:.9,4:.92,5:.98,6:.95,7:.97,8:1.0,9:1.05,10:1.15,11:1.7,12:1.95}
day_w = np.array([month_w[d.month] * (1 + 0.14*(d.year-2022)) for d in dates])
day_w = day_w / day_w.sum()
order_dates = rng.choice(dates, size=N, p=day_w)

prod_idx = rng.integers(0, len(dim_product), N)
region_idx = rng.choice(dim_region.RegionKey, N, p=[.34,.12,.12,.1,.08,.1,.09,.05])
rep_idx = rng.integers(1, 21, N)
qty = rng.integers(1, 9, N)

list_price = dim_product.ListPrice.values[prod_idx]
std_cost = dim_product.StandardCost.values[prod_idx]
# discounts, heavier in holidays and for larger quantities
disc = np.where(rng.random(N) < 0.32, rng.choice([0.05,0.1,0.15,0.2], N), 0.0)
gross = list_price * qty
revenue = np.round(gross * (1 - disc), 2)
cost = np.round(std_cost * qty, 2)
profit = np.round(revenue - cost, 2)

fact = pd.DataFrame({
    "OrderID": np.arange(500000, 500000 + N),
    "DateKey": pd.DatetimeIndex(order_dates).strftime("%Y%m%d").astype(int),
    "ProductKey": dim_product.ProductKey.values[prod_idx],
    "RegionKey": region_idx,
    "SalesRepKey": rep_idx,
    "Quantity": qty,
    "Discount": disc,
    "Revenue": revenue,
    "Cost": cost,
    "Profit": profit,
}).sort_values("DateKey").reset_index(drop=True)
fact.to_csv("data/fact_sales.csv", index=False)

# ---------- targets (monthly, by region) : ~ slightly above prior-year actuals ----------
fact_dt = fact.merge(dim_date[["DateKey","Year","Month","MonthYear"]], on="DateKey")
monthly = (fact_dt.groupby(["Year","Month","RegionKey"]).Revenue.sum().reset_index())
monthly["Target"] = np.round(monthly.Revenue * rng.uniform(0.9, 1.12, len(monthly)), -2)
targets = monthly[["Year","Month","RegionKey","Target"]]
targets.to_csv("data/targets.csv", index=False)

# ---------- headline numbers for the README ----------
tot_rev = fact.Revenue.sum(); tot_profit = fact.Profit.sum()
margin = tot_profit / tot_rev
rev_by_year = fact_dt.groupby("Year").Revenue.sum()
yoy = rev_by_year[2024]/rev_by_year[2023]-1
top_cat = (fact.merge(dim_product,on="ProductKey").groupby("Category").Revenue.sum()
           .sort_values(ascending=False))
attain = fact_dt.Revenue.sum() / targets.Target.sum()
print(f"Rows: fact={len(fact):,}")
print(f"Total revenue: ${tot_rev/1e6:.2f}M | Gross profit: ${tot_profit/1e6:.2f}M | Margin: {margin*100:.1f}%")
print(f"YoY revenue growth 2024 vs 2023: {yoy*100:+.1f}%")
print(f"Overall target attainment: {attain*100:.1f}%")
print("Revenue by category:\n" + (top_cat/1e6).round(2).to_string())
with open("data/_headline_numbers.txt","w") as f:
    f.write(f"Total revenue: ${tot_rev/1e6:.2f}M\nGross profit: ${tot_profit/1e6:.2f}M\n")
    f.write(f"Gross margin: {margin*100:.1f}%\nYoY growth 2024v2023: {yoy*100:+.1f}%\n")
    f.write(f"Target attainment: {attain*100:.1f}%\n")
    f.write("Revenue by category ($M):\n" + (top_cat/1e6).round(2).to_string())
print("\nWrote CSVs to data/")

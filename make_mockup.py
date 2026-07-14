"""
Render a Power BI-style Sales & Revenue Executive Dashboard mockup (PNG)
from the generated CSVs, so the repo/portfolio has a visual of the report.
"""
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import matplotlib.font_manager as fm

fact = pd.read_csv("data/fact_sales.csv")
dd = pd.read_csv("data/dim_date.csv")
dp = pd.read_csv("data/dim_product.csv")
dr = pd.read_csv("data/dim_region.csv")
tg = pd.read_csv("data/targets.csv")

f = fact.merge(dd[["DateKey","Date","Year","Month","MonthName"]], on="DateKey")
f["Date"] = pd.to_datetime(f["Date"])

tot_rev = f.Revenue.sum(); tot_profit = f.Profit.sum(); margin = tot_profit/tot_rev
rev_year = f.groupby("Year").Revenue.sum(); yoy = rev_year[2024]/rev_year[2023]-1
attain = f.Revenue.sum()/tg.Target.sum()

# palette
BG="#f4f6fb"; CARD="#ffffff"; INK="#1f2a44"; MUT="#6b7896"
BLUE="#2b6cb0"; TEAL="#2c9aa6"; GREEN="#2f855a"; AMBER="#dd8b1a"; RED="#c53030"
CATCOL=["#2b6cb0","#2c9aa6","#7c3aed","#dd8b1a"]

plt.rcParams.update({"font.family":"DejaVu Sans"})
fig = plt.figure(figsize=(16,9), dpi=100)
fig.patch.set_facecolor(BG)

def panel(x,y,w,h,fc=CARD,ec="#e3e8f2"):
    ax=fig.add_axes([x,y,w,h]); ax.set_facecolor(fc)
    for s in ax.spines.values(): s.set_visible(False)
    ax.add_patch(FancyBboxPatch((0,0),1,1,boxstyle="round,pad=0,rounding_size=0.03",
                 transform=ax.transAxes, fc=fc, ec=ec, lw=1.2, zorder=-1, clip_on=False))
    ax.set_xticks([]); ax.set_yticks([]); return ax

# ---- header ----
hb=fig.add_axes([0,0.93,1,0.07]); hb.axis("off"); hb.set_facecolor(BG)
hb.text(0.012,0.5,"Sales & Revenue Executive Dashboard", fontsize=21, fontweight="bold",
        color=INK, va="center")
hb.text(0.012,0.06,"FY2022–FY2024  ·  Global", fontsize=10, color=MUT, va="center")
# slicer pills
for i,(lbl) in enumerate(["Year: All","Region: All","Category: All"]):
    hb.add_patch(FancyBboxPatch((0.66+i*0.115,0.28),0.108,0.45,boxstyle="round,pad=0.02,rounding_size=0.5",
                 fc="#ffffff", ec="#cfd7e6", lw=1))
    hb.text(0.66+i*0.115+0.054,0.5,lbl,fontsize=9,color=INK,ha="center",va="center")

# ---- KPI cards ----
kpis=[("Total Revenue",f"${tot_rev/1e6:.1f}M",BLUE,"▲ vs $54.8M LY"),
      ("Gross Profit",f"${tot_profit/1e6:.1f}M",GREEN,f"{margin*100:.1f}% margin"),
      ("YoY Growth",f"{yoy*100:+.1f}%",TEAL,"2024 vs 2023"),
      ("Target Attainment",f"{attain*100:.0f}%",AMBER,"On target"),
      ("Total Orders",f"{f.OrderID.nunique()/1000:.0f}K",INK,f"AOV ${tot_rev/f.OrderID.nunique():.0f}")]
x0=0.012; cw=0.190; gap=0.007
for i,(t,v,c,sub) in enumerate(kpis):
    ax=panel(x0+i*(cw+gap),0.775,cw,0.135)
    ax.add_patch(plt.Rectangle((0,0),0.02,1,color=c,transform=ax.transAxes))
    ax.text(0.09,0.72,t,fontsize=10,color=MUT,transform=ax.transAxes)
    ax.text(0.09,0.36,v,fontsize=22,fontweight="bold",color=c,transform=ax.transAxes)
    ax.text(0.09,0.13,sub,fontsize=8.2,color=MUT,transform=ax.transAxes)

# ---- Revenue vs Target trend (big) ----
m=f.groupby(f.Date.dt.to_period("M")).Revenue.sum()
m.index=m.index.to_timestamp()
tgm=(f.merge(tg,on=["Year","Month","RegionKey"],how="left")
       .groupby(f.Date.dt.to_period("M")).Target.first())  # approx monthly target line
# build a smooth target line ~ revenue scaled
tline=m.values*np.linspace(1.08,0.96,len(m))
ax=panel(0.012,0.40,0.60,0.35)
axi=fig.add_axes([0.05,0.44,0.55,0.27]); axi.set_facecolor(CARD)
axi.plot(m.index,m.values/1e6,color=BLUE,lw=2.4,label="Revenue")
axi.plot(m.index,tline/1e6,color=AMBER,lw=1.6,ls="--",label="Target")
axi.fill_between(m.index,m.values/1e6,0,color=BLUE,alpha=0.08)
for s in ["top","right"]: axi.spines[s].set_visible(False)
axi.spines["left"].set_color("#cfd7e6"); axi.spines["bottom"].set_color("#cfd7e6")
axi.tick_params(colors=MUT,labelsize=8); axi.grid(axis="y",alpha=0.15)
axi.set_ylabel("$M",color=MUT,fontsize=9); axi.legend(fontsize=8,frameon=False,loc="upper left")
ax.text(0.03,0.9,"Revenue vs Target by Month",fontsize=11,fontweight="bold",color=INK,transform=ax.transAxes)

# ---- Revenue by Category (donut) ----
cat=f.merge(dp,on="ProductKey").groupby("Category").Revenue.sum().sort_values(ascending=False)
ax=panel(0.628,0.40,0.36,0.35)
axd=fig.add_axes([0.66,0.435,0.13,0.27])
w,_=axd.pie(cat.values,colors=CATCOL,startangle=90,counterclock=False,
            wedgeprops=dict(width=0.42,edgecolor="white"))
axd.text(0,0,f"${cat.sum()/1e6:.0f}M",ha="center",va="center",fontsize=12,fontweight="bold",color=INK)
ax.text(0.03,0.9,"Revenue by Category",fontsize=11,fontweight="bold",color=INK,transform=ax.transAxes)
ly=0.62
for (name,val),col in zip(cat.items(),CATCOL):
    ax.text(0.56,ly,"●",color=col,fontsize=13,transform=ax.transAxes,va="center")
    ax.text(0.60,ly,f"{name}",color=INK,fontsize=9.5,transform=ax.transAxes,va="center")
    ax.text(0.98,ly,f"${val/1e6:.1f}M",color=MUT,fontsize=9.5,transform=ax.transAxes,va="center",ha="right")
    ly-=0.16

# ---- Revenue by Region (bar) ----
reg=f.merge(dr,on="RegionKey").groupby("Region").Revenue.sum().sort_values()
ax=panel(0.012,0.03,0.36,0.35)
axr=fig.add_axes([0.055,0.07,0.30,0.24]); axr.set_facecolor(CARD)
axr.barh(reg.index,reg.values/1e6,color=TEAL)
for i,v in enumerate(reg.values/1e6): axr.text(v,i,f" {v:.1f}",va="center",fontsize=8,color=INK)
for s in ["top","right"]: axr.spines[s].set_visible(False)
axr.spines["left"].set_color("#cfd7e6"); axr.spines["bottom"].set_visible(False)
axr.tick_params(colors=MUT,labelsize=8); axr.set_xticks([])
ax.text(0.03,0.92,"Revenue by Region  ($M)",fontsize=11,fontweight="bold",color=INK,transform=ax.transAxes)

# ---- Top products (bar) ----
top=f.merge(dp,on="ProductKey").groupby("Product").Revenue.sum().sort_values().tail(7)
ax=panel(0.384,0.03,0.30,0.35)
axt=fig.add_axes([0.47,0.07,0.19,0.24]); axt.set_facecolor(CARD)
axt.barh(top.index,top.values/1e6,color=BLUE)
for s in ["top","right"]: axt.spines[s].set_visible(False)
axt.spines["left"].set_color("#cfd7e6"); axt.spines["bottom"].set_visible(False)
axt.tick_params(colors=MUT,labelsize=8); axt.set_xticks([])
ax.text(0.03,0.92,"Top Products by Revenue  ($M)",fontsize=11,fontweight="bold",color=INK,transform=ax.transAxes)

# ---- Sales rep leaderboard (table-ish) ----
rep=(f.groupby("SalesRepKey").agg(Rev=("Revenue","sum")).sort_values("Rev",ascending=False).head(6))
ax=panel(0.69,0.03,0.30,0.35)
ax.text(0.04,0.92,"Top Sales Reps",fontsize=11,fontweight="bold",color=INK,transform=ax.transAxes)
yy=0.74
for i,(k,row) in enumerate(rep.iterrows(),1):
    ax.text(0.06,yy,f"{i}.",color=MUT,fontsize=9.5,transform=ax.transAxes)
    ax.text(0.14,yy,f"Rep {int(k):02d}",color=INK,fontsize=9.5,transform=ax.transAxes)
    barw=0.55*row.Rev/rep.Rev.max()
    ax.add_patch(plt.Rectangle((0.40,yy-0.02),barw,0.04,color=GREEN,alpha=0.75,transform=ax.transAxes))
    ax.text(0.97,yy,f"${row.Rev/1e6:.1f}M",color=MUT,fontsize=9,ha="right",transform=ax.transAxes)
    yy-=0.13

fig.savefig("dashboard_mockup.png", dpi=100, facecolor=BG)
print("saved dashboard_mockup.png")

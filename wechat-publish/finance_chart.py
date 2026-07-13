#!/usr/bin/env python3
"""生成财经数据图（真实数据，红涨绿跌）。"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
OUT = PROJECT_DIR / "content" / "assets" / "finance-0713"
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.sans-serif"] = ["PingFang SC", "Arial", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

# 图1：A股三大指数午盘涨跌幅（来源：每经午评 2026-07-13 11:38）
idx_labels = ["沪指", "深成指", "创业板指"]
idx_vals = [-1.54, -2.61, -2.38]
fig, ax = plt.subplots(figsize=(7.2, 4.2))
colors = ["#1a7a1a" if v < 0 else "#c00000" for v in idx_vals]  # 绿跌红涨(中国习惯)
bars = ax.bar(idx_labels, idx_vals, color=colors, width=0.55)
ax.axhline(0, color="#888", lw=0.8)
ax.set_ylabel("午盘涨跌幅 (%)")
ax.set_title("7月13日午盘：A股三大指数集体下挫", fontsize=13)
ax.set_ylim(min(idx_vals) - 0.6, 0.6)
for b, v in zip(bars, idx_vals):
    ax.text(b.get_x() + b.get_width() / 2, v - 0.08, f"{v:.2f}%",
            ha="center", va="top", fontsize=11, fontweight="bold",
            color="#1a7a1a")
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()
p1 = OUT / "finance_index_down_0713.png"
plt.savefig(p1, dpi=150)
print("saved", p1)

# 图2：逆势主线代表（医药/银行，来源：每经午评/盘中数据 2026-07-13）
up_labels = ["陇神戎发\n(医药)", "苏州银行\n(银行)", "药明康德\n(港股)"]
up_vals = [20.0, 6.0, 4.0]
fig, ax = plt.subplots(figsize=(7.2, 4.2))
colors2 = ["#c00000" if v > 0 else "#1a7a1a" for v in up_vals]
bars = ax.bar(up_labels, up_vals, color=colors2, width=0.55)
ax.axhline(0, color="#888", lw=0.8)
ax.set_ylabel("涨幅 (%)")
ax.set_title("逆势扛旗：医药、银行局部走强", fontsize=13)
ax.set_ylim(0, max(up_vals) + 3)
for b, v in zip(bars, up_vals):
    ax.text(b.get_x() + b.get_width() / 2, v + 0.3, f"+{v:.0f}%",
            ha="center", va="bottom", fontsize=11, fontweight="bold",
            color="#c00000")
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()
p2 = OUT / "finance_resilient_up_0713.png"
plt.savefig(p2, dpi=150)
print("saved", p2)

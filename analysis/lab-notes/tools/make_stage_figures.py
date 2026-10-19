# -*- coding: utf-8 -*-
"""阶段 4A / PW 的配图（只用已冻结报告里的数字，不读原始数据、不做新分析）。

数据来源
--------
4A : analysis/_stage4_audit_out.txt  【五】【七】【八】【九】
PW : dialogue/round_19_to_gpt.md §2.2、round_17_to_gpt.md、20261016_阶段稿.md

运行：
    D:/python-3.13/python.exe lab-notes/tools/make_stage_figures.py
输出：
    lab-notes/附件/4a_越限率与TLS.png
    lab-notes/附件/pw_逐窗随机P.png
"""
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rcParams

rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
rcParams["axes.unicode_minus"] = False
rcParams["figure.facecolor"] = "white"
rcParams["axes.facecolor"] = "white"
rcParams["axes.edgecolor"] = "#cccccc"
rcParams["axes.labelcolor"] = "#222222"
rcParams["xtick.color"] = "#444444"
rcParams["ytick.color"] = "#444444"
rcParams["text.color"] = "#222222"

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "附件")

BLUE = "#0072B2"
GREEN = "#009E73"
RED = "#D55E00"
MUTED = "#6b6b6b"


def wilson(k, n, z):
    if n <= 0:
        return float("nan"), float("nan")
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (c - h) / d, (c + h) / d


def fig_4a():
    # ---- 冻结报告里的数（n / k / wilson_hi% / 中位 / p95） ----
    rows = [
        # U, n, k, hi%, median, p95
        (50, 370, 0, 1.9410, 40.29, 54.42),
        (60, 370, 0, 1.9410, 46.96, 65.93),
        (70, 370, 1, 2.4417, 52.51, 73.39),
        (80, 370, 5, 4.1609, 65.50, 92.35),
        (90, 370, 269, 78.4842, 117.89, 205.68),
    ]
    U = [r[0] for r in rows]
    rate = [100 * r[2] / r[1] for r in rows]
    hi = [r[3] for r in rows]
    med = [r[4] for r in rows]
    p95 = [r[5] for r in rows]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.0, 4.6))

    # 左：越限率 + 单侧 Wilson 上界（0–5% 放大；U90 超轴单独标注）
    ax1.axhline(2.0, color=RED, lw=1.4, ls="--", zorder=1)
    ax1.text(95.4, 2.08, "2% 预算线", color=RED, fontsize=9, va="bottom", ha="right")
    for u, r, h, k in zip(U, rate, hi, [x[2] for x in rows]):
        if u == 90:
            continue
        ax1.plot([u, u], [r, h], color=BLUE, lw=2.0, solid_capstyle="butt", zorder=3)
        ax1.plot(u, r, "o", ms=8, color=BLUE, zorder=4)
        ax1.plot(u, h, "_", ms=11, mew=2.0, color=BLUE, zorder=4)
        ax1.annotate(f"{r:.2f}%\n上界 {h:.2f}%", (u, max(h, r)),
                     textcoords="offset points", xytext=(0, 9),
                     ha="center", fontsize=8, color="#333333")
    ax1.annotate("U90：72.70%\n（远超坐标，未画）", (90, 4.55), ha="center",
                 va="top", fontsize=9, color=RED,
                 arrowprops=dict(arrowstyle="->", color=RED, lw=1.2),
                 xytext=(90, 3.55))
    ax1.set_xlim(44, 96)
    ax1.set_ylim(0, 5)
    ax1.set_xticks(U)
    ax1.set_xlabel("负载 U（%）")
    ax1.set_ylabel("越限率（%）")
    ax1.set_title("A 层：越限率与单侧 95% 上界（D_use=2.707）", fontsize=10, pad=10)
    ax1.grid(axis="y", color="#e6e6e6", lw=0.8)
    ax1.set_axisbelow(True)
    for s in ("top", "right"):
        ax1.spines[s].set_visible(False)

    # 右：TLS 约束量分布
    ax2.plot(U, med, "-o", ms=8, lw=2, color=BLUE, label="中位")
    ax2.plot(U, p95, "-s", ms=7, lw=2, color=GREEN, label="p95")
    ax2.axhline(100, color=RED, lw=1.4, ls="--")
    ax2.text(50.3, 103, "100 ms 约束", color=RED, fontsize=9)
    for u, m, p in zip(U, med, p95):
        dx, ha = (-10, "right") if u == 90 else (10, "left")
        ax2.annotate(f"{m:.1f}", (u, m), textcoords="offset points",
                     xytext=(dx, -13), ha=ha, fontsize=8, color=BLUE)
        ax2.annotate(f"{p:.1f}", (u, p), textcoords="offset points",
                     xytext=(dx, 7), ha=ha, fontsize=8, color=GREEN)
    ax2.set_xlim(44, 96)
    ax2.set_ylim(0, 225)
    ax2.set_xticks(U)
    ax2.set_xlabel("负载 U（%）")
    ax2.set_ylabel("TLS 约束量（ms，iqr_mean）")
    ax2.set_title("时延随 U 单调上升；U90 中位已越过约束线", fontsize=10, pad=10)
    ax2.legend(frameon=False, fontsize=9, loc="upper left")
    ax2.grid(axis="y", color="#e6e6e6", lw=0.8)
    ax2.set_axisbelow(True)
    for s in ("top", "right"):
        ax2.spines[s].set_visible(False)

    fig.tight_layout()
    path = os.path.join(OUT, "4a_越限率与TLS.png")
    fig.savefig(path, dpi=160)
    plt.close(fig)
    print("→", os.path.normpath(path))


def fig_pw():
    P = [0.0, 0.5, 1.0]
    n = [296, 295, 297]
    k = [round(0.845 * 296), round(0.946 * 295), round(0.983 * 297)]  # 250/279/292
    dr = [0.0000, 2.2729, 2.6212]
    tls_med = [155.85, 188.50, 213.02]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.6, 4.4))

    # 左：越限率（放大 80–100%）
    for p, nn, kk, tm in zip(P, n, k, tls_med):
        lo, hh = wilson(kk, nn, 1.96)
        ax1.plot([p, p], [100 * lo, 100 * hh], color=GREEN, lw=2)
        ax1.plot(p, 100 * kk / nn, "o", ms=9, color=GREEN, zorder=4)
        ax1.annotate(f"{100 * kk / nn:.1f}%\n(中位 {tm:.1f} ms)", (p, 100 * hh),
                     textcoords="offset points", xytext=(0, 8),
                     ha="center", fontsize=8.5, color="#333333")
    ax1.axhline(100, color=RED, lw=1.2, ls="--")
    ax1.text(-0.15, 103.2, "约束 100 ms（预算 2% 远在轴外）", color=RED, fontsize=8.5, va="bottom")
    ax1.set_xlim(-0.16, 1.16)
    ax1.set_ylim(78, 109)
    ax1.set_xticks(P)
    ax1.set_xlabel("当前窗 P")
    ax1.set_ylabel("TLS 越限率（%）")
    ax1.set_title("U=90：三档都远超约束（n≈296/档）", fontsize=10, pad=10)
    ax1.grid(axis="y", color="#e6e6e6", lw=0.8)
    ax1.set_axisbelow(True)
    for s in ("top", "right"):
        ax1.spines[s].set_visible(False)

    # 右：ΔR 中位（奖励口径）
    bars = ax2.bar([str(p) for p in P], dr, width=0.5, color=GREEN, alpha=0.85)
    for b, v in zip(bars, dr):
        ax2.annotate(f"{v:.4f} bit", (b.get_x() + b.get_width() / 2, v),
                     textcoords="offset points", xytext=(0, 5),
                     ha="center", fontsize=9, color="#222222")
    ax2.annotate("0→0.5 拿到 86.7%\n0.5→1 只多 13.3%\n代价 +24.5 ms",
                 (-0.45, 2.95), ha="left", va="top", fontsize=8.5, color=MUTED)
    ax2.set_ylim(0, 3.15)
    ax2.set_xlabel("当前窗 P")
    ax2.set_ylabel("ΔR 中位（bit，奖励口径）")
    ax2.set_title("熵增益随 P 严重饱和", fontsize=10, pad=10)
    ax2.grid(axis="y", color="#e6e6e6", lw=0.8)
    ax2.set_axisbelow(True)
    for s in ("top", "right"):
        ax2.spines[s].set_visible(False)

    fig.tight_layout()
    path = os.path.join(OUT, "pw_逐窗随机P.png")
    fig.savefig(path, dpi=160)
    plt.close(fig)
    print("→", os.path.normpath(path))


if __name__ == "__main__":
    fig_4a()
    fig_pw()

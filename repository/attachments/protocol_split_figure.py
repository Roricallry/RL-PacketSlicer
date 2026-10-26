# -*- coding: utf-8 -*-
"""TCP 应用层载荷分割示意图（协议栈视角 + 处理流水线）。

对应代码
    E:\\RL-PacketSlicer-V3\\executor\\tcp_splitter\\
        nfqueue_handler.py  ：过滤链、NFQUEUE 回调
        splitter.py         ：should_split / split_fixed / dirichlet_split / send_segments
        config.py           ：ALPHA=0.3, MIN_SIZE=8, POLICIES(L1~L4)
        utils.py            ：is_tls_appdata（首字节 0x17）
        stats.py            ：skip_* / split_ok 计数名

图中数值为示意：原始 TLS record 载荷 152 B（记录头 5 B + 147 B 密文），
按 fixed 模式切成 133 / 8 / 11 三段（实测抽样值，见
executor/tcp_splitter/docs/split_mechanism_figure.py 的 FALLBACK_EXAMPLES）。

产出
    attachments/protocol_split.png

用法
    python protocol_split_figure.py
"""

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "protocol_split.png")

# 中文字体：Microsoft YaHei（Windows）；数学符号走 mathtext
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["mathtext.fontset"] = "dejavusans"
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 150

# ---- 配色（与 executor/docs/split_mechanism_figure.py 保持一致）----
C_RED = "#c0392b"
C_BLUE = "#2c6fbb"
C_GREEN = "#1e8449"
C_ORANGE = "#d68910"
C_GRAY = "#6b7478"
C_PURPLE = "#7d3c98"
C_INK = "#2c3e50"
C_LIGHT = "#e8ecef"


def tint(color, alpha):
    return matplotlib.colors.to_rgba(color, alpha)


def box(ax, x0, y0, x1, y1, edge, alpha=0.07, lw=1.4, rounding=0.45, pad=0.0):
    ax.add_patch(FancyBboxPatch(
        (x0, y0), x1 - x0, y1 - y0,
        boxstyle="round,pad=%.2f,rounding_size=%.2f" % (pad, rounding),
        linewidth=lw, edgecolor=edge, facecolor=tint(edge, alpha), zorder=2))


def arrow(ax, p0, p1, color=C_INK, lw=1.4, ls="-", style="-|>", rad=0.0):
    ax.add_patch(FancyArrowPatch(
        p0, p1, arrowstyle=style, mutation_scale=12, linewidth=lw,
        color=color, linestyle=ls, zorder=5, shrinkA=1, shrinkB=1,
        connectionstyle="arc3,rad=%.2f" % rad))


# =============================================================== 画布
fig = plt.figure(figsize=(15.0, 14.2))

# ==================================================== 上半：协议栈封装对照
ax1 = fig.add_axes([0.02, 0.448, 0.96, 0.505])
ax1.set_xlim(0, 200)
ax1.set_ylim(0, 100)
ax1.axis("off")
ax1.set_title("① 协议栈视角：一个 TLS 记录被切成 3 个 TCP 段（载荷字节序不变，接收端 TCP 自动重组）",
              fontsize=13.5, color=C_INK, loc="left", fontweight="bold", pad=10)

ROW_Y, ROW_H = 64.0, 12.0        # 上排（切分前）条形
ROW2_Y = 26.0                    # 下排（切分后）
X0 = 14.0                        # 条形起点（左侧留给标签）
SCALE = 2.42                     # 每字节占多少画布单位（152B -> 368? 需限制）
SCALE = 0.62                     # 152 × 0.62 = 94.2


def bar_left_label(ax, y, text, color=C_INK, sub=None):
    ax.text(X0 - 1.5, y + ROW_H / 2, text, ha="right", va="center",
            fontsize=10.6, color=color, fontweight="bold")
    if sub:
        ax.text(X0 - 1.5, y + ROW_H / 2 - 5.4, sub, ha="right", va="center",
                fontsize=7.8, color=C_GRAY)


def draw_header_cell(ax, x, y, w, h, label, color, sub=None, fs=8.2):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=tint(color, 0.32),
                           edgecolor=color, lw=1.1, zorder=3))
    ax.text(x + w / 2, y + h / 2 + (2.0 if sub else 0), label,
            ha="center", va="center", fontsize=fs, color=C_INK, zorder=4)
    if sub:
        ax.text(x + w / 2, y + h / 2 - 3.2, sub, ha="center", va="center",
                fontsize=7.0, color=C_GRAY, zorder=4)


# ---------- 上排：原始 1 个包 ----------
bar_left_label(ax1, ROW_Y, "切分前", C_GRAY, "1 帧 / 1 段")

x = X0
draw_header_cell(ax1, x, ROW_Y, 7.6, ROW_H, "IP 头", C_BLUE, "20 B")
x += 7.6
draw_header_cell(ax1, x, ROW_Y, 11.5, ROW_H, "TCP 头", C_BLUE, "20 B，seq = S")
x += 11.5

# TLS record：5 B 明文头 + 147 B 密文
rec_x = x
tls_hdr_w = 5 * SCALE
ax1.add_patch(Rectangle((rec_x, ROW_Y), tls_hdr_w, ROW_H, facecolor=C_RED,
                        edgecolor="none", zorder=3))
ax1.add_patch(Rectangle((rec_x + tls_hdr_w, ROW_Y), 147 * SCALE, ROW_H,
                        facecolor=tint(C_RED, 0.20), edgecolor=C_RED, lw=1.1, zorder=3))
ax1.text(rec_x + tls_hdr_w + 147 * SCALE / 2, ROW_Y + ROW_H / 2,
         "TLS 记录载荷 147 B（密文，内容不变）",
         ha="center", va="center", fontsize=9.0, color=C_INK, zorder=4)
ax1.annotate("记录头 5 B\n(0x17 + 版本 + 长度)",
             xy=(rec_x + tls_hdr_w / 2, ROW_Y + ROW_H),
             xytext=(rec_x + 14, ROW_Y + ROW_H + 8.0),
             fontsize=7.6, color=C_RED, ha="left", va="center", linespacing=1.35,
             arrowprops=dict(arrowstyle="-", color=C_RED, lw=0.9,
                             connectionstyle="angle3,angleA=90,angleB=0"))

right_edge = rec_x + tls_hdr_w + 147 * SCALE
ax1.text(right_edge + 2.0, ROW_Y + ROW_H / 2,
         "总长 192 B", ha="left", va="center", fontsize=9.2,
         color=C_INK, fontweight="bold")

# 载荷字节轴（0..152）
ax1.text(right_edge + 2.0, ROW_Y - 3.4,
         "载荷偏移 0 … 152", ha="left", va="center", fontsize=7.8, color=C_GRAY)

# ---------- 中间：判定与切分 ----------
box(ax1, 34, 53.5, 92, 61.5, C_ORANGE, alpha=0.10, lw=1.3, rounding=0.6)
ax1.text(63, 57.5, "→ 按 fixed 模式切", ha="center", va="center",
         fontsize=8.2, color=C_ORANGE, fontweight="bold")

arrow(ax1, (right_edge + 1.5, ROW_Y + ROW_H / 2),
      (92.6, ROW_Y + ROW_H / 2), color=C_ORANGE, lw=1.5)
arrow(ax1, (63, 53.0), (X0 + 60, ROW2_Y + ROW_H + 3), color=C_ORANGE,
      lw=1.5, rad=-0.10)

# ---------- 下排：切分后 3 个包 ----------
seg_lengths = [133, 8, 11]
seg_colors = [C_PURPLE, C_GREEN, C_PURPLE]
ROW_GAP = 5.6
labels = [
    ("第 1 段（替换原包）", "seq = S", "IP.id = id"),
    ("第 2 段（新构造）", "seq = S + 133", "IP.id = id + 1"),
    ("第 3 段（新构造）", "seq = S + 141", "IP.id = id + 2"),
]
offs = 0
seg_off = []
for k, ln in enumerate(seg_lengths):
    y = ROW2_Y - k * (ROW_H + ROW_GAP)
    bar_left_label(ax1, y, labels[k][0], seg_colors[k], labels[k][1])
    x = X0
    draw_header_cell(ax1, x, y, 7.6, ROW_H, "IP 头", C_BLUE,
                     "20 B" if k == 0 else "20 B (id+%d)" % k)
    x += 7.6
    draw_header_cell(ax1, x, y, 11.5, ROW_H, "TCP 头", C_BLUE,
                     "20 B" if k == 0 else "20 B")
    x += 11.5
    w = ln * SCALE
    ax1.add_patch(Rectangle((x, y), w, ROW_H, facecolor=tint(seg_colors[k], 0.38),
                            edgecolor=seg_colors[k], lw=1.2, zorder=3))
    txt = "%d B" % ln
    ax1.text(x + w / 2, y + ROW_H / 2, txt, ha="center", va="center",
             fontsize=9.0 if w > 34 else 7.6,
             color=C_INK if w > 34 else seg_colors[k], zorder=4,
             fontweight="bold")
    if k == 0:
        ax1.add_patch(Rectangle((x, y), 5 * SCALE, ROW_H, facecolor=C_RED,
                                edgecolor="none", zorder=4))
        ax1.annotate("记录头 5 B 完整落在第 1 段",
                     xy=(x + 2.5 * SCALE, y - 0.4),
                     xytext=(x, y - 3.4),
                     fontsize=7.2, color=C_RED, va="center", ha="left",
                     arrowprops=dict(arrowstyle="-", color=C_RED, lw=0.9))
    ax1.text(x + w + 1.0, y + ROW_H / 2,
             "%s → 偏移 %d-%d" % (labels[k][2], offs, offs + ln),
             ha="left", va="center", fontsize=7.1, color=C_GRAY)
    seg_off.append((offs, ln, x + w))
    offs += ln

# 在每段条形右端外面标出累计字节数，提示"3 段拼起来仍是同一段字节流"
for (o, ln, xr) in seg_off:
    if o + ln >= 152:
        continue
    ax1.text(xr + 6.0, ROW2_Y + ROW_H + 1.8,
             "累计 %d" % (o + ln), fontsize=6.6, color=C_GRAY,
             ha="left", va="center")

# ---------- 左侧竖线：说明三段载荷是同一段字节 ----------
x_left = X0 + 10.2
y_top = ROW2_Y + ROW_H
y_bot = ROW2_Y - 2 * (ROW_H + ROW_GAP)
ax1.add_patch(FancyArrowPatch((x_left, y_top + 5.2), (x_left, y_bot - 2.4),
                              arrowstyle="<|-|>", mutation_scale=9,
                              linewidth=0.9, color=C_GRAY,
                              linestyle=(0, (2, 2)), zorder=1))

# ---------- 左下：变化 / 不变量 表 ----------
tab_x, tab_y = 61.0, 26.0
box(ax1, tab_x - 3, tab_y - 4, 116, 57.0, C_INK, alpha=0.03, lw=1.0, rounding=0.7)
ax1.text(tab_x, 53.0, "切分前后：谁变了、谁没变", fontsize=10.4, color=C_INK,
         fontweight="bold", va="center")

rows = [
    ("", "切分前", "切分后"),
    ("TCP 段数", "1", "3"),
    ("IP 包总字节", "192 B", "272 B（+80 B 头部）"),
    ("载荷字节", "152 B", "152 B（拼接后等同）"),
    ("TCP seq", "S", "S / S+133 / S+141"),
    ("flags / options", "原样", "原样（3 段相同）"),
    ("IP.id", "id", "id / id+1 / id+2"),
    ("IP/TCP 校验和", "原值", "删除后重算"),
    ("记录头长度字段", "147", "147（仍在首段）"),
    ("接收端", "—", "按 seq 重组，无感"),
]
col_x = [tab_x, tab_x + 25, tab_x + 41]
yy = 48.6
for i, r in enumerate(rows):
    if i == 0:
        for cx, t in zip(col_x, r):
            ax1.text(cx, yy, t, fontsize=8.0, color=C_GRAY, fontweight="bold",
                     va="center")
    else:
        ax1.text(col_x[0], yy, r[0], fontsize=8.0, color=C_INK, va="center")
        ax1.text(col_x[1], yy, r[1], fontsize=8.0, color=C_GRAY, va="center")
        is_inv = r[2] in ("152 B（拼接后等同）", "147（仍在首段）",
                          "原样（3 段相同）") or "无感" in r[2]
        ax1.text(col_x[2], yy, r[2], fontsize=8.0,
                 color=C_GREEN if is_inv else C_RED, va="center")
    yy -= 4.4
ax1.plot([tab_x - 1, 115], [46.6 - 2.6, 46.6 - 2.6], color=C_LIGHT, lw=1.0, zorder=4)

ax1.text(tab_x, 5.6,
         "绿色 = 不变量（接收端语义不变）\n红色 = 变化量（本端可观测）",
         fontsize=7.6, color=C_GRAY, va="center", style="italic", linespacing=1.5)

# ---------- 右侧：原包 → 分段 的标题说明 ----------
ax1.text(122, 21.0,
         "三段共享同一段字节流；\nTCP seq 逐段累加，接收端\n按序重组后仍是完整 TLS 记录。",
         fontsize=8.0, color=C_INK, va="center", ha="left", linespacing=1.7)
ax1.text(122, 10.0, "标注的 IP.id / seq 偏移来自\nsplitter.py: send_segments()",
         fontsize=7.4, color=C_GRAY, va="center", ha="left", linespacing=1.6,
         style="italic")

# ==================================================== 下半：处理流水线
ax2 = fig.add_axes([0.02, 0.035, 0.96, 0.385])
ax2.set_xlim(0, 200)
ax2.set_ylim(0, 100)
ax2.axis("off")
ax2.set_title("② 数据面流水线：iptables → NFQUEUE → 过滤 → 切分 → 注入（executor/tcp_splitter）",
              fontsize=13.5, color=C_INK, loc="left", fontweight="bold", pad=10)

# 主链节点：(x0, x1, title, sub, color)
nodes = [
    (2, 27, "FORWARD 链", "iptables 匹配\n-p tcp -d 目标IP", C_BLUE),
    (33, 57, "NFQUEUE 1", "内核把匹配包\n排队到用户态", C_BLUE),
    (63, 92, "handle_packet()", "Scapy 解析\n（在节点下方逐条过滤）", C_ORANGE),
    (98, 128, "切分构造", "fixed: 152 → 133/8/11\nrandom: 按长度选 L1~L4", C_PURPLE),
    (134, 163, "回注网络", "第 1 段 set_payload\n后 2 段 send() 新建", C_GREEN),
    (169, 197, "接收端", "TCP 按 seq 重组\nTLS 记录完整可用", C_INK),
]
NY0, NY1 = 50.0, 72.0
for x0, x1, title, sub, color in nodes:
    box(ax2, x0, NY0, x1, NY1, color, alpha=0.09, lw=1.4, rounding=0.7)
    ax2.text((x0 + x1) / 2, NY1 - 6.0, title, ha="center", va="center",
             fontsize=9.6, color=color, fontweight="bold")
    ax2.text((x0 + x1) / 2, NY0 + 8.2, sub, ha="center", va="center",
             fontsize=7.4, color=C_GRAY, linespacing=1.55)

for i in range(len(nodes) - 1):
    y = (NY0 + NY1) / 2
    arrow(ax2, (nodes[i][1] + 0.6, y), (nodes[i + 1][0] - 0.6, y), color=C_INK)

# 5 道过滤：垂直挂在 handle_packet 下方
filters = [
    ("源 = 目标 IP？", "skip_target_src", "放行（防响应回声循环）"),
    ("src 不等于 src_filter？", "skip_src_filter", "放行"),
    ("dst 不在 targets / 无 Raw？", "packet_accept", "放行"),
    ("首字节不是 0x17？", "skip_non_tls", "放行（非 TLS AppData）"),
    ("random() 不小于 p？", "skip_pval", "放行（不切）"),
]
fy = 38.5
for i, (cond, cnt, act) in enumerate(filters):
    yy = fy - i * 5.4
    ax2.add_patch(Rectangle((64, yy - 1.5), 27, 4.2,
                            facecolor=tint(C_GRAY, 0.08), edgecolor="none", zorder=2))
    ax2.text(64.6, yy + 0.6, cond, fontsize=7.2, color=C_INK, va="center")
    ax2.text(92.4, yy + 0.6, "→ %s（%s）" % (act, cnt), fontsize=6.7,
             color=C_GRAY, va="center")
ax2.annotate("", xy=(77.5, fy + 1.0), xytext=(77.5, NY0 - 0.8),
             arrowprops=dict(arrowstyle="-|>", color=C_ORANGE, lw=1.2))
ax2.text(63.5, fy + 3.6, "命中任意一条即 packet.accept() 放行", fontsize=7.4,
         color=C_ORANGE, va="center")

# 失败兜底
box(ax2, 98, 6.0, 150, 18.0, C_RED, alpha=0.06, lw=1.1, rounding=0.6)
ax2.text(124, 14.6, "异常兜底：except → 打印 + packet.accept()",
         ha="center", va="center", fontsize=8.0, color=C_RED, fontweight="bold")
ax2.text(124, 9.6, "宁可少切一刀，也不丢包", ha="center", va="center",
         fontsize=7.4, color=C_GRAY)
arrow(ax2, (112, NY0 - 0.8), (112, 18.3), color=C_RED, lw=1.0, ls=":", rad=0.0)

# 熵测量旁路（虚线）
box(ax2, 154, 4.0, 197, 31.0, C_PURPLE, alpha=0.05, lw=1.0, rounding=0.6)
ax2.text(175.5, 27.4, "熵测量旁路（旁挂，不改包）", ha="center", va="center",
         fontsize=8.2, color=C_PURPLE, fontweight="bold")
ax2.text(175.5, 21.8,
         "record(dst, before_len, after_lengths)\nbefore 记原长，after 记各段长",
         ha="center", va="center", fontsize=7.0, color=C_GRAY, linespacing=1.5)
ax2.text(175.5, 13.2,
         "30 s 结算 shannon / Hmax / Hnorm\nGET /entropy/measure?duration=30",
         ha="center", va="center", fontsize=7.0, color=C_GRAY, linespacing=1.5)
arrow(ax2, (110, NY0 - 0.8), (166, 31.4), color=C_PURPLE, lw=1.0,
      ls=(0, (3, 2)), rad=-0.25)

# 控制面：Flask :5055（虚线箭头指向 NFQUEUE / 切分）
box(ax2, 2, 4.0, 52, 30.0, C_INK, alpha=0.03, lw=1.0, rounding=0.6)
ax2.text(27, 25.6, "控制面 Flask :5055", ha="center", va="center",
         fontsize=8.2, color=C_INK, fontweight="bold")
ax2.text(27, 17.4,
         "POST /start  设置 dst_ips + 装规则\nPOST /config  {p_value, segment_mode,\n"
         "              segment_count}（version+1）\nPOST /stop   清规则 + unbind",
         ha="center", va="center", fontsize=7.0, color=C_GRAY, linespacing=1.5)
arrow(ax2, (45, 30.4), (45, NY0 - 0.8), color=C_INK, lw=1.0, ls=(0, (3, 2)))
arrow(ax2, (52.5, 17.4), (98, 21.0), color=C_INK, lw=1.0, ls=(0, (3, 2)),
      rad=-0.12)

# 底部注释
ax2.text(2, 0.4,
         "关键不变量：只改包长与分段，不改载荷内容 → 接收端无需任何恢复逻辑；"
         "seq 连续性由 send_segments() 逐段累加保证。",
         fontsize=7.8, color=C_GRAY, style="italic", va="bottom")

fig.savefig(OUT, bbox_inches="tight", pad_inches=0.18, facecolor="white")
print("wrote", OUT)

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

版本说明（v2：重排版面）
    初版把「变化对照表」压在分段条形上，filter 列表与兜底/旁路框互相交叠，
    上下两半高度也不均衡。本版改为：
      上半 = 左「封包条形」+ 右「变化对照表」两列互不侵占，表格本身画成真表格；
      下半 = 主链一行 + 下方两个并列分区（左：过滤链与兜底，右：控制面 / 旁路）。
    语料层面只做同一件事：只改包长与分段，不改载荷内容。

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


def box(ax, x0, y0, x1, y1, edge, alpha=0.07, lw=1.4, rounding=0.45, pad=0.0,
        fc=None, zorder=2):
    ax.add_patch(FancyBboxPatch(
        (x0, y0), x1 - x0, y1 - y0,
        boxstyle="round,pad=%.2f,rounding_size=%.2f" % (pad, rounding),
        linewidth=lw, edgecolor=edge,
        facecolor=fc if fc is not None else tint(edge, alpha), zorder=zorder))


def arrow(ax, p0, p1, color=C_INK, lw=1.4, ls="-", style="-|>", rad=0.0):
    ax.add_patch(FancyArrowPatch(
        p0, p1, arrowstyle=style, mutation_scale=12, linewidth=lw,
        color=color, linestyle=ls, zorder=5, shrinkA=1, shrinkB=1,
        connectionstyle="arc3,rad=%.2f" % rad))


# =============================================================== 画布
# 画布按 200 × 175 的虚拟网格排版：上半 0~100，下半 103~175。
# ax1 / ax2 共用同一个 x 轴，左右边界对齐。
fig = plt.figure(figsize=(15.0, 13.1))

GRID_X, GRID_Y = 200.0, 175.0
FIG_W, FIG_H = 15.0, 13.1
IN = (FIG_W / GRID_X, FIG_H / GRID_Y)     # 1 网格单位对应的英寸数

ax1 = fig.add_axes([0.03, 0.415, 0.94, 0.545])
ax1.set_xlim(0, GRID_X)
ax1.set_ylim(0, 100)
ax1.set_aspect(IN[0] / IN[1])             # 保证 1 单位 x == 1 单位 y（不被拉伸）
ax1.axis("off")

ax2 = fig.add_axes([0.03, 0.035, 0.94, 0.335])
ax2.set_xlim(0, GRID_X)
ax2.set_ylim(103, 175)
ax2.set_aspect(IN[0] / IN[1])
ax2.axis("off")

# ==================================================== 上半：协议栈封装对照
ax1.set_title("① 协议栈视角：一个 TLS 记录被切成 3 个 TCP 段（载荷字节序不变，接收端 TCP 自动重组）",
              fontsize=13.5, color=C_INK, loc="left", fontweight="bold", pad=12)

X0 = 17.0                         # 条形起点（左侧留给段标签）
SCALE = 0.54                      # 每字节占多少画布单位IP_W, TCP_W = 6.0, 9.0            # 头部色块宽度（纯示意，不按比例）
ROW_H = 9.0                       # 条形高度

# 右侧表格（与条形严格分列，不再互相压盖）
TAB_X0, TAB_X1 = 121.0, 197.0
TAB_COL = (TAB_X0, 141.0, 154.0)  # 字段 / 切分前 / 切分后
TAB_TOP, TAB_BOT = 88.0, 4.0


def seg_label(ax, y, title, color, sub):
    ax.text(X0 - 1.5, y + ROW_H / 2 + 1.4, title, ha="right", va="center",
            fontsize=10.0, color=color, fontweight="bold")
    ax.text(X0 - 1.5, y + ROW_H / 2 - 2.6, sub, ha="right", va="center",
            fontsize=7.6, color=C_GRAY)


def seg_label_right(ax, y, title, color, sub):
    """第 2 段起改用右对齐标签：条短、右侧空白多，避免压到下一行。"""
    ax.text(80.0, y + ROW_H / 2 + 1.4, title, ha="left", va="center",
            fontsize=10.0, color=color, fontweight="bold")
    ax.text(80.0, y + ROW_H / 2 - 2.6, sub, ha="left", va="center",
            fontsize=7.6, color=C_GRAY)


def header_cell(ax, x, y, w, label, sub=None, fs=7.6):
    ax.add_patch(Rectangle((x, y), w, ROW_H, facecolor=tint(C_BLUE, 0.30),
                           edgecolor=C_BLUE, lw=1.1, zorder=3))
    ax.text(x + w / 2, y + ROW_H / 2 + (1.8 if sub else 0), label,
            ha="center", va="center", fontsize=fs, color=C_INK, zorder=4)
    if sub:
        ax.text(x + w / 2, y + ROW_H / 2 - 2.6, sub, ha="center", va="center",
                fontsize=6.8, color=C_GRAY, zorder=4)


# ---------- 上排：切分前 1 个包 ----------
Y_TOP = 73.0
seg_label(ax1, Y_TOP, "切分前", C_GRAY, "1 帧 / 1 段")

x = X0
header_cell(ax1, x, Y_TOP, IP_W, "IP 头", "20 B")
x += IP_W
header_cell(ax1, x, Y_TOP, TCP_W, "TCP 头", "20 B", fs=7.0)
x += TCP_W

rec_x = x
tls_hdr_w = 5 * SCALE
ax1.add_patch(Rectangle((rec_x, Y_TOP), tls_hdr_w, ROW_H, facecolor=C_RED,
                        edgecolor="none", zorder=3))
ax1.add_patch(Rectangle((rec_x + tls_hdr_w, Y_TOP), 147 * SCALE, ROW_H,
                        facecolor=tint(C_RED, 0.18), edgecolor=C_RED, lw=1.1, zorder=3))
ax1.text(rec_x + tls_hdr_w + 147 * SCALE / 2, Y_TOP + ROW_H / 2,
         "TLS 记录载荷 147 B（密文，内容不变）",
         ha="center", va="center", fontsize=8.8, color=C_INK, zorder=4)
ax1.annotate("记录头 5 B\n(0x17 + 版本 + 长度)",
             xy=(rec_x + tls_hdr_w / 2, Y_TOP + ROW_H),
             xytext=(rec_x + 16, Y_TOP + ROW_H + 7.5),
             fontsize=7.4, color=C_RED, ha="left", va="center", linespacing=1.35,
             arrowprops=dict(arrowstyle="-", color=C_RED, lw=0.9,
                             connectionstyle="angle3,angleA=90,angleB=0"))

right_edge = rec_x + tls_hdr_w + 147 * SCALE
ax1.text(right_edge + 1.6, Y_TOP + ROW_H / 2 + 1.4, "总长",
         ha="left", va="center", fontsize=8.0, color=C_INK, fontweight="bold")
ax1.text(right_edge + 1.6, Y_TOP + ROW_H / 2 - 1.6, "192 B",
         ha="left", va="center", fontsize=8.0, color=C_INK, fontweight="bold")
ax1.text(X0 - 1.5, Y_TOP - 4.4, "载荷偏移 0 … 152",
         ha="right", va="center", fontsize=7.0, color=C_GRAY)

# ---------- 中间：切分动作（横向箭头 + 模式标签）----------
Y_ARROW = 61.6
ax1.annotate("", xy=(X0 + 30, Y_ARROW), xytext=(X0 + 3, Y_ARROW),
             arrowprops=dict(arrowstyle="-|>", color=C_ORANGE, lw=1.6))
ax1.text(X0 + 33, Y_ARROW, "fixed 模式：152 B → 133 / 8 / 11",
         ha="left", va="center", fontsize=8.6, color=C_ORANGE, fontweight="bold")
ax1.text(X0 + 3, Y_ARROW + 3.4, "按固定长度切；random 模式则按长度区间选 L1~L4",
         ha="left", va="center", fontsize=7.2, color=C_GRAY)

# ---------- 下排：切分后 3 个包 ----------
seg_lengths = [133, 8, 11]
seg_colors = [C_PURPLE, C_GREEN, C_PURPLE]
ROW_GAP = 5.0
Y_SEG0 = 44.0
Y_SEG_RIGHT_LABEL = 22.0          # 右侧标签的起点 y（第 2 段起标签改放右侧）
LABEL_X_RIGHT = 80.0
labels = [
    ("第 1 段（替换原包）", "seq = S", "IP.id = id"),
    ("第 2 段（新构造）", "seq = S + 133", "IP.id = id + 1"),
    ("第 3 段（新构造）", "seq = S + 141", "IP.id = id + 2"),
]

offs = 0
seg_right = []
for k, ln in enumerate(seg_lengths):
    y = Y_SEG0 - k * (ROW_H + ROW_GAP)
    if k == 0:
        seg_label(ax1, y, labels[k][0], seg_colors[k], labels[k][1])
    else:
        seg_label_right(ax1, y, labels[k][0], seg_colors[k], labels[k][1])
    x = X0
    header_cell(ax1, x, y, IP_W, "IP 头", "20 B" if k == 0 else "id+%d" % k)
    x += IP_W
    header_cell(ax1, x, y, TCP_W, "TCP 头", "+20 B")
    x += TCP_W
    w = ln * SCALE
    ax1.add_patch(Rectangle((x, y), w, ROW_H, facecolor=tint(seg_colors[k], 0.36),
                            edgecolor=seg_colors[k], lw=1.2, zorder=3))
    ax1.text(x + w / 2, y + ROW_H / 2, "%d B" % ln, ha="center", va="center",
             fontsize=8.8 if w > 30 else 7.2,
             color=C_INK if w > 30 else seg_colors[k], zorder=4, fontweight="bold")
    if k == 0:  # 5 B 记录头完整落在第 1 段
        hdr_w = 5 * SCALE
        ax1.add_patch(Rectangle((x, y), hdr_w, ROW_H, facecolor=C_RED,
                                edgecolor="none", zorder=4))
    ax1.text(x + w + 1.2, y + ROW_H / 2,
             "%s → 偏移 %d–%d" % (labels[k][2], offs, offs + ln),
             ha="left", va="center", fontsize=6.6, color=C_GRAY)
    if k == 0:  # 记录头标注放在条形正上方（第 1 段顶部无其它内容）
        ax1.annotate("记录头 5 B 完整落在第 1 段",
                     xy=(x + 2.5 * SCALE, y + ROW_H / 2),
                     xytext=(x + 39.5, y + ROW_H + 0.8),
                     fontsize=7.0, color=C_RED, ha="center", va="bottom",
                     arrowprops=dict(arrowstyle="-", color=C_RED, lw=0.9,
                                     connectionstyle="angle3,angleA=90,angleB=0"))
    seg_right.append((x + w, offs + ln))
    offs += ln

# 段尾累计字节：把「三段拼起来仍是同一段字节流」画成一条递进虚线
for (xr, cum) in seg_right[:-1]:
    ax1.text(xr + 1.2, Y_SEG0 - 2.6, "累计 %d B" % cum,
             fontsize=6.6, color=C_GRAY, ha="left", va="top")

# 左侧竖虚线：三段载荷是同一段字节流
xl = X0 + 4.0
ax1.add_patch(FancyArrowPatch((xl, Y_SEG0 + ROW_H + 0.4),
                              (xl, Y_SEG0 - 2 * (ROW_H + ROW_GAP) - 0.4),
                              arrowstyle="<|-|>", mutation_scale=8,
                              linewidth=0.9, color=C_GRAY,
                              linestyle=(0, (2, 2)), zorder=1))

# 左侧底部：一句话结论
ax1.text(xl + 3.0, 18.4,
         "三段共享同一段字节流：TCP seq 逐段累加，\n"
         "接收端按序重组后仍是完整 TLS 记录，应用层无感。",
         fontsize=8.0, color=C_INK, va="top", ha="left", linespacing=1.7)

# ---------- 右侧：变化 / 不变量 表 ----------
TAB_TOP = 84.0
TAB_BOT = 10.0
box(ax1, TAB_X0 - 3.5, TAB_BOT, TAB_X1, TAB_TOP, C_INK, alpha=0.025, lw=1.0,
    rounding=0.8)

ax1.text(TAB_X0, TAB_TOP - 4.8, "切分前后：谁变了、谁没变", fontsize=10.4,
         color=C_INK, fontweight="bold", va="center")

rows = [
    ("TCP 段数", "1", "3"),
    ("IP 包总字节", "192 B", "272 B（+80 B 头）"),
    ("载荷字节", "152 B", "152 B（拼接等同）"),
    ("TCP seq", "S", "S / S+133 / S+141"),
    ("flags / options", "原样", "原样（3 段相同）"),
    ("IP.id", "id", "id / id+1 / id+2"),
    ("IP/TCP 校验和", "原值", "删除后重算"),
    ("记录头长度字段", "147", "147（仍在首段）"),
    ("接收端", "—", "按 seq 重组，无感"),
]
INVARIANT = {"152 B（拼接等同）", "原样（3 段相同）", "147（仍在首段）",
             "按 seq 重组，无感"}

ROW_STEP = 6.6
HEAD_Y = TAB_TOP - 9.8
TAB_L, TAB_R = TAB_X0 - 2.2, TAB_X1 - 2.2
ax1.plot([TAB_L, TAB_R], [HEAD_Y + 2.6, HEAD_Y + 2.6],
         color=C_LIGHT, lw=1.2, zorder=4)
for cx, t in zip(TAB_COL, ("字段", "切分前", "切分后")):
    ax1.text(cx, HEAD_Y, t, fontsize=8.0, color=C_GRAY, fontweight="bold",
             va="center")

yy = HEAD_Y - ROW_STEP
for i, (name, before, after) in enumerate(rows):
    if i % 2 == 0:
        ax1.add_patch(Rectangle((TAB_L, yy - ROW_STEP / 2 + 1.0),
                                TAB_R - TAB_L, ROW_STEP - 2.0,
                                facecolor=tint(C_INK, 0.03), edgecolor="none",
                                zorder=1))
    ax1.text(TAB_COL[0], yy, name, fontsize=8.0, color=C_INK, va="center")
    ax1.text(TAB_COL[1], yy, before, fontsize=8.0, color=C_GRAY, va="center")
    ax1.text(TAB_COL[2], yy, after, fontsize=8.0, va="center",
             color=C_GREEN if after in INVARIANT else C_RED)
    yy -= ROW_STEP

ax1.text(TAB_X0, yy - 1.2,
         "绿色 = 不变量（接收端语义不变）    红色 = 变化量（本端可观测）",
         fontsize=7.2, color=C_GRAY, va="center")
ax1.text(TAB_X0, TAB_BOT + 2.6,
         "IP.id / seq 偏移来自 splitter.py: send_segments()",
         fontsize=6.8, color=C_GRAY, va="center", style="italic")
ax1.text(TAB_X0, TAB_BOT + 6.6,
         "三段拼接后 = 原 152 B 字节流，顺序与内容均未改变。",
         fontsize=7.2, color=C_INK, va="center")

# ==================================================== 下半：处理流水线
ax2.set_title("② 数据面流水线：iptables → NFQUEUE → 过滤 → 切分 → 注入（executor/tcp_splitter）",
              fontsize=13.5, color=C_INK, loc="left", fontweight="bold", pad=12)

nodes = [
    (2, 28, "FORWARD 链", "iptables 匹配\n-p tcp -d 目标IP", C_BLUE),
    (33, 59, "NFQUEUE 1", "内核把匹配包\n排队到用户态", C_BLUE),
    (64, 94, "handle_packet()", "Scapy 解析\n逐条过滤（见图下）", C_ORANGE),
    (99, 129, "切分构造", "fixed / random\n选 L1~L4 长度", C_PURPLE),
    (134, 164, "回注网络", "第 1 段 set_payload\n后 2 段 send() 新建", C_GREEN),
    (169, 197, "接收端", "TCP 按 seq 重组\nTLS 记录完整可用", C_INK),
]
NY0, NY1 = 146.0, 168.0
for x0, x1, title, sub, color in nodes:
    box(ax2, x0, NY0, x1, NY1, color, alpha=0.09, lw=1.4, rounding=0.7)
    ax2.text((x0 + x1) / 2, NY1 - 5.6, title, ha="center", va="center",
             fontsize=9.4, color=color, fontweight="bold")
    ax2.text((x0 + x1) / 2, NY0 + 7.4, sub, ha="center", va="center",
             fontsize=7.2, color=C_GRAY, linespacing=1.55)

for i in range(len(nodes) - 1):
    y = (NY0 + NY1) / 2
    arrow(ax2, (nodes[i][1] + 0.6, y), (nodes[i + 1][0] - 0.6, y), color=C_INK)

# ---------- 左下：过滤链（挂在 handle_packet 正下方）+ 异常兜底 ----------
FIL_X0, FIL_X1 = 2.0, 100.0
box(ax2, FIL_X0, 106.0, FIL_X1, 141.0, C_ORANGE, alpha=0.045, lw=1.1, rounding=0.8)
ax2.text(FIL_X0 + 3.0, 137.4, "过滤链：命中任意一条即 packet.accept() 放行",
         fontsize=8.2, color=C_ORANGE, fontweight="bold", va="center")

arrow(ax2, (79.0, NY0 - 0.8), (79.0, 141.2), color=C_ORANGE, lw=1.2)

filters = [
    ("源 = 目标 IP？", "skip_target_src", "放行：防响应回声循环"),
    ("src 不等于 src_filter？", "skip_src_filter", "放行"),
    ("dst 不在 targets / 无 Raw？", "packet_accept", "放行"),
    ("首字节不是 0x17？", "skip_non_tls", "放行：非 TLS AppData"),
    ("random() 不小于 p？", "skip_pval", "放行：不切"),
]
fy = 129.0
for i, (cond, cnt, act) in enumerate(filters):
    yy = fy - i * 4.2
    ax2.text(FIL_X0 + 3.0, yy, "%d  %s" % (i + 1, cond), fontsize=7.2,
             color=C_INK, va="center")
    ax2.text(FIL_X0 + 3.0, yy - 2.1, "→ %s（%s）" % (act, cnt), fontsize=6.5,
             color=C_GRAY, va="center")

# 兜底：与过滤链同区，放在链尾
box(ax2, FIL_X0 + 3.0, 105.4, FIL_X1 - 3.0, 110.2, C_RED, alpha=0.07, lw=1.0,
    rounding=0.5)
ax2.text((FIL_X0 + FIL_X1) / 2, 108.8, "异常兜底：except → 打印 + packet.accept()",
         ha="center", va="center", fontsize=7.2, color=C_RED, fontweight="bold")
ax2.text((FIL_X0 + FIL_X1) / 2, 106.3, "宁可少切一刀，也不丢包",
         ha="center", va="center", fontsize=6.4, color=C_GRAY)

# ---------- 右下：并列两个小分区（控制面 / 熵测量旁路）----------
box(ax2, 106.0, 105.0, 152.0, 138.0, C_INK, alpha=0.025, lw=1.0, rounding=0.7)
ax2.text(129.0, 134.6, "控制面 Flask :5055", ha="center", va="center",
         fontsize=8.0, color=C_INK, fontweight="bold")
ax2.text(129.0, 119.6,
         "POST /start\n设置 dst_ips + 装规则\n\n"
         "POST /config\n{p_value, segment_mode,\n segment_count}（version+1）\n\n"
         "POST /stop\n清规则 + unbind",
         ha="center", va="center", fontsize=6.5, color=C_GRAY, linespacing=1.4)

box(ax2, 157.0, 105.0, 197.0, 138.0, C_PURPLE, alpha=0.045, lw=1.0, rounding=0.7)
ax2.text(177.0, 134.6, "熵测量旁路（旁挂，不改包）", ha="center", va="center",
         fontsize=8.0, color=C_PURPLE, fontweight="bold")
ax2.text(177.0, 119.6,
         "record(dst, before_len,\n         after_lengths)\n"
         "before 原长 / after 各段长\n\n"
         "30 s 结算 shannon / Hmax / Hnorm\n"
         "GET /entropy/measure?duration=30",
         ha="center", va="center", fontsize=6.5, color=C_GRAY, linespacing=1.45)

# 两条虚连线：控制面 → NFQUEUE（装规则/绑队列）；handle_packet → 旁路（只读上报）
arrow(ax2, (112.0, 138.2), (112.0, NY0 - 0.8), color=C_INK, lw=1.0,
      ls=(0, (3, 2)))
ax2.text(110.4, 140.6, "装规则 / 改 p", fontsize=6.2, color=C_INK,
         va="center", ha="right")
arrow(ax2, (95.0, NY0 - 0.8), (168.0, 138.2), color=C_PURPLE, lw=1.0,
      ls=(0, (3, 2)), rad=-0.18)
ax2.text(135.0, 143.6, "只读上报 record()", fontsize=6.2, color=C_PURPLE,
         va="center", ha="center")

# 底部注释
ax2.text(2, 103.4,
         "关键不变量：只改包长与分段，不改载荷内容 → 接收端无需任何恢复逻辑；"
         "seq 连续性由 send_segments() 逐段累加保证。",
         fontsize=7.6, color=C_GRAY, style="italic", va="bottom")

fig.savefig(OUT, bbox_inches="tight", pad_inches=0.18, facecolor="white")
print("wrote", OUT)

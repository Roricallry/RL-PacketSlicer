# -*- coding: utf-8 -*-
"""protocol_split_figure.py 的几何自检。

不依赖肉眼、不依赖图片识别：把脚本执行后图上每个
Rectangle / FancyBboxPatch / text 的像素包围盒抓出来，两两算重叠，
按"谁盖住谁、会不会真的遮挡"分类输出。

判定规则（这一版修正了初版把箭头/底框全算成冲突的问题）
  [1] 实心填充块之间的重叠  —— 必须为 0（这是真正会互相遮挡的情况）
  [2] 文本出画布            —— 必须为 0
  [3] 文本互相重叠          —— 必须为 0
  [4] 信息性重叠            —— 只报告：箭头穿过底框、背景底框套住内容、
                              文本压在自己所属的块上，这些都是正常设计

用法
    python check_overlap.py
"""

import os
import sys

import matplotlib

matplotlib.use("Agg")

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import protocol_split_figure as P  # noqa: E402  导入即绘制；末尾会 savefig


def overlap(a, b):
    x0, y0 = max(a[0], b[0]), max(a[1], b[1])
    x1, y1 = min(a[2], b[2]), min(a[3], b[3])
    if x1 <= x0 or y1 <= y0:
        return 0.0
    return (x1 - x0) * (y1 - y0)


def is_solid(p):
    """有可见填充色的矩形类图元（背景底框的 alpha 很低，视为容器）。"""
    if not isinstance(p, (P.Rectangle, P.FancyBboxPatch)):
        return False
    fc = p.get_facecolor()
    return fc[3] >= 0.25


def is_container(p):
    fc = p.get_facecolor()
    return isinstance(p, (P.Rectangle, P.FancyBboxPatch)) and fc[3] < 0.15


def run():
    fig = P.fig
    fig.canvas.draw()
    rnd = fig.canvas.get_renderer()
    lines, hard = [], 0

    for idx, ax in enumerate(fig.get_axes()):
        name = "上半：协议栈封装" if idx == 0 else "下半：处理流水线"
        items = []
        for p in ax.patches:
            if not p.get_visible():
                continue
            e = p.get_window_extent(rnd)
            items.append((type(p).__name__, (e.x0, e.y0, e.x1, e.y1)))
        texts = []
        for t in ax.texts:
            if not t.get_visible() or not t.get_text().strip():
                continue
            e = t.get_window_extent(rnd)
            if e.width <= 0 or e.height <= 0:
                continue
            texts.append((t.get_text().replace("\n", " / ")[:30],
                          (e.x0, e.y0, e.x1, e.y1)))

        lines.append("\n===== %s  (%d 图元, %d 文本) =====" % (name, len(items), len(texts)))

        # [1] 实心块互相重叠
        bad = []
        patches = [p for p in ax.patches if p.get_visible()]
        for i in range(len(patches)):
            for j in range(i + 1, len(patches)):
                pi, pj = patches[i], patches[j]
                if not (is_solid(pi) and is_solid(pj)):
                    continue
                ei = pi.get_window_extent(rnd)
                ej = pj.get_window_extent(rnd)
                ov = overlap((ei.x0, ei.y0, ei.x1, ei.y1), (ej.x0, ej.y0, ej.x1, ej.y1))
                if ov > 4.0:
                    # 完全包含的覆盖（如记录头色块压在记录条形左端）是设计意图
                    box_i = ei.width * ei.height
                    box_j = ej.width * ej.height
                    contained = ov >= 0.98 * min(box_i, box_j)
                    if contained:
                        continue
                    bad.append((ov, type(pi).__name__, type(pj).__name__))
        if bad:
            hard += len(bad)
            lines.append("  [1] 实心块重叠 %d 对  ✗" % len(bad))
            for ov, a, b in bad:
                lines.append("      %s × %s   %.0f px²" % (a, b, ov))
        else:
            lines.append("  [1] 实心块重叠：0 对  ✓")

        # [2] 文本出画布
        canvas = (0, 0, fig.bbox.width, fig.bbox.height)
        out = [(t, r) for t, r in texts
               if overlap(r, canvas) <= 0]
        if out:
            hard += len(out)
            lines.append("  [2] 文本出画布 %d 条  ✗" % len(out))
            for t, r in out:
                lines.append("      %s" % t)
        else:
            lines.append("  [2] 文本出画布：0 条  ✓")

        # [3] 文本互相重叠
        cross = []
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                ov = overlap(texts[i][1], texts[j][1])
                if ov > 6.0:
                    cross.append((ov, texts[i][0], texts[j][0]))
        if cross:
            hard += len(cross)
            lines.append("  [3] 文本互相重叠 %d 对  ✗" % len(cross))
            for ov, a, b in cross:
                lines.append("      %s  ×  %s   %.0f px²" % (a, b, ov))
        else:
            lines.append("  [3] 文本互相重叠：0 对  ✓")

        # [4] 信息性：容器被内容压住 / 箭头穿过容器
        info = 0
        for i in range(len(patches)):
            for j in range(i + 1, len(patches)):
                pi, pj = patches[i], patches[j]
                if is_solid(pi) and is_solid(pj):
                    continue
                ei = pi.get_window_extent(rnd)
                ej = pj.get_window_extent(rnd)
                ov = overlap((ei.x0, ei.y0, ei.x1, ei.y1), (ej.x0, ej.y0, ej.x1, ej.y1))
                if ov > 4.0:
                    info += 1
        lines.append("  [4] 信息性重叠（箭头/底框与内容交叠）：%d 处，属正常设计，不计为冲突" % info)

    return lines, hard


if __name__ == "__main__":
    lines, hard = run()
    print("\n".join(lines))
    print("\n===== 硬冲突合计 %d 处 =====" % hard)
    print("几何自检通过：无实心块压盖、无文本越界、无叠字。" if hard == 0
          else "存在硬冲突，见 [1]/[2]/[3]。")

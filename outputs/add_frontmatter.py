# -*- coding: utf-8 -*-
"""Insert standardized YAML frontmatter into notes lacking it (preserves BOM, line endings)."""
import io, os, sys

ROOT = r"E:\Node\RL-PacketSlicer\repository"

def build(meta):
    lines = ["---"]
    lines.append(f"title: {meta['title']}")
    lines.append("aliases:")
    for a in meta["aliases"]:
        lines.append(f"  - {a}")
    lines.append("tags:")
    for t in meta["tags"]:
        lines.append(f"  - {t}")
    lines.append(f"type: {meta['type']}")
    lines.append(f"status: {meta['status']}")
    lines.append(f"created: {meta['created']}")
    if meta.get("source"):
        lines.append(f"source: {meta['source']}")
    lines.append("---")
    return "\r\n".join(lines) + "\r\n\r\n"

NOTES = {
    "iperf3.md": dict(
        title="iperf3", aliases=["iperf3", "Iperf3"], type="tool", status="developing",
        tags=["工具/网络测试", "工具/性能测量", "网络/带宽测量"],
    ),
    "TLS.md": dict(
        title="TLS", aliases=["TLS 协议", "Transport Layer Security", "记录层", "握手层"],
        type="concept", status="developing",
        tags=["网络安全/协议", "网络安全/加密", "网络协议/传输层"],
    ),
    "Z-score.md": dict(
        title="Z-score", aliases=["标准分数", "z 分数", "标准化"], type="method", status="evergreen",
        tags=["统计/预处理", "统计/标准化"],
    ),
    "上下文赌博机（Contextual Bandit）.md": dict(
        title="上下文赌博机（Contextual Bandit）", aliases=["Contextual Bandit", "上下文多臂赌博机", "LinUCB"],
        type="concept", status="developing",
        tags=["机器学习/强化学习", "机器学习/在线学习", "机器学习/探索-利用"],
    ),
    "信息熵（香农熵）.md": dict(
        title="信息熵（香农熵）", aliases=["信息熵", "香农熵", "Shannon Entropy", "Entropy"],
        type="concept", status="developing",
        tags=["数学/信息论", "数学/概率论"],
    ),
    "四分位距法（IQR）.md": dict(
        title="四分位距法（IQR）", aliases=["IQR", "四分位距", "Interquartile Range", "箱线图法"],
        type="method", status="developing",
        tags=["统计/描述统计", "统计/异常值检测"],
    ),
    "强化学习（RL）.md": dict(
        title="强化学习（RL）", aliases=["Reinforcement Learning", "RL"],
        type="concept", status="developing",
        tags=["机器学习/强化学习"],
    ),
    "相对于baseline的标准化.md": dict(
        title="相对于 baseline 的标准化", aliases=["baseline 标准化", "Baseline-normalized z-score"],
        type="method", status="seed",
        tags=["统计/标准化", "网络/流量分析", "网络/基线度量"],
    ),
    "软演员-评论家算法（CSAC）.md": dict(
        title="软演员-评论家算法（CSAC）", aliases=["SAC", "Soft Actor-Critic", "SAC-Lagrangian", "Constrained SAC"],
        type="method", status="developing",
        tags=["机器学习/强化学习", "机器学习/约束优化"],
    ),
    "metric_theoretical_foundation.md": dict(
        title="空口分帧混淆度量的理论基础", aliases=["metric_theoretical_foundation", "log2 W / n 度量"],
        type="doc", status="developing",
        tags=["网络/流量分析", "网络/空口分帧", "数学/信息论"],
    ),
}

if __name__ == "__main__":
    # created dates from file metadata (local time), passed as YYYY-MM-DD via mapping below
    created = {
        "iperf3.md": "2026-09-08",
        "TLS.md": "2026-09-08",
        "Z-score.md": "2026-09-08",
        "上下文赌博机（Contextual Bandit）.md": "2026-09-29",
        "信息熵（香农熵）.md": "2026-09-08",
        "四分位距法（IQR）.md": "2026-09-08",
        "强化学习（RL）.md": "2026-09-08",
        "相对于baseline的标准化.md": "2026-09-08",
        "软演员-评论家算法（CSAC）.md": "2026-09-08",
        "metric_theoretical_foundation.md": "2026-10-18",
    }
    for name, meta in NOTES.items():
        path = os.path.join(ROOT, name)
        with io.open(path, "r", encoding="utf-8-sig", newline="") as f:
            raw = f.read()
        if raw.lstrip().startswith("---"):
            print(f"SKIP (has frontmatter): {name}")
            continue
        meta["created"] = created[name]
        # drop leading blank lines so frontmatter sits on line 1
        body = raw.lstrip("\r\n")
        out = build(meta) + body
        with io.open(path, "w", encoding="utf-8-sig", newline="") as f:
            f.write(out)
        print(f"OK: {name}")

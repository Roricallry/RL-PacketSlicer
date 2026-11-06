

```python
decide(u, state):
    bm  = buckets[bucket_key(u)]              # U 按 10 分桶
    x   = features(state)                     # [1, u60, prev_a, prev_r, prev_tls,
                                              #  prev_viol, t_norm, roll3_r, roll3_tls]
    allowed = ACTIONS - blocked(bm)           # 安全门，不属于 CB 本体
    if 还有动作没跑过: 轮流选它                 # FORCE_SWEEP
    else:
        for a in allowed:
            w_a ~ N(mean_a, σ²·A_a⁻¹)         # Thompson
        chosen = argmax_a (w_a · x)
    return chosen, x                          # x 回传，保证决策/更新同口径

observe(u, p, reward, tls, x):
    a = 离 p 最近的训练动作
    A_a += x xᵀ
    b_a += x·y
    ss_a += (y - xᵀw_old)² ; df_a += 1
    # TLS 只进安全门，不进奖励回归
```
---
title: Dirichlet 分布
aliases:
  - 狄利克雷分布
  - Dirichlet Distribution
  - Dirichlet
tags:
  - 数学/概率论
  - 机器学习
  - 网络安全/流量分析
type: concept
status: developing
created: 2026-10-18
---

# Dirichlet 分布（狄利克雷分布）

## 1. 基本概念

### 1.1 定义

**Dirichlet 分布是一种定义在概率向量上的连续多元概率分布，可以生成一组非负且总和为 1 的随机比例。**

假设需要生成 $K$ 个比例，组成向量：

$$  
\mathbf{x}=(x_1,x_2,\ldots,x_K)  
$$

这些比例满足：

$$  
x_i\geq 0,\qquad \sum_{i=1}^{K}x_i=1  
$$

例如：

$$  
\mathbf{x}=(0.1,0.2,0.5,0.2)  
$$

其中：

$$  
0.1+0.2+0.5+0.2=1  
$$

这组数可以表示概率分布、资源分配比例，也可以用于将固定长度的数据划分为多个部分。

### 1.2 直观理解

假设有 1000 Byte 的数据，需要分成 4 份。

如果生成的比例为：

$$  
\mathbf{x}=(0.1,0.2,0.5,0.2)  
$$

那么各份长度为：

$$  
\mathbf{L}=1000\mathbf{x}  
$$

即：

$$  
\mathbf{L}=(100,200,500,200)  
$$

因此，Dirichlet 分布的核心思路是：

1. 根据参数随机生成一组比例。
    
2. 将比例乘以总长度。
    
3. 转换为实际的整数长度。
    
4. 必要时进行约束修正。
    

**核心特点：总量固定，各部分比例随机变化。**

---

## 2. 数学定义

### 2.1 概率密度函数

假设随机向量满足：

$$  
\mathbf{x}\sim\operatorname{Dirichlet}(\boldsymbol{\alpha})  
$$

其中参数向量为：

$$  
\boldsymbol{\alpha}=(\alpha_1,\alpha_2,\ldots,\alpha_K)  
$$

且：

$$  
\alpha_i>0  
$$

Dirichlet 分布的概率密度函数为：

$$\frac{1}{B(\boldsymbol{\alpha})}  
\prod_{i=1}^{K}x_i^{\alpha_i-1} $$
$$

其中，多元 Beta 函数为：

\frac{\prod_{i=1}^{K}\Gamma(\alpha_i)}  
{\Gamma\left(\sum_{i=1}^{K}\alpha_i\right)}  
$$

这里：

- $K$：比例的数量，也就是向量的维数。
    
- $x_i$：第 $i$ 个比例。
    
- $\alpha_i$：第 $i$ 个分量对应的浓度参数。
    
- $\Gamma(\cdot)$：Gamma 函数，是阶乘在实数范围内的推广。
    
- $B(\boldsymbol{\alpha})$：归一化常数。
    

变量必须满足：

$$  
x_i\geq 0,\qquad \sum_{i=1}^{K}x_i=1  
$$

不需要直接计算这个概率密度函数，也可以使用 NumPy 等工具进行采样。

### 2.2 对称 Dirichlet 分布

当所有参数相等时：

$$  
\alpha_1=\alpha_2=\cdots=\alpha_K=\alpha  
$$

称为对称 Dirichlet 分布：

$$  
\mathbf{x}\sim\operatorname{Dirichlet}(\alpha,\ldots,\alpha)  
$$

此时只需要两个核心参数：

- $K$：需要生成多少个比例。
    
- $\alpha$：控制这些比例的分布形态。
    

例如，需要生成 5 个比例时：

$$  
\mathbf{x}\sim\operatorname{Dirichlet}  
(\alpha,\alpha,\alpha,\alpha,\alpha)  
$$

这也是数据包随机分割中较容易使用的一种形式。

---

## 3. 参数 alpha 的作用

### 3.1 alpha 是什么？

$\alpha$ 是 Dirichlet 分布的浓度参数（concentration parameter）。

在对称 Dirichlet 分布中，它控制比例向量偏离均匀分配的程度。

需要注意：

**alpha 不直接指定某个分片的长度，而是控制随机比例向量的统计分布形态。**

### 3.2 当 alpha 小于 1

$$  
0<\alpha<1  
$$

分布倾向于产生较为稀疏的比例向量，即少数分量较大，其余分量较小。

例如，一次采样可能得到：

$$  
\mathbf{x}=(0.03,0.07,0.78,0.05,0.07)  
$$

如果总长度为 1000 Byte，则对应：

$$  
\mathbf{L}=(30,70,780,50,70)  
$$

此时，大部分长度集中在第三份中。

特点：

- 分片大小差异通常较大。
    
- 可能产生很小的比例。
    
- 适合探索明显不均匀的分配策略。
    

### 3.3 当 alpha 等于 1

$$  
\alpha=1  
$$

此时得到的是定义在整个概率单纯形上的均匀分布。

例如，可能得到：

$$  
\mathbf{x}=(0.05,0.35,0.20,0.10,0.30)  
$$

这里的“均匀分布”是指单纯形上的概率密度均匀，并不是说每个分量都相等。

### 3.4 当 alpha 大于 1

$$  
\alpha>1  
$$

分布更倾向于均匀分配附近。

例如，分成 5 份时，均匀分配对应：

$$  
\mathbf{x}=(0.2,0.2,0.2,0.2,0.2)  
$$

较大的 alpha 会使采样结果通常更加接近这个中心。

### 3.5 参数对比

|alpha|分布倾向|分片大小特征|
|---|---|---|
|$0<\alpha<1$|偏向单纯形边界和顶点|差异通常较大|
|$\alpha=1$|单纯形上的均匀密度|可能存在明显差异|
|$\alpha>1$|偏向均匀分配中心|通常更接近平均分配|

注意：以上是统计趋势，而不是确定性规则。单次采样结果可能与直观预期不同。

---

## 4. 数学期望与方差

设：

$$  
\mathbf{x}\sim\operatorname{Dirichlet}  
(\alpha_1,\ldots,\alpha_K)  
$$

定义浓度参数之和：

$$  
\alpha_0=\sum_{i=1}^{K}\alpha_i  
$$

### 4.1 数学期望

第 $i$ 个分量的数学期望为：

$$  
E[x_i]=\frac{\alpha_i}{\alpha_0}  
$$

对于对称 Dirichlet 分布：

$$  
E[x_i]=\frac{1}{K}  
$$

例如，生成 5 个比例时：

$$  
E[x_i]=\frac{1}{5}=0.2  
$$

无论对称分布中的 alpha 取什么正值，每个分量的期望都是 0.2。

但这并不意味着每次生成的 5 个比例都相等。

### 4.2 方差

第 $i$ 个分量的方差为：

$$\frac{\alpha_i(\alpha_0-\alpha_i)}  
{\alpha_0^2(\alpha_0+1)} $$ 
$$

对于对称 Dirichlet 分布：

\frac{K-1}{K^2(K\alpha+1)}  
$$

在固定 $K$ 时，alpha 越大，单个比例的方差越小。

因此：

- 小 alpha：比例波动通常更大。
    
- 大 alpha：比例通常更集中在均匀分配附近。
    

### 4.3 分量之间的关系

Dirichlet 分布的分量并不相互独立，因为所有分量的总和必须为 1。

当 $i\neq j$ 时：

$$-\frac{\alpha_i\alpha_j}  
{\alpha_0^2(\alpha_0+1)}  
$$

协方差为负，说明一个分量增大时，其他分量可分配的总比例会减少。

---

## 5. Dirichlet 分布如何采样？

### 5.1 基于 Gamma 分布的采样方法

Dirichlet 分布可以通过 Gamma 分布构造。

首先，独立生成 $K$ 个随机变量：

$$  
Y_i\sim\operatorname{Gamma}(\alpha_i,1)  
$$

然后对它们进行归一化：

$$  
X_i=\frac{Y_i}{\sum_{j=1}^{K}Y_j}  
$$

最终得到：

$$  
\mathbf{X}\sim\operatorname{Dirichlet}  
(\alpha_1,\ldots,\alpha_K)  
$$

因为每个 $Y_i$ 都非负，归一化后有：

$$  
X_i\geq 0  
$$

并且：

$$  
\sum_{i=1}^{K}X_i=1  
$$

这是一种标准的 Dirichlet 随机采样方法。

### 5.2 Python 示例

```
import numpy as np

rng = np.random.default_rng()

K = 5
alpha = 0.3

ratios = rng.dirichlet(np.full(K, alpha))

print("比例向量：", ratios)
print("比例之和：", ratios.sum())
```

其中：

- `K` 决定生成多少个比例。
    
- `alpha` 决定对称 Dirichlet 分布的形态。
    
- `rng.dirichlet()` 返回随机比例向量。
    

如果希望复现实验，可以固定随机种子：

```
rng = np.random.default_rng(42)
```

---

## 6. 应用于数据包分割

### 6.1 问题定义

假设原始数据长度为 $L$ Byte，需要分成 $n$ 份。

目标是生成：

$$  
\mathbf{x}=(x_1,x_2,\ldots,x_n)  
$$

满足：

$$  
x_i\geq 0,\qquad \sum_{i=1}^{n}x_i=1  
$$

然后将比例转换为分片长度：

$$  
l_i=Lx_i  
$$

但真实分片长度必须是整数，因此需要进行整数化处理。

此外，如果希望每个分片至少为 $m$ Byte，还需要引入最小分片长度约束。

### 6.2 为什么需要最小分片长度？

Dirichlet 分布允许某些比例非常接近 0。

例如：

$$  
\mathbf{x}=(0.001,0.009,0.09,0.90)  
$$

如果总长度为 1000 Byte，直接转换后为：

$$  
\mathbf{L}=(1,9,90,900)  
$$

这可能导致：

- 产生过小的分片。
    
- 增加分片数量带来的处理开销。
    
- 影响实际系统的吞吐量和通信时延。
    

因此，可以额外规定：

$$  
l_i\geq m  
$$

其中 $m$ 是预先设定的最小分片长度。

注意：最小分片长度是工程约束，不是 Dirichlet 分布本身的属性。

### 6.3 加入最小长度约束

首先必须满足：

$$  
L\geq nm  
$$

先为每份预留 $m$ Byte：

$$  
R=L-nm  
$$

其中 $R$ 是剩余的可分配长度。

然后对剩余长度生成比例：

$$  
\mathbf{x}\sim\operatorname{Dirichlet}  
(\alpha,\ldots,\alpha)  
$$

将剩余长度按比例分配：

$$  
l_i=m+r_i  
$$

其中 $r_i$ 为分配到第 $i$ 份的额外长度，并满足：

$$  
\sum_{i=1}^{n}r_i=R  
$$

因此最终有：

$$  
\sum_{i=1}^{n}l_i=L  
$$

以及：

$$  
l_i\geq m  
$$

这样就能同时保证总长度不变和最小分片长度约束。

### 6.4 Python 实现

```python
import numpy as np

def dirichlet_split(total_len, n, min_size=32,
                    alpha=0.3, seed=None):
    if n < 1:
        raise ValueError("n 必须大于等于 1")

    if min_size < 1:
        raise ValueError("min_size 必须大于等于 1")

    if total_len < n * min_size:
        raise ValueError("总长度不足以满足最小长度约束")

    rng = np.random.default_rng(seed)

    remaining = total_len - n * min_size
    ratios = rng.dirichlet(np.full(n, alpha))

    # 将剩余长度转换为连续分配值
    raw = ratios * remaining

    # 向下取整
    extra = np.floor(raw).astype(int)

    # 计算尚未分配的字节数
    left = remaining - extra.sum()

    # 最大余数法：将剩余字节分配给小数部分最大的分量
    if left > 0:
        order = np.argsort(-(raw - extra))
        extra[order[:left]] += 1

    lengths = extra + min_size

    assert len(lengths) == n
    assert sum(lengths) == total_len
    assert min(lengths) >= min_size

    return lengths.tolist()


lengths = dirichlet_split(
    total_len=1200,
    n=5,
    min_size=32,
    alpha=0.3,
    seed=42
)

print("分片长度：", lengths)
print("总长度：", sum(lengths))
```

这个函数保证：

1. 分片数量为 $n$。
    
2. 每份长度至少为 `min_size`。
    
3. 所有分片长度之和等于原始长度。
    
4. 相同随机种子和相同输入会产生相同结果。
    

---

## 7. Dirichlet 分布的常见应用

### 7.1 贝叶斯统计

Dirichlet 分布是多项分布参数的共轭先验分布，可用于估计多个类别的概率。

例如，估计某个系统中不同类型请求的出现概率。

### 7.2 机器学习

Dirichlet 分布可用于主题模型、类别概率建模和贝叶斯推断。

### 7.3 联邦学习

在一些联邦学习研究中，Dirichlet 分布用于控制不同客户端所拥有的数据类别比例，以构造非独立同分布（Non-IID）数据集。

### 7.4 资源分配

当总量固定且各部分比例需要满足非负、总和为 1 时，可以用 Dirichlet 分布生成随机分配比例。

数据包分割可以采用同样的数学思想。

---

## 8. 在 TLS 数据包分割项目中的注意事项

### 8.1 明确分割对象

需要区分：

- 应用层数据。
    
- TLS Record。
    
- TCP 载荷。
    
- IP 数据包。
    

这些对象并不等价，具体分割行为会受到实现层次和协议机制影响。

### 8.2 alpha 需要实验验证

不能仅凭 alpha 较小就断定分割策略更好。

应该通过实验比较不同 alpha 下的：

- 分片长度方差。
    
- 最大分片与最小分片之比。
    
- 分片数量与相关处理开销。
    
- 通信时延和吞吐量。
    
- IoT 设备兼容性与连接稳定性。
    

### 8.3 最小长度不是通用常数

`min_size=32` 只是示例值，不代表所有场景都适合 32 Byte。

具体值需要根据实际分割对象、系统实现和实验结果确定。

### 8.4 TCP 的字节流语义

TCP 提供的是字节流，不保证应用层写入边界与接收端读取边界一致。

如果在网关侧修改 TCP 载荷，需要正确处理序列号、校验和、重传及流重组等问题。Dirichlet 分布本身不能解决这些协议问题。

---

## 9. 总结

Dirichlet 分布是一种用于生成满足总和约束的随机比例向量的连续多元概率分布。

核心知识点：

1. **维数 $K$**：决定生成多少个比例。
    
2. **浓度参数 $\alpha$**：控制比例向量的分布形态。
    
3. **总和约束**：所有比例之和为 1。
    
4. **Gamma 归一化采样**：一种标准的随机生成方法。
    
5. **最小分片长度约束**：工程上额外施加的限制。
    

在数据包分割中，可以采用以下流程：

$$  
\boxed{  
\text{Dirichlet 采样}  
\rightarrow  
\text{比例转换}  
\rightarrow  
\text{整数化}  
\rightarrow  
\text{约束检查}  
}  
$$

这种方法能够生成可控的不均匀分片，但其实际收益仍需要通过通信性能和设备兼容性实验验证。

## 10. 参考资料

- Bishop, C. M. _Pattern Recognition and Machine Learning_. Springer, 2006.
    
- Gelman, A., et al. _Bayesian Data Analysis_, 3rd Edition. CRC Press, 2013.
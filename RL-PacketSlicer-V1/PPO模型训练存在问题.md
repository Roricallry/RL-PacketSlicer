# 一、PPO里面到底有三个东西

对于每一个状态 sts_tst​，PPO需要三个量：

## 1. Value

Critic预测：

V(st)V(s_t)V(st​)

表示：

> 当前状态未来总收益的估计。

例如：

```
V(s)=2.3
```

表示：

Critic认为：

```
从这个状态开始，未来还能获得2.3奖励
```

---

## 2. Advantage

优势函数：

AtA_tAt​

表示：

> 当前动作到底比Critic预估的平均水平好多少。

例如：

```
A=+1.5
```

表示：

```
这个动作特别好
```

而：

```
A=-0.8
```

表示：

```
这个动作比平均水平差
```

Actor只关心这个。

---

## 3. Return

Critic学习目标：

RtR_tRt​

表示：

```
真实应该得到多少价值
```

Critic训练：

(V(s)−Rt)2(V(s)-R_t)^2(V(s)−Rt​)2

---

# 二、GAE真正计算的是什么

GAE首先计算：

δt=rt+γV(st+1)−V(st)\delta_t = r_t+\gamma V(s_{t+1})-V(s_t)δt​=rt​+γV(st+1​)−V(st​)

然后：

At=δt+γλAt+1A_t= \delta_t+\gamma\lambda A_{t+1}At​=δt​+γλAt+1​

最后得到：

```
raw_advantage
```

即：

```
[1.3,0.9,-0.4,2.1,...]
```

这个：

```
就是原始优势值
```

---

然后：

PPO通常会做：

```
adv=(adv-mean)/std
```

原因：

让训练更稳定。

例如：

原来：

```
[100,200,-50]
```

变成：

```
[-0.1,1.2,-1.1]
```

防止梯度爆炸。

---

# 三、问题出在哪里

你当前代码：

## 第一步：

```
advantages_t=self._compute_gae(...)
```

进入：

```
advantages=(advantages-mean)/std
```

所以：

返回的是：

```
标准化后的优势
```

例如：

原来：

```
raw_adv=[5,3,-2]
```

返回：

```
adv=[0.9,0.2,-1.1]
```

---

然后：

代码写：

```
returns_t=advantages_t+old_values_t
```

假设：

```
old_values=[4,5,3]
```

于是：

```
returns=[4.9,5.2,1.9]
```

但是：

真正应该：

```
returns=raw_advantage+old_value
```

即：

```
returns=[9,8,1]
```

差距巨大。

---

# 四、为什么不能用标准化后的Advantage算Return

因为：

Critic要学习的是：

```
未来真实收益
```

而不是：

```
缩放后的收益
```

标准化后的：

```
0.90.2-1.1
```

已经没有物理意义了。

它只是：

```
供Actor排序用
```

不能作为Critic标签。

否则：

Critic永远学不准。

训练会很不稳定。
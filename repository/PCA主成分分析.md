---
tags:
  - 机器学习
  - 降维
---
>**PCA（Principal Component Analysis，主成分分析）** 是一种常用的**无监督线性降维方法**。它通过正交变换，把原来可能相关的多个变量转换为一组**线性不相关**的新变量，称为“主成分”。其中第一主成分方差最大，第二主成分在与第一主成分正交的方向上方差最大，依次类推。

## 核心思想

用较少的主成分保留尽可能多的原始信息。

设中心化后的数据矩阵为 $X\in\mathbb{R}^{n\times d}$，协方差矩阵为：$$\sum=\frac{1}{n-1}X^TX$$
PCA 要找投影方向 $w$，使得投影后的方差最大：$$\max_{w} w^T\sum w \;\;\;\; s.t. \;||w||=1$$

解就是 $\sum$ 的最大特征值对应的特征向量。前 $k$ 个特征向量构成新的坐标轴，把数据投影到这 $k$ 个方向上，就完成降维。

## 主要步骤

1. **数据预处理**
    - 通常先中心化：每个特征减去均值。
    - 如果不同特征量纲差异大，先标准化：$x′=\frac{x−\mu}{\sigma}$​。
2. **计算协方差矩阵**
    $$\sum=\frac{1}{n-1}X^T_cX_c$$​
3. **特征值分解或 SVD**
    
    - 特征值 $\lambda_i$ 表示第 $i$ 个主成分的方差。
    - 特征向量表示主成分方向。
    - 实际计算中常用 SVD，数值更稳定：$$X_c=USV^T$$$V$ 的列是主成分方向，得分可写为 $US$。
    
4. **选择主成分个数 $k$**
    
    - 按特征值从大到小排序。
    - 累计方差贡献率：$$r_k=\frac{\sum_{i=1}^{k}\lambda_i}{\sum^{d}_{i=1}\lambda_i}$$​
    - 常选累计贡献率达到 85%、90% 或 95%。
    - 也可用碎石图、Kaiser 准则、交叉验证等。
5. **投影降维**
    $$Z=X_cV_k$$$Z$ 就是降维后的数据，维度为 $n\times k$。
    

## 优缺点

**优点：**

- 降低维度，减少计算量和存储。
    
- 去除变量间的线性相关性。
    
- 可用于可视化、去噪、特征提取。
    
- 在均方误差意义下，保留信息最多。
    

**缺点：**

- 假设线性关系，非线性结构效果差。
    
- 方差大的方向不一定对任务最重要。
    
- 主成分是原始变量的线性组合，解释性较弱。
    
- 对量纲和异常值敏感。
    
- 属于无监督方法，不考虑标签信息。
    

## Python 示例

```python

from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.datasets import load_iris
import matplotlib.pyplot as plt

X, y = load_iris(return_X_y=True)

# 标准化
X_scaled = StandardScaler().fit_transform(X)

# PCA 降维到 2 维
pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_scaled)

print("各主成分方差贡献率：", pca.explained_variance_ratio_)
print("累计贡献率：", pca.explained_variance_ratio_.cumsum())
print("主成分方向：\n", pca.components_)
plt.scatter(X_pca[:, 0], X_pca[:, 1], c=y)
plt.xlabel("PC1")
plt.ylabel("PC2")
plt.title("PCA of Iris Dataset")
plt.show()
```
如果想自动选择保留 95% 方差：

```python

pca = PCA(n_components=0.95)
X_pca = pca.fit_transform(X_scaled)
print(X_pca.shape)
```
## 常见应用

- 数据可视化：高维数据降到 2D/3D。
    
- 图像压缩：如人脸识别中的 Eigenfaces。
    
- 生物信息、金融、文本挖掘中的特征降维。
    
- 机器学习预处理，减少过拟合和噪声。
    
- 数据去相关和白化。
    

一句话总结：**PCA 通过找方差最大的正交方向，把高维数据投影到低维空间，在尽量保留原始信息的同时实现降维。**
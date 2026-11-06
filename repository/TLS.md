---
title: TLS
aliases:
  - TLS 协议
  - Transport Layer Security
  - 记录层
  - 握手层
tags:
  - 网络安全/协议
  - 网络安全/加密
  - 网络协议/传输层
type: concept
status: developing
created: 2026-09-08
---

## 概述

TLS（Transport Layer Security，传输层安全协议）运行在**可靠传输层（通常为 TCP）**之上，为上层应用提供保密性、完整性和身份认证。其前身是 SSL，SSL 3.0 之后的版本由 IETF 标准化为 TLS。

> [!info] 与端口无关
> TLS **不绑定任何端口**。`443` 只是 HTTPS 的 IANA 注册端口，属于约定而非协议规范。识别 TLS 流量应依据**记录层头部的 Content Type 与版本号**，而不是端口号。

TLS 报文结构按层次划分，主要分为**记录层（Record Layer）** 和**握手层（Handshake Layer）**，它们各自有不同的头部字段。

## 1. 记录层头部 (Record Header)

这是TLS中最基础、最常见的头部，每个TLS数据包（称为“记录”）都包含此头部。它固定为5个字节，包含以下3个字段：

| 字段                          | 大小  | 说明                                                                                 |
| --------------------------- | --- | ---------------------------------------------------------------------------------- |
| **内容类型 (Content Type)**     | 1字节 | 标识记录负载的类型。常见类型有：`22 (0x16)` 握手、`20 (0x14)` 更改密码规范、`21 (0x15)` 警报、`23 (0x17)` 应用数据。 |
| **协议版本 (Protocol Version)** | 2字节 | 表示TLS的版本号。例如，TLS 1.0是 `0x0301`，TLS 1.2是 `0x0303`。                                  |
| **记录长度 (Record Length)**    | 2字节 | 指明后续负载数据的字节长度，不包括头部自身。最大长度通常为 `2^14` (16384) 字节。                                   |

补充说明：
- `Content Type` 就是上文所说的 `0x14`–`0x17` 四个值，这是**协议识别最可靠的依据**。
- `Protocol Version` 字段在 TLS 1.3 中固定填 `0x0303`（兼容性伪装），实际版本由握手阶段 `supported_versions` 扩展协商。
- 同一条 TLS 连接中，`ChangeCipherSpec`（`0x14`）只在从明文切换到密文的那一刻出现一次；之后的记录都是 `0x17` 应用数据。

## 2. 握手消息头部 (Handshake Header)

握手消息是记录层负载的一种。一个握手记录里可以包含一条或多条握手消息，每条消息都有自己的头部。它固定为4个字节，包含以下字段：

| 字段                        | 大小  | 说明                                             |
| ------------------------- | --- | ---------------------------------------------- |
| **消息类型 (Handshake Type)** | 1字节 | 标识握手消息的类型。例如，`1 (0x01)` 是客户端问候 (Client Hello)。 |
| **消息长度 (Length)**         | 3字节 | 指明该握手消息负载的字节长度。                                |

常见握手消息类型：

| 值 | 消息 | 方向 |
|---|---|---|
| `0x01` | ClientHello | C → S |
| `0x02` | ServerHello | S → C |
| `0x0B` | Certificate | S → C |
| `0x0C` | ServerKeyExchange | S → C |
| `0x0D` | CertificateRequest | S → C |
| `0x0E` | ServerHelloDone | S → C |
| `0x10` | ClientKeyExchange | C → S |
| `0x14` | Finished | 双向 |

> [!note] TLS 1.3 的变化
> TLS 1.3 中握手的整体顺序被重新编排（1-RTT 握手），`ServerHello` 之后紧接加密的 `EncryptedExtensions`、`Certificate`、`CertificateVerify`、`Finished`，不再有 `ServerKeyExchange` 与 `ServerHelloDone`；`ChangeCipherSpec` 也仅为兼容目的而保留。

> [!tip] 与 RFC 的对应
> 记录层与握手层的帧格式定义在 RFC 5246（TLS 1.2）第 6 章与第 7.4 节；TLS 1.3 的变更见 RFC 8446。两版的外部结构相似，差别主要在握手消息集合与加密时机。

## 3. 握手流程简述（TLS 1.2）

```text
Client                                Server
  |  ClientHello  ------------------>  |
  |  <------------------  ServerHello  |
  |  <------------------  Certificate  |
  |  <-------------  ServerHelloDone  |
  |  ClientKeyExchange  ------------->  |
  |  ChangeCipherSpec   ------------->  |
  |  Finished           ------------->  |
  |  <--------------- ChangeCipherSpec |
  |  <----------------------- Finished |
  |  <======= Application Data =======> |
```

握手完成后，双方使用协商出的**对称密钥**加解密应用数据，记录层的 `Content Type` 变为 `0x17`，此后流量呈现为不可区分的密文。

## 4. 端口与典型部署

TLS 可部署在任意 TCP 端口上，常见的注册端口如下：

| 端口 | 应用 |
|---|---|
| **443** | HTTPS（HTTP over TLS） |
| 8443 | 备用 HTTPS（管理台、Tomcat 等） |
| 993 / 995 | IMAPS / POP3S |
| 465 / 587 | SMTPS / 邮件提交 |
| 636 | LDAPS |
| 853 | DNS over TLS（DoT） |
| 990 | FTPS |
| 5061 | SIP over TLS |
| 8883 | MQTT over TLS |

> [!warning] 抓包时的误区
> - **443 ≠ 一定是 TLS**：443 上也可能跑自定义协议或代理流量。
> - **TLS ≠ 只在 443**：非标准端口上的 TLS 常用于规避基于端口的检测。
> - **UDP 443 是 QUIC（HTTP/3）**：TLS 1.3 握手被直接嵌入 QUIC 数据包，**没有独立的 TLS 记录层**，不能按记录层头部解析。

## 5. 流量识别要点

在抓包分析（如 Wireshark）或流量分类时，可依据以下特征识别 TLS：

1. **记录层**：载荷首字节 `Content Type` 落在 `0x14`–`0x17` 范围内，紧随其后的 2 字节版本为 `0x03 0x0X`。
2. **握手记录**：`Content Type == 0x16` 且紧接的 `Handshake Type` 为 `0x01`（ClientHello）时，几乎可确定为 TLS 连接开始。
3. **ClientHello 特征**：包含 2 字节版本（如 `0x0303`）、32 字节随机数、会话 ID、密码套件列表、扩展（SNI 在扩展中）。
4. **区分 TLS 与 QUIC**：QUIC 的首字节为长包头标志位，且位于 UDP 之上。

## 总结

简单来说，TLS 的头部结构是分层的：
1. **记录层头部 (5字节)**：最外层，包含 内容类型、协议版本 和 记录长度。
2. **握手消息头部 (4字节)**：仅当 内容类型 是"握手"时才存在，包含 消息类型 和 消息长度。
3. **协议不绑定端口**：443 只是 HTTPS 的约定；识别 TLS 应依赖记录层头部的 `Content Type`（`0x14`–`0x17`）与版本号，而非端口号。

## 相关笔记

- 承载层：TCP
- 上层应用：HTTP/1.1、HTTP/2（HTTPS 场景）、SMTPS / IMAPS / LDAPS 等
- 密钥与证书：X.509 证书、RSA / ECDHE 密钥交换
- 相关协议：QUIC（UDP 443，内置 TLS 1.3 握手）


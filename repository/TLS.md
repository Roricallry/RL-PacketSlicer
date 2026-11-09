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

## 4. 空长度记录与填充：流量分析对抗

### 4.1 零长度 application_data 是否合法

| 版本 | 记录类型 | 是否允许零长度负载 | 依据 |
|---|---|---|---|
| TLS 1.2 (RFC 5246 §6.2.1) | application_data | **允许**（MAY） | 原文注明"potentially useful as a traffic analysis countermeasure" |
| TLS 1.2 (RFC 5246 §6.2.1) | handshake / alert / change_cipher_spec | **禁止**（MUST NOT） | — |
| TLS 1.3 (RFC 8446 §5.1) | application_data | **允许**（MAY） | "useful as a traffic analysis countermeasure" |
| TLS 1.3 (RFC 8446 §5.4) | 加密记录中的 `application_data` | **允许** `TLSInnerPlaintext.content` 为空 | 用于生成"看起来像正常大小"的填充流量（cover traffic） |
| TLS 1.3 (RFC 8446 §5.1 / §5.4) | handshake / alert | **禁止** | 收到则必须用 `unexpected_message` alert 终止连接 |

要点：**零长度记录不是 1.3 才引入的**，TLS 1.2 就有，而且规范给出的理由就是流量分析对抗。你的判断在这一半上是正确的。

### 4.2 TLS 1.2 的可观测性：为什么"能看破"

TLS 1.2 的加密是"MAC-then-Encrypt"或"AEAD"，但**记录外部头部的 5 个字节始终是明文**：

```text
+--------+----------+--------+----------------------------+
| type   | version  | length | fragment (加密后的内容)      |
| 1 字节 | 2 字节   | 2 字节 |                            |
+--------+----------+--------+----------------------------+
   ^ ^ ^ 明 文（攻击者可见、可读）
```

RFC 5246 §6 特别写明：

> Note in particular that **type and length of a record are not protected by encryption**. If this information is itself sensitive, application designers may wish to take steps (**padding, cover traffic**) to minimize information leakage.

因此攻击者可以：
- 看到每条记录到底是 `0x17` 应用数据还是 `0x16` 握手 / `0x15` 警报；
- 看到每条记录的长度，从而判断"这条是空的还是带数据的"；
- 结合时间戳还原请求-响应模式（例如网页资源、按键节奏、视频比特率）。

> [!caution] 对应关系需要修正
> TLS 1.2 里**能直接看出"某条记录是 0x17 应用数据 + length=0"**，这是真的。
> 但攻击者在 TLS 1.2 中**同样看不出被加密的内容到底是多少字节**——单条记录里 content 的长度只能靠密文总长度减去 MAC/IV/填充开销来推断，并且 CBC 模式的 padding 还会让长度信息模糊化。
> 所以更准确的说法是：**1.2 泄露的是"记录边界 + 类型 + 总长度"，1.3 在此基础上把"类型"也藏进了密文。**

### 4.3 TLS 1.3 的填充机制

TLS 1.3 对每个加密记录都做了两个关键改动：

1. **外层 ContentType 恒定**：`opaque_type` 一律填 `23 (0x17)`，真实类型藏在加密后的 `TLSInnerPlaintext.type` 里。
2. **记录内填充**：`TLSInnerPlaintext` 结构为

```text
opaque content[TLSPlaintext.length];
ContentType type;
uint8 zeros[length_of_padding];
```

`zeros` 是**任意长度、全零**、跟在真实类型之后、和内容一起被 AEAD 加密的字节串。攻击者只能看到外层 5 字节头（类型恒为 0x17、版本恒为 0x0303、长度 = 内容 + 填充 + 1 + AEAD 开销），看不到"真实内容多少、填充多少"。

注意两个细节：
- **填充是加密的**：规范要求发送方在加密前把填充字节全置 0；接收方解密后从尾部往前扫描第一个非零字节即真实 `type`，其后的零都是填充。这意味着**明文内容本身不能以 0 结尾**——这是一个实现上的坑。
- **长度上限**：`TLSCiphertext.length` 不得超过 $2^{14} + 256$ 字节。
- **padding 可选**：实现自行决定是否填充，填充量为 0 即"不填充"。

#### 4.3.1 外层 opaque_type 恒为 0x17

RFC 8446 §5.2 的 `TLSCiphertext` 定义中把该字段写成**带默认值的常量**：

```text
struct {
    ContentType opaque_type = application_data;      /* 23 */
    ProtocolVersion legacy_record_version = 0x0303;  /* TLS v1.2 */
    uint16 length;
    opaque encrypted_record[TLSCiphertext.length];
} TLSCiphertext;
```

规范原文（§5.2）：

> The outer opaque_type field of a TLSCiphertext record is **always set to the value 23 (application_data)** for outward compatibility with middleboxes accustomed to parsing previous versions of TLS. **The actual content type of the record is found in TLSInnerPlaintext.type after decryption.**

结构对照：

```text
TLS 1.3 加密记录（线上可见）:
+--------+----------+--------+---------------------------------------------+
| 0x17   | 0x0303   | length | encrypted_record                            |
| 明文   | 明文     | 明文   |  = AEAD( content + real_type + zeros[] )    |
+--------+----------+--------+---------------------------------------------+
                                       ^^^^^^^^^   都看不到
真实类型（握手 0x16 / 警报 0x15 / 应用数据 0x17）在密文里
```

三个要点：

1. **只有加密记录才恒为 `0x17`**。握手早期的 `ClientHello`、`ServerHello` 记录仍是未加密的 `TLSPlaintext`，此时外层 `type` 是真实值 `0x16`（握手），版本为 `0x0301`（首个 ClientHello，兼容用）或 `0x0303`；`ChangeCipherSpec` 兼容记录也是明文 `0x14`。即**"恒为 0x17"只对 `TLSCiphertext` 成立**。
2. **目的是中间盒兼容（ossification）**。部分老防火墙/中间盒只认识握手与 `application_data` 两类记录，统一标成 `0x17` 可避免它们因看到陌生记录类型而拦截或报错。
3. **真实类型并未丢失，只是被加密**。解密后由 `TLSInnerPlaintext.type` 给出；定位方式是解密后从尾部向前扫描第一个非零字节。

> [!note] 校验路径
> 因此抓包时无法靠外层类型判断版本，必须看 `ServerHello` 中 `supported_versions` 扩展是否协商出 `0x0304`；也可以观察 `ServerHello` 之后是否仍出现明文的 `0x16` / `0x15` 记录——若出现则为 1.2 或更早。

### 4.4 1.3 的填充并不彻底解决流量分析

RFC 8446 附录 E.3 明确指出：

> TLS is susceptible to a variety of traffic analysis attacks based on observing the **length and timing** of encrypted packets ... TLS does not provide any specific defenses against this form of attack but does include a padding mechanism for use by applications.

即：
1. **总长度仍然暴露**（记录长度 = 内容 + 填充 + 固定开销），填充只是让攻击者猜不准"内容 vs 填充"的比例，不能消掉长度信号；
2. **时序仍然暴露**，填充不解决；
3. **填充是"应用可选的"**，协议并不会自动把每条记录填成固定长度。`TLSCiphertext.length` 仍然逐条记录跳动；
4. **响应式"空包探测"**：攻击者可以向服务器注入记录，观察是否触发响应来探测"接收方是否在解密"（附录 E.3 提到了这种 trickling / timing 通道）；
5. **0-RTT early data 也是有长度的密文**，一样参与长度分析。

因此 1.3 的改进是**把类型藏起来、给了应用的填充原语**，而不是"消灭了流量分析"。真正抗流量分析需要应用层做**定长填充或恒定速率发送**（例如 ESNI/ECH、Tor、Oblivious HTTP 的思路），代价是性能与带宽。

### 4.5 攻击面小结

| 观测项 | TLS 1.2 | TLS 1.3 |
|---|---|---|
| 记录类型（握手/警报/应用数据） | **可见**（明文 `type`） | 加密记录恒为 `0x17`，**不可见** |
| 记录长度 | 可见（明文 `length`） | 可见（明文 `length`） |
| 内容长度 | 可估算（长度 - MAC/IV/填充） | 不可直接拆分，受 padding 干扰 |
| 填充 | 仅 CBC 模式的整块填充 | 任意长度，加密、零值 |
| 空负载记录 | 允许（`0x17`, length=0 直接可见） | 允许（空 `content` + 可选 padding） |
| 时序 | 可见 | 可见 |
| 握手明文 | ServerHello 之后的 Certificate 等仍明文 | ServerHello 之后全部加密 |

### 4.6 抓包时的实践含义

1. **TLS 1.2**：过滤 `tls.record.content_type == 23 && tls.record.length == 0` 就能直接看到空的应用数据记录；看 `content_type` 还能区分握手、警报。
2. **TLS 1.3**：Wireshark 只能看到外层 `application_data`，**记录类型、内层长度拆分都需要密钥**。仅有的启发式手段是看每条记录的总长度分布和方向。
3. **不要误判心跳**：TLS 心跳扩展（RFC 6520）在 TLS 1.3 中已不再使用；不要在 1.3 里找 `heartbeat` 记录类型。

## 5. 端口与典型部署

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

## 6. 流量识别要点

在抓包分析（如 Wireshark）或流量分类时，可依据以下特征识别 TLS：

1. **记录层**：载荷首字节 `Content Type` 落在 `0x14`–`0x17` 范围内，紧随其后的 2 字节版本为 `0x03 0x0X`。
2. **握手记录**：`Content Type == 0x16` 且紧接的 `Handshake Type` 为 `0x01`（ClientHello）时，几乎可确定为 TLS 连接开始。
3. **ClientHello 特征**：包含 2 字节版本（如 `0x0303`）、32 字节随机数、会话 ID、密码套件列表、扩展（SNI 在扩展中）。
4. **区分 TLS 与 QUIC**：QUIC 的首字节为长包头标志位，且位于 UDP 之上。
5. **区分 1.2 与 1.3**：1.3 握手后所有记录外层 `Content Type` 恒为 `0x17`，`legacy_record_version` 恒为 `0x0303`；若后续仍能看到 `0x16` / `0x15` 明文记录，说明是 1.2 或更早。

## 总结

简单来说，TLS 的头部结构是分层的：
1. **记录层头部 (5字节)**：最外层，包含 内容类型、协议版本 和 记录长度。
2. **握手消息头部 (4字节)**：仅当 内容类型 是"握手"时才存在，包含 消息类型 和 消息长度。
3. **协议不绑定端口**：443 只是 HTTPS 的约定；识别 TLS 应依赖记录层头部的 `Content Type`（`0x14`–`0x17`）与版本号，而非端口号。
4. **零长度应用数据记录**：TLS 1.2 与 1.3 都允许，属于流量分析对抗手段（1.2 明文可见，1.3 藏在密文）。
5. **填充**：TLS 1.3 把真实类型与可选零值填充一起加密，外层类型恒为 `0x17`；但记录总长度与时序仍可观测，抗流量分析并不彻底。

## 相关笔记

- 承载层：TCP
- 上层应用：HTTP/1.1、HTTP/2（HTTPS 场景）、SMTPS / IMAPS / LDAPS 等
- 密钥与证书：X.509 证书、RSA / ECDHE 密钥交换
- 相关协议：QUIC（UDP 443，内置 TLS 1.3 握手）
- 延伸阅读：RFC 8446 §5.2 / §5.4（记录保护与填充）、附录 E.3（Traffic Analysis）

## 官方文档

- **TLS 1.3（现行标准）**：RFC 8446 — <https://www.rfc-editor.org/rfc/rfc8446.html>
- **TLS 1.2**：RFC 5246 — <https://www.rfc-editor.org/rfc/rfc5246.html>
- **RFC 编辑器 TLS 系列索引**：<https://www.rfc-editor.org/rfc-index.html>（检索关键字 TLS）
- **IANA 注册表**：
  - TLS ContentType：<https://www.iana.org/assignments/tls-parameters/tls-parameters.xhtml>
  - TLS Cipher Suites：<https://www.iana.org/assignments/tls-parameters/tls-parameters.xhtml#tls-parameters-4>
  - 服务端口（含 443）：<https://www.iana.org/assignments/service-names-port-numbers/service-names-port-numbers.xhtml>
- **IETF TLS 工作组**：<https://datatracker.ietf.org/wg/tls/about/>
- **RFC 8446 中文相关补充**：RFC 7627（会话哈希）、RFC 6520（心跳，1.3 已弃用）、RFC 7301（ALPN）


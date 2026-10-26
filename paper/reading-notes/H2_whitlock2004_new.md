# 精读笔记 · Whitlock & Floru 2004《New Balanced-Input IC》（AES 117th Conv. Paper 6261）

> 格式标准（全组沿用）：出处 → 核心命题（原文引用）→ 关键数值（原文）→ 对 P1/P2/P3 的对照 → 没读到的。
> 读法：pdftotext 全文逐节读，引用一律原文加页码；不转述成模糊话。

## 核心命题（原文）

1. "noise rejection in a balanced system has absolutely **NOTHING to do with signal symmetry** ... It is the **balance of common-mode impedances** that defines a balanced system!"（p.2）
2. 平衡接口等效 **Wheatstone 电桥**（Fig.2）：null 对阻抗变化的敏感度可由"驱动端共模阻抗极小 + 接收端共模阻抗极大"压制（p.2）。
3. **对地电容的第三机制（本次精读新发现）**：RFI 抑制的并联电容 "At 10 kHz, these capacitors alone will lower common-mode input impedances to about 16 kΩ. This seriously degrades high frequency CMRR with real-world sources, **even if the capacitors are perfectly matched**."（p.4）——**完美匹配的 C_G 也照样恶化 HF CMRR**，机制是 Zcm 被拉低后对源失配的敏感度上升，与失配致转换是两条独立通道。
4. 解法路线是**提高接收端 Zcm**（bootstrap 抬到 >10 MΩ），而非匹配滤波元件（p.3–4）。

## 关键数值（原文）

- 常规接收端 Zcm=10 kΩ：驱动端 **1 Ω 失衡即降系统 CMRR 40 dB（120→80 dB）**；"Equipment imbalances of 10 Ω are not uncommon."（p.3）
- 变压器 Zcm≈50 MΩ（60 Hz）：失衡近 100 Ω 不受影响；1 kΩ 完全不平衡源仍有 94 dB（p.3）
- InGenius IC：SiCr 薄膜电阻 **0.005% 匹配 → ~90 dB CMRR**；激光线性修调；离散实现"practically impossible"（p.5）
- 10 kHz 时常规 RFI 电容把 Zcm 拉到 ~16 kΩ（p.4）

## 对 P1/P2/P3 的对照

- **P1（失配消去条件）**：本文是"静态阻抗平衡"谱系最强定量件，但它证明**匹配不是充分条件**——完美匹配的 C_G 因 Zcm 载荷仍伤 CMRR。我们的 P1 必须显式区分两条通道：失配致 G_DC≠0（P1 管）与 Zcm 载荷致敏感度上升（Whitlock 管，工程对策=高 Zcm/自举）。**T2 的 C_G 属后者**——这直接影响论文 Discussion 的机理表述。
- **P2（Kelvin 地板）**：Whitlock 的 Zcm 框架与 P2 互补——P2 是"两线结构类不同"，Whitlock 是"Zcm 不够高"；两者都指向"匹配救不了的退化"。
- **P3**：无直接内容（本文不涉 AAF 衰减上界）。
- **引文价值**：p.2 的 Wheatstone 桥等效 + 1Ω→40dB 数字是 Intro/理论节的最好引文；Fig.3（CMRR vs 失衡 vs Zcm 曲线族）可作对照图引用。

## 没读到的

- p.3 提及的"A previous paper of Whitlock examined balanced interfaces in considerable detail"[1]= JAES 43(6) 1995 pp.454–464（whitlock1995balanced，正文未到手，在付费清单）；
- [2]= AES 101st Conv. Preprint 4372 (1996) bootstrap 详解，无本地。

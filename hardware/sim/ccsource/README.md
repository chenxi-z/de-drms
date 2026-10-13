# 恒流源 LTspice 拓扑验证（2026-10-13）

验证对象：E.2 恒流激励源的两种候选接法（LTspice 26.1.1 / wine，`ltspice-sim` 批处理）。

## 结论

**定稿接法（变体 A）**：运放同相端 = VSET，反相端 = BSS138 源极（B），Rsense 自源极到地（E = GND），
BSS138 漏极（X 节点）接负载回线。I = VSET/Rsense，与 R_sample 无关。

| R_sample | I（推导自 V_sample/R） | V(b)=V_Rsense | V_sample | V_DS 裕量 | V_G |
| --- | --- | --- | --- | --- | --- |
| 10 kΩ | 7.857 µA | 1.17857 V | 78.57 mV | 2.043 V | 2.710 V |
| 20 kΩ | 7.857 µA | 1.17857 V | 157.14 mV | 1.964 V | 2.711 V |
| 60 kΩ | 7.857 µA | 1.17857 V | 471.43 mV | 1.650 V | 2.713 V |
| 120 kΩ | 7.857 µA | 1.17857 V | 942.86 mV | 1.179 V | 2.716 V |

（Rsense 与 Rsample 两路电流互推一致 <0.001%；VSET = 3.3×200k/560k = 1.178571 V，与 E.2.1 一致。）

**证伪接法（变体 B，原 E.3.1/rref 图字面链：Rsense 在漏极路径、B 经调整管到地）**：
环路为**正反馈**——V(b) 随栅压升高而降低，仿真显示其锁死在零电流态（调整管关断、V(b) 顶到 3.3 V），
不能恒流。理论平衡点 I = (V_T−VSET)/(R_sample+Rsense) 随 R 变 13.2→7.8 µA，且该点不稳定。

**CURR_DIS 暂态**（3 ms 拉高关断 / 8 ms 释放使能，R_sample = 10 kΩ）：
- 关断：<0.2 ms（τ≈30 µs），残流谷值 0.163 µA（满度 2%；VSET 残压 24 mV，与 E.2.1 "VSET≈0" 相符）
- 使能：**0.871 ms** 回到 ±0.1%，无过冲无振铃 → E.3.3 的 ~1 ms 换路预算内（不宽裕，测量窗口前预留 ≥1 ms）

## 文件与再生成

- `models.inc`——行为级模型：OPA333 宏（Aol=2e6→GBW 350 kHz、输出钳位）与线性版（暂态用）；
  BSS138 level-1（VTO 1.25 V 典型）。**拓扑级保真度**，非厂商宏模型
- `cca.tpl` / `ccb.tpl`——两种拓扑模板；`cca_tran.net`——CURR_DIS 暂态
- 再生成：`sed "s/{RL}/10k/" cca.tpl > cca_10k.net && ltspice-sim run cca_10k.net`
- 产物（*.raw/*.log、按 RL 生成的 .net）不入库

## 后续

- 换 TI OPA333 官方 PSpice 宏模型 + onsemi BSS138 模型复核（本行为级模型未建 Vos/Ib/SR，
  DC 精度结论对拓扑判定充分；环路稳定性仅见"无振铃"线索，PM 定量需官方模型 + TZ 环路测试）
- 原理图定稿后按实际网表回归

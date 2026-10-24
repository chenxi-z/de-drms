# 设计文档索引

当前目标：**直流测量首板 + 扫频扩展预留**（2026-10-24）。原理图/PCB由用户修改。

1. [主设计文档附录 F](2026-10-10-universal-signal-chain.md#dc-prototype)：当前实施基线、改图电阻电容清单、证据与未决项。
2. [引脚分配](pin-assignment.md)：本轮目标连接；CS迁PA8后才适用新固件。
3. [CubeMX操作清单](../../firmware/DE-DRM/CUBEMX_SETUP.md)：旧IOC必须GUI复存，防止重新生成覆盖代码修复。
4. [说明图](diagram/)：七张无历史后缀的拓扑图及其同名PNG；生成器在`diagram/_lib/`。
5. [器件选型历史](component-selection.md)、[专题历史](spec/)、[交接记录](HANDOFF.md)。
6. [AAF六方案报告](../../hardware/sim/signalchain/aaf_pkg_review/REPORT.md)：保留原始门槛与失败项，T2只是首板折中候选。

当前规则：用户本轮确认 > 主文档附录F与当前引脚表 > 历史正文/附录D/E。
历史三/四级AAF、一机全量程、TMP117、TF电源开关、BQ24040和VBUS ADC均不能直接沿用。
历史后缀图（旧版、一阶、k3b、旧B案、频响比较）只用于追溯，不是当前改图依据。

已核查提交`9aa1a5f`只有新仿真/文档，没有新版EDA。上次上板性能承诺未验证；
仍须解决最终网表与台架三颗补偿电容差异、USB取电与描述符、Rref公差、真实布局和连续采集固件。

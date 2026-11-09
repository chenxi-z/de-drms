# 按角色阅读项目文档

| 读者 | 从这里开始 | 用它做什么 |
| --- | --- | --- |
| 项目负责人、需求评审人 | [设备行为与验收](spec/device-behavior.md) | 审定操作者能做什么、看到什么，以及试验怎样才算成功。 |
| 固件开发者、接续固件工作的 agent | [固件规则与交付顺序](design/2026-11-09-firmware-mode-protocol-rules.md) | 先看业务与按键，再看第 6–9 节的模块边界、资源和放行条件。实现细节查[架构 C1–C6](design/2026-11-05-firmware-architecture.md)；变更和验证历史查[实施计划](design/2026-11-06-firmware-architecture-plan.md)。 |
| 上位机开发者、接续客户端工作的 agent | [上位机接入指南](protocol/host-integration.md) | 从连接、观察试验、发送命令、断线恢复走到读文件。 |
| 两端协议维护者 | [CDC v2 规范](protocol/de-drms-cdc-v2.md)和[机器字段表](../shared/protocol/de-drms-cdc-v2.json) | Markdown 定义行为与编码规则，JSON 定义编号、类型和测试向量，成对修改、同次提交。文件读取另查[BIN v2 规格](design/2026-11-06-record-v2-format.md)。 |
| 测试、联调、首板验收人员 | [设备行为与验收](spec/device-behavior.md) → [固件规则第 3、9 节](design/2026-11-09-firmware-mode-protocol-rules.md) → [MSC 验收](design/2026-11-05-msc-design.md) | 按可观察结果设计端到端用例；分别记录软件回放、真实板卡、不同采样档与存储介质的证据。 |
| 硬件维护、引脚与 CubeMX 配置人员 | [设计索引](design/README.md) → [引脚表](design/pin-assignment.md)；本机工程另有 `firmware/DE-DRMS-Code/CUBEMX_SETUP.md` | 查首板实施基线、硬件资源及重生成约束。 |
| 最终操作者、客户 | [用户手册区](user_manual/) | 这里收录随实测固件版本发布的操作说明。当前尚无已发布手册；评审时可先看设备行为页。 |

**维护分工**　设备行为变化从负责人页发起，再同步受影响的固件与接口规则。固件目录、线程和驱动的内部调整归固件文档；线上字段与重试语义归共享协议；文件布局归 BIN 规格。角色指南引用这些原件。发现冲突时由对应维护者同时修正文档和相应验收用例。

**版本状态**　正式 CDC v2 是设计接口。当前固件仍有 ASCII 控制入口，上位机尚未开发。已发布能力以对应固件版本及实测记录为准。

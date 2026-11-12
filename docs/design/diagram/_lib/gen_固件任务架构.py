#!/usr/bin/env python3
"""Render the agreed firmware task proposal; does not describe shipped behavior."""
from pathlib import Path
from html import escape
import cairosvg

OUT = Path(__file__).resolve().parents[1]
W, H = 1600, 1540
parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">',
'''<defs>
<pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M24 0H0V24" fill="none" stroke="#eef2f7" stroke-width="0.5"/></pattern>
''']
COLORS = {'control': '#7c3aed', 'data': '#059669', 'fault': '#dc2626', 'neutral': '#374151'}
for key, color in COLORS.items():
    parts.append(f'<marker id="a-{key}" markerUnits="userSpaceOnUse" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto"><path d="M0 1L9 5L0 9Z" fill="{color}"/></marker>')
parts += ['</defs>', '<rect width="1600" height="1540" fill="#fff"/>', '<rect width="1600" height="1540" fill="url(#grid)"/>']


def text(x, y, value, size=13, color='#374151', bold=False):
    parts.append(f'<text x="{x}" y="{y}" font-family="Noto Sans CJK SC" font-size="{size}" fill="{color}" font-weight="{700 if bold else 400}">{escape(value)}</text>')


def panel(x, y, w, h, title):
    parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="#fff" stroke="#cbd5e1"/>')
    text(x + 20, y + 29, title, 15, bold=True)


def box(x, y, w, h, title, lines, fill='#f1f5f9', stroke='#94a3b8'):
    parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="1.3"/>')
    text(x + 16, y + 27, title, 14, '#0f172a', True)
    for i, line in enumerate(lines):
        text(x + 16, y + 52 + i * 22, line, 12)


def arrow(points, kind='control'):
    pairs = ' '.join(f'{x},{y}' for x, y in points)
    dash = ' stroke-dasharray="6 4"' if kind == 'control' else ''
    parts.append(f'<polyline points="{pairs}" fill="none" stroke="{COLORS[kind]}" stroke-width="2"{dash} marker-end="url(#a-{kind})"/>')


text(40, 48, '固件任务架构', 27, '#0f172a', True)
text(40, 78, 'STM32U575RGT6 · ThreadX · 两个按键 / 五个 LED · 硬件冻结', 14)
text(40, 104, '设计提案：职责与通道已讨论；不是当前源码实现状态。任务优先级数值、队列容量与执行预算待验证。', 12, '#b45309')

panel(40, 130, 1520, 650, '一、控制与交互：业务异步协调，关键事件及时处理')
box(70, 180, 360, 110, '本机交互任务 · 低优先级', [
    '两个按键独立状态机；单击 / 长按',
    '五个 LED 非阻塞灯效；读取最新业务状态',
    '只提交操作，不裁决业务、不直接关机'], '#eff6ff', '#60a5fa')
box(70, 340, 360, 110, 'CDC 接收任务', [
    '接收 → 增量拼帧 → 校验 → 解码',
    '同任务分级解析，完整请求才跨线程',
    '保留来源 / 会话 / 请求编号'], '#eff6ff', '#60a5fa')
box(70, 500, 360, 110, 'USART1 调试服务', [
    'RX 环形缓冲 / TX DMA',
    '独立启动 / 故障日志及调试指令',
    '不承担正式协议、数据流、文件或升级'], '#eff6ff', '#60a5fa')
box(600, 340, 400, 130, '设备控制任务 · 高优先级、短执行', [
    '业务独立状态机：测量 / 记录 / 基线 / 校准',
    '统一接纳请求、检查冲突、预占资源',
    '发起异步操作，接收结果；不等待写卡',
    '协调安全停止、导出互锁和安全待机'], '#f5f3ff', '#8b5cf6')
box(1140, 180, 390, 110, 'USB 管理任务', [
    'PC13 / 枚举 / 挂起恢复 / 会话失效',
    '常插烧录、复位后的软件断开与重连',
    'CDC 与 MSC 生命周期；不直接读卡'], '#eff6ff', '#60a5fa')
box(1140, 340, 390, 110, '系统服务任务 · 低优先级', [
    '电池 / RTC / 参数与诊断快照',
    '普通信息低频刷新；有效性与更新时间',
    'Flash 维护窗口保存；不周期反复擦写'], '#f1f5f9', '#94a3b8')
box(1140, 500, 390, 110, 'CDC 发送任务 · 单一发送者', [
    '控制结果 / 关键故障优先，数据分块调度',
    '等待完成再释放缓冲；间隔按实测配置',
    'USB 拥塞只阻塞发送，不阻塞安全动作'], '#fff7ed', '#fb923c')
box(600, 530, 400, 70, '紧急事件与操作结果通道', [
    '故障 / 停止优先；独立预留容量，不能被数据占满'], '#fef2f2', '#ef4444')

arrow([(430, 235), (480, 235), (480, 370), (600, 370)])
arrow([(430, 395), (520, 395), (520, 410), (600, 410)])
arrow([(430, 555), (560, 555), (560, 450), (600, 450)])
arrow([(1140, 235), (1080, 235), (1080, 370), (1000, 370)])
arrow([(1140, 395), (1100, 395), (1100, 410), (1000, 410)])
arrow([(1000, 450), (1060, 450), (1060, 555), (1140, 555)])
arrow([(800, 530), (800, 470)], 'fault')
arrow([(1000, 565), (1080, 565), (1080, 585), (1140, 585)], 'fault')
text(70, 665, '请求：TX_QUEUE 保留顺序、来源与编号；安全停止独立保留。状态：最新快照 + 事件标志；提示：有界队列。', 13)
text(70, 697, '控制出口：异步请求采集 / 存储 / 系统服务；业务结果回到控制。LED 仅读取状态与提示，不介入裁决。', 13)
text(70, 729, '红色通道：各业务故障先触发本机处理，再尽快通知电脑。不能等待 USB 发送完成才停采或结束失败记录。', 13, '#b91c1c')
text(70, 757, '注意：任务调度优先级、消息发送优先级、NVIC 中断优先级是三套规则；关键通知只能在完整帧边界插队。', 12)

panel(40, 810, 1520, 350, '二、采样数据路径：两级有界环形缓冲，按批次处理')
box(70, 875, 210, 170, '采集任务 / ISR', [
    'ADS / 模拟通路唯一控制',
    '启动 / 停止 / 换路 / 稳定',
    'DRDY 启动 SPI DMA',
    'DMA 完成发布帧',
    '初始化与计算分离'], '#eff6ff', '#60a5fa')
box(320, 875, 170, 170, '原始帧环形缓冲', [
    '当前容量 64 KiB',
    '固定帧 16 字节',
    '单生产者 / 单消费者',
    '满则报告采集故障',
    '128 kSPS 约 32 ms'], '#ecfdf5', '#059669')
box(530, 875, 240, 170, '测量处理任务', [
    'CRC / 格式 / 序号 / 有效性',
    '电阻 / R/R0 / 区间判定',
    '基线 / 校准累计统计',
    '保留原始坏帧用于诊断',
    '批处理 + 有界执行预算'], '#ecfdf5', '#059669')
box(810, 875, 170, 170, '记录环形缓冲', [
    '当前容量 512 KiB',
    '单生产者 / 单消费者',
    '不覆盖未写入数据',
    '满则结束失败记录',
    '128 kSPS 约 256 ms'], '#ecfdf5', '#059669')
box(1030, 875, 240, 170, '存储任务 · TF 唯一所有者', [
    '挂载 / 批量写 / 分段 / flush',
    '原始记录与诊断信息',
    'MSC 只读扇区服务',
    '协议文件分块下载',
    '介质交接 / 取消 / 排空'], '#faf5ff', '#a855f7')
box(1320, 875, 210, 170, 'TF 卡', [
    '记录与导出互斥',
    '记录中不下载',
    '掉卡 / 卡满 / 写失败',
    '记录报错，监测可继续',
    '恢复卡不自动续录'], '#faf5ff', '#a855f7')
for a, b in [(280, 320), (490, 530), (770, 810), (980, 1030), (1270, 1320)]:
    arrow([(a, 960), (b, 960)], 'data')
box(810, 1070, 720, 60, '送往 CDC 发送：曲线统计 / 原始数据块', [
    '小型有界缓冲 + 接收额度；慢电脑不占住记录队列，不新增第三套大型采样缓冲'], '#fff7ed', '#fb923c')
arrow([(650, 1045), (650, 1100), (810, 1100)], 'data')

panel(40, 1190, 1520, 300, '三、图注与自查要点')
box(70, 1240, 460, 170, '实时与故障边界', [
    '采集 / 控制优先；交互和普通信息低优先级',
    '关键故障事件即时投递，周期统计不能代替安全检测',
    '看门狗按实际进展监督，不无条件定时喂狗',
    'USBX 内部线程仍保留，需共同核对调度',
    '128 kSPS 吞吐量与最坏延迟必须上板验证'])
box(570, 1240, 460, 170, '内存与队列预算', [
    '现有两环形缓冲 + 写入暂存合计 608 KiB',
    '最近构建 data + bss 约 693 KiB，主 RAM 768 KiB',
    '75 KiB 差额不是可任意分配的运行内存承诺',
    '缓冲时长按空队列估算，不是允许处理延迟',
    '线程栈 / 水位 / 小缓冲统一预算，所有队列有界'])
box(1070, 1240, 460, 170, '冻结硬件与实现状态', [
    '两个按键、五个 LED，无显示屏',
    '灯光 GPIO 由本机交互任务唯一写入',
    'VDDUSB 同 VCC：支持软重连，不是物理断电',
    'MSC / R0 / 分档 / 任务拆分仍需代码实现',
    '不改原理图、PCB、器件或接线'])
text(70, 1446, '图例：紫色虚线 = 控制 / 生命周期消息；绿色实线 = 采样数据；红色实线 = 关键事件优先通道。', 13)
text(70, 1474, '数据消费者取得有效帧后再计算；坏帧不参与基线和区间正常判定。所有跨任务缓冲均需明确归属和释放时机。', 12)
text(40, 1522, 'DE-DRMS · 2026-11-05 · 讨论版架构，依据本会话已确认职责；未承诺具体优先级数值或高速性能。', 12, '#64748b')
parts.append('</svg>')
svg = OUT / '固件任务架构.svg'
svg.write_text('\n'.join(parts) + '\n', encoding='utf-8')
cairosvg.svg2png(url=str(svg), write_to=str(OUT / '固件任务架构@2x.png'), scale=2)
print(svg)

/*****************************************************************************
 * 文件：drms_measurement.c
 * 职责：测量算法——把 12 字节原始帧变成"多少欧姆"，以及相关的判据。
 *
 * 在整机中的位置：
 *   ADC 原始帧 → drms_decode_frame（拆包、校验、判量程）
 *              → drms_excitation_ok（激励是否正常）
 *              → drms_resistance（算电阻）
 *              → 监测管线（滤波、判级）
 *
 * 一个必须理解的前提：R = k × V_sample / V_Rsense
 *
 *   V_Rsense 是已知阻值 Rsense 上的压降，它与样品上的压降流过**同一个电流**
 *   （恒流源串联），所以两者之比就是电阻之比。
 *   系数 k 由参考校准确定：用已知的 R_ref 测一次，算出 k = R_ref × sum(CH2)/sum(CH1)。
 *   这样一来 Rsense 的绝对误差被完全消掉——它只影响比值中的分母和分子，两边同时出现。
 *   最终绝对精度锚定在 R_ref 上（本板 ±0.02%）。
 *
 * 为什么分成好几个小函数：
 *   解码、激励检查、算电阻各自独立，可以单独测试、单独调用。
 *   尤其 32 kSPS 以上的纯直录模式会跳过全部三个——那条路径只搬字节。
 *****************************************************************************/

#include "drms_measurement.h"
#include <math.h>

/* 计算一帧的 CRC-16（CRC-CCITT-FALSE）。
 *
 * 参数来自 TI SBAS590E §9.5.1.7：多项式 0x1021、初值 0xFFFF、
 * 不做位反射、无最终异或。ADC 在每帧末尾附上这个校验值，
 * 我们算一遍比对，不一致说明传输被打断。
 *
 * 实现用半字节查表：每字节只查两次表，比逐位算法快一倍多。
 * 这在高速档很关键——128 kSPS 时每帧都要算一次。 */
uint16_t drms_crc16(const uint8_t *bytes, size_t length)
{
  /* CRC-CCITT-FALSE 参数：多项式 0x1021、初值 0xFFFF、不反射、无最终异或。
   * 出处 TI SBAS590E §9.5.1.7。半字节查表是为了把每帧的计算量控制住。 */
  static const uint16_t table[16] = {
    0x0000,0x1021,0x2042,0x3063,0x4084,0x50a5,0x60c6,0x70e7,
    0x8108,0x9129,0xa14a,0xb16b,0xc18c,0xd1ad,0xe1ce,0xf1ef
  };
  uint16_t crc = 0xffff;
  for (size_t i = 0; i < length; ++i)
  {
    crc = (uint16_t)((crc << 4) ^ table[((crc >> 12) ^ (bytes[i] >> 4)) & 15]);
    crc = (uint16_t)((crc << 4) ^ table[((crc >> 12) ^ bytes[i]) & 15]);
  }
  return crc;
}

/* 计算 CRC-32（ISO-HDLC，即 zlib 参数）。
 *
 * 用于：记录文件的整体校验、配置块的完整性、协议帧的尾部。
 * 与 CRC-16 不同，这一套是我们自己定的（不是 ADC 要求的），
 * 所以参数必须与协议文档严格一致，否则主机验不过。
 *
 * 用右移版本（反射多项式 0xEDB88320），与 Python 的 zlib.crc32 等价——
 * 这样上位机和测试脚本能直接复用标准库校验。 */
uint32_t drms_crc32(const uint8_t *bytes, size_t length)
{
  uint32_t crc = 0xffffffffU;
  for (size_t i = 0; i < length; ++i)
  {
    crc ^= bytes[i];
    for (unsigned int bit = 0; bit < 8; ++bit)
      crc = (crc >> 1) ^ (0xedb88320U & (0U - (crc & 1U)));
  }
  return ~crc;
}

/* 把 3 个字节按大端拼成 24 位有符号整数。
 *
 * 符号扩展的做法：先把值左移 8 位到 32 位的高半区，再算术右移回来，
 * 这样最高位自然就填满了高位。比手工判断符号位更不容易写错。
 *
 * ADC 输出的是二进制补码，满量程 ±2^23。 */
static int32_t signed24(const uint8_t *bytes)
{
  uint32_t value = ((uint32_t)bytes[0] << 16) | ((uint32_t)bytes[1] << 8) | bytes[2];
  /* 用减法而不是把无符号转成有符号：后者的行为由实现定义，
   * 换编译器可能就变味了，而出错的位置恰恰是最难查的。 */
  return value & 0x800000U ? (int32_t)(value & 0x7fffffU) - 0x800000 : (int32_t)value;
}

/* 把一帧 12 字节原始数据拆成电压、电流和一组标志位。
 *
 * 帧结构（每帧 4 个字，每字 3 字节，共 12 字节）：
 *   字节 0-2  状态字（含各类故障标志）
 *   字节 3-5  通道 0，样品/参考电压
 *   字节 6-8  通道 1，Rsense 压降
 *   字节 9-10 CRC-16
 *   字节 11   保留（应为 0）
 *
 * 判据逐条都有明确来源：
 *   · CRC 不符 → CRC_ERROR，这帧的数据不可信；
 *   · 状态字首字节不是 0x22、次字节最高位为 1、保留字节非 0 → FORMAT_ERROR，
 *     说明帧错位或 ADC 配置与预期不符；
 *   · 状态字的故障位（0x6F 掩码）→ ADC_FAULT；
 *   · 数值贴边 → RANGE_ERROR（详见下方注释）。
 *
 * 注意 F_ADCIN 这一位被有意排除在掩码之外：本板 AIN2N 直接接 AVSS，
 * 低于最低比较器门限，这一位会常态置位。它属于"已知的、无害的"，
 * 而其余故障位（协议错、重同步、看门狗、溢出、饱和）才是真问题。
 *
 * 返回 1 表示这帧完全干净可用；0 表示有任一标志置位。 */
int drms_decode_frame(const uint8_t frame[12], DRMS_Sample *sample)
{
  sample->voltage = signed24(frame + 3);
  sample->sense = signed24(frame + 6);
  sample->status = (uint16_t)(((uint16_t)frame[0] << 8) | frame[1]);
  sample->flags = 0;
  if (drms_crc16(frame, 9) != (uint16_t)(((uint16_t)frame[9] << 8) | frame[10]))
    sample->flags |= DRMS_SAMPLE_CRC_ERROR;
  if (frame[0] != 0x22 || (frame[1] & 0x80) || frame[2] != 0 || frame[11] != 0)
    sample->flags |= DRMS_SAMPLE_FORMAT_ERROR;
  /* 本板上 F_ADCIN 单独置位属于正常现象，不算故障：AIN2N 被有意接到 AVSS，
   * 低于最低比较器门限，这一位会常态置位。
   * 所以原始状态字里保留它，但掩码 0x6F 把它排除在外——
   * 真正要拦的是协议错、重同步、看门狗、溢出和数字饱和。 */
  if (frame[1] & 0x6f)
    sample->flags |= DRMS_SAMPLE_ADC_FAULT;
  if (sample->voltage >= 8388606 || sample->voltage <= -8388607 ||
      sample->sense >= 8388606 || sample->sense <= 4096 || sample->voltage < -4096)
    sample->flags |= DRMS_SAMPLE_RANGE_ERROR;
  return sample->flags == 0;
}

/* 判断恒流激励是否处于正常工作状态。
 *
 * 这是一个**首板合理性护栏**，不是标定过的电流规格。判据来自设计值：
 *   VSET = 3.3 × 100/(180+100) ≈ 1.1786 V，允许 ±10%；
 *   V_Rsense = 8 µA × 150 kΩ = 1.2 V，对应 ADC 码约 4.05M；
 *   同时要求 V_sample + V_Rsense 不超过合规上限（预留 T 点 0.5 V 余量）。
 *
 * 三道条件同时成立才算正常：
 *   1. 帧本身无标志；
 *   2. Rsense 压降落在 [3.64M, 4.45M] 码值区间（对应 ±10%）；
 *   3. 两路压降之和不超过合规栈上限——超了说明恒流源已经退出恒流区。
 *
 * 为什么需要它：电阻比值在"没有电流"时也会算出一个数（0/0 附近的噪声），
 * 那个数看起来完全正常但毫无意义。这一层就是拦住这种情况。
 *
 * 返回 1 正常；0 表示激励异常，此时不应采信任何电阻读数。 */
int drms_excitation_ok(const DRMS_Sample *sample)
{
  /* 首板合理性护栏，不是标定过的电流规格。
   *   VSET = 3.3×100/(180+100) = 1.178571 V，允许 ±10%；
   *   内部基准 2.442 V；
   *   另外预留 0.5 V 合规余量（T 点设计最低 2.97 V 以下）。
   * 这三个数共同确定了下方的码值区间，改任何一个都要重新推导。 */
  return !sample->flags && sample->sense >= 3643701 && sample->sense <= 4453411 &&
         (int64_t)sample->voltage + sample->sense <= 8484791;
}

/* 算出电阻值：R = k × V_sample / V_Rsense。
 *
 * k 由参考校准给出（drms_reference_scale）。未校准时 k 取 Rsense 的名义值，
 * 此时结果只用于粗看，绝对精度没有保证——调用方应通过 cal 标志告知操作者。
 *
 * 拒绝计算的情形（任一成立即返回 0）：
 *   · 帧有标志（数据不可信）；
 *   · Rsense 压降过小（≤ 4096 码）——分母趋零，算出来的数没有意义；
 *   · 样品电压贴满量程或为负——已饱和或接反；
 *   · k 非法（非有限值或非正）。
 *
 * 这些判断不是防御性冗余：ΣΔ 在过载时输出会贴边，若不拦住，
 * 满量程除以一个很小的数会得到一个巨大的"电阻值"，看起来像断线但其实是 ADC 饱和。
 *
 * 返回 1 成功；0 表示这次算不出可信的电阻。 */
int drms_resistance(const DRMS_Sample *sample, double scale, double *ohms)
{
  if (sample->flags || sample->sense <= 4096 || sample->voltage >= 8388606 ||
      sample->voltage < -4096 || !isfinite(scale) || scale <= 0)
    return 0;
  *ohms = scale * (double)sample->voltage / (double)sample->sense;
  return isfinite(*ohms);
}

/* 由参考测量算出比例系数 k。
 *
 * 公式：k = R_ref × ΣV_Rsense / ΣV_ref
 *
 * 注意这里的除法方向：因为 k 将来要乘在 V_sample/V_Rsense 上，
 * 所以它必须包含 R_ref 与"电流对应的码值"之间的换算关系。
 * 直白地说：用已知的 R_ref 标定一次，就知道"一个码值代表多少欧姆"。
 *
 * 用累加和而不是逐点平均：4096 个样本累加后一次除法，
 * 避免逐点除法的舍入误差累积。
 *
 * 结果做合理性检查（100k–200k Ω 范围）：落在范围外说明参考支路或
 * 激励有问题，宁可校准失败也不能接受一个离谱的系数。
 *
 * 返回 1 成功；0 表示输入非法或结果不合理。 */
int drms_reference_scale(int64_t voltage_sum, int64_t sense_sum,
                         double reference_ohms, double *scale)
{
  if (voltage_sum <= 0 || sense_sum <= 0 || reference_ohms <= 0 || !isfinite(reference_ohms))
    return 0;
  double value = reference_ohms * (double)sense_sum / (double)voltage_sum;
  if (!isfinite(value) || value < 100000. || value > 200000.)
    return 0;
  *scale = value;
  return 1;
}

/* 采样率到 ADC 时钟寄存器的映射表——这是采样率支持的**唯一权威来源**。
 *
 * 每个档位对应一个 CLK2 寄存器值，它编码了两件事：
 *   ICLK_DIV[7:5]  ICLK 到调制器时钟 fMOD 的分频
 *   OSR[3:0]       过采样比，决定 fDATA = fMOD / OSR
 *
 * 本板 fICLK = 16.384 MHz（板载晶振），实测各档都落在设计值上：
 *   4 kSPS  → OSR 1024
 *   64 kSPS → OSR 64（这是无损采集的上限）
 *   128 kSPS → OSR 32（受读取时序限制，已在入口拒绝，见 drms_acq_start）
 *
 * 想加新档位必须同时确认 ADC 是否支持该 OSR、以及固件能否在该速率下
 * 完整搬运数据——不能只看寄存器能不能写。
 *
 * 返回 1 表示速率受支持，clk2 回填寄存器值；0 表示不支持。 */
int drms_rate_register(uint32_t rate, uint8_t *clk2)
{
  switch (rate)
  {
    case 1000: *clk2 = 0x20; return 1;
    case 4000: *clk2 = 0x22; return 1;
    case 8000: *clk2 = 0x25; return 1;
    case 16000: *clk2 = 0x28; return 1;
    case 32000: *clk2 = 0x2b; return 1;
    case 64000: *clk2 = 0x2d; return 1;
    case 128000: *clk2 = 0x2f; return 1;
    default: return 0;
  }
}

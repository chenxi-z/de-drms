#include "drms_acquisition.h"
#include "drms_measurement.h"
#include "drms_fifo.h"
#include "drms_capture_time.h"
#include "main.h"
#include "spi.h"
#include <string.h>


/* One SPI data frame is 12 bytes; the DMA block length and the SPI TSIZE
 * programmed at start-up both use this. */
#define EXCHANGE_BYTES (12u)

/* Highest sample rate proven lossless on hardware. */
#define DRMS_ACQ_MAX_RATE (64000u)

static DRMS_RawFrame frames[4096];
static DRMS_FIFO queue;
/* Double-buffered receive. A single buffer serialises the whole loop: the next
 * DRDY had to wait for the previous frame's DMA to finish and its completion
 * handler to run, and at 128 kSPS that loop does not close inside 7.81 us, so
 * roughly half the frames were dropped as overruns. With two buffers the DMA
 * can be armed for the next frame while the previous one is still being
 * consumed, which doubles the tolerated loop time to 15.62 us. */
static uint8_t dma_rx_buf[2][12] __attribute__((aligned(4)));
static uint8_t dma_rx[12] __attribute__((aligned(4))); /* last completed frame */
static uint8_t dma_tx[12] __attribute__((aligned(4)));
static volatile uint32_t rx_buf_index;

/* Host-test hook: the unit tests simulate the DMA by writing the completed frame
 * into the buffer the fast path just armed. On the 64-bit host the register
 * value cannot be turned back into a pointer, so the address is handed out
 * directly instead. Never called by firmware. */
uint8_t *drms_acq_test_rx_buffer(void)
{
  return dma_rx_buf[rx_buf_index ^ 1u];
}

/* ---------------------------------------------------------------------------
 * Fast per-frame exchange
 *
 * Verified on hardware over SWD while running at 4 kSPS: after a transfer
 * completes the SPI keeps TSIZE at the frame length (CR2 = 12) and stays
 * enabled (SPE = 1) with CSTART back at 0. The peripheral therefore only has
 * to be configured once; a frame needs nothing more than re-arming the two
 * GPDMA channels and setting CSTART.
 *
 * The generic HAL path instead calls HAL_SPI_TransmitReceive_DMA every frame,
 * which revalidates the handle, recomputes transfer counts, rewires four DMA
 * callbacks and issues two HAL_DMA_Start_IT calls. At 128 kSPS a frame budget
 * is 7.81 us and the SPI transfer itself takes 4.80 us at 20 MHz SCLK, leaving
 * about 3 us (480 cycles) of software - the HAL path does not fit, this one
 * does.
 *
 * Completion still arrives on GPDMA1_Channel1_IRQHandler. Because that channel
 * is not driven by the HAL here, the ISR services it directly and the frame is
 * published through the same path the HAL callback uses.
 * -------------------------------------------------------------------------- */

static int fast_path_active;
/* Bring-up counters: prove whether the fast path starts and whether its DMA
 * interrupt is reached. Read over SWD. */
volatile uint32_t drms_acq_fx_start, drms_acq_fx_fail, drms_acq_fx_irq, drms_acq_fx_done;
/* Timing probe for the 128 kSPS budget. The window is measured with the DWT
 * cycle counter (160 MHz): isr_us is from ISR entry to CS low (covers the
 * handler prologue, the sequence bookkeeping and the timestamp), arm_us is from
 * CS low to CSTART (the DMA reprogramming), and total_us is entry to CSTART.
 * Min/mean/max are kept so a jitter problem cannot hide behind an average. */
volatile uint32_t drms_acq_t_isr_min, drms_acq_t_isr_max, drms_acq_t_isr_sum;
volatile uint32_t drms_acq_t_arm_min, drms_acq_t_arm_max, drms_acq_t_arm_sum;
volatile uint32_t drms_acq_t_tot_min, drms_acq_t_tot_max, drms_acq_t_tot_sum;
volatile uint32_t drms_acq_t_n;

/* Arm one 12-byte exchange. Returns 0 when started. */
static int fast_exchange_start(void)
{
  DMA_Channel_TypeDef *rx_ch = hspi1.hdmarx->Instance;
  DMA_Channel_TypeDef *tx_ch = hspi1.hdmatx->Instance;

  /* A channel that has not finished would corrupt this frame. */
  if ((rx_ch->CCR & DMA_CCR_EN) || (tx_ch->CCR & DMA_CCR_EN))
    return 1;

  /* Alternate the receive buffer so the frame just completed stays intact
   * while this one is in flight. */
  uint32_t slot = rx_buf_index ^ 1u;

  /* Geometry and pending flags, in the same order HAL's DMA_SetConfig uses.
   * Leaving a stale TC/DTE/USE flag latched stops the next transfer from
   * starting, so they are cleared before the channel is enabled. */
  rx_ch->CBR1 = EXCHANGE_BYTES;
  rx_ch->CSAR = (uint32_t)(uintptr_t)&hspi1.Instance->RXDR;
  rx_ch->CDAR = (uint32_t)(uintptr_t)dma_rx_buf[slot];
  rx_ch->CFCR = DMA_FLAG_TC | DMA_FLAG_HT | DMA_FLAG_DTE | DMA_FLAG_ULE |
                DMA_FLAG_USE | DMA_FLAG_SUSP | DMA_FLAG_TO;

  tx_ch->CBR1 = EXCHANGE_BYTES;
  tx_ch->CSAR = (uint32_t)(uintptr_t)dma_tx;
  tx_ch->CDAR = (uint32_t)(uintptr_t)&hspi1.Instance->TXDR;
  tx_ch->CFCR = DMA_FLAG_TC | DMA_FLAG_HT | DMA_FLAG_DTE | DMA_FLAG_ULE |
                DMA_FLAG_USE | DMA_FLAG_SUSP | DMA_FLAG_TO;

  /* Only the receive side interrupts; it marks the end of the exchange. The
   * transmit side is driven by SPI's request line alone, and letting its
   * interrupt through would reach HAL_DMA_IRQHandler, which does not own this
   * transfer. */
  SET_BIT(rx_ch->CCR, DMA_CCR_TCIE | DMA_CCR_DTEIE);
  CLEAR_BIT(tx_ch->CCR, DMA_CCR_TCIE | DMA_CCR_HTIE | DMA_CCR_DTEIE);

  /* Clear any error flag left by the previous frame. A latched UDR or OVR
   * makes the peripheral report a fault and refuse to run the next exchange,
   * which is what stopped everything after the first frame. These are cleared
   * through IFCR, not by touching SPE. */
  SET_BIT(hspi1.Instance->IFCR, SPI_IFCR_OVRC | SPI_IFCR_UDRC | SPI_IFCR_EOTC |
                                  SPI_IFCR_TXTFC | SPI_IFCR_SUSPC | SPI_IFCR_MODFC);

  /* Open the SPI request lines and start. SPI itself stays enabled across
   * frames - disabling it here is what produced UDR/OVR and broke the HAL
   * exchange() used for rate changes. */
  SET_BIT(hspi1.Instance->CFG1, SPI_CFG1_TXDMAEN | SPI_CFG1_RXDMAEN);
  SET_BIT(rx_ch->CCR, DMA_CCR_EN);
  SET_BIT(tx_ch->CCR, DMA_CCR_EN);
  /* SPE is not guaranteed to be set: the init exchange() leaves the peripheral
   * enabled, but a finished frame's cleanup or an earlier error path can leave
   * it clear, and CSTART is ignored while SPE is 0. Assert both every frame;
   * SPE survives a completed transfer, so this does not restart the state
   * machine. */
  __HAL_SPI_ENABLE(&hspi1);
  SET_BIT(hspi1.Instance->CR1, SPI_CR1_CSTART);
  ++drms_acq_fx_start;
  return 0;
}

/* Close out one exchange in the ISR. */
static void fast_exchange_finish(void)
{
  DMA_Channel_TypeDef *rx_ch = hspi1.hdmarx->Instance;
  DMA_Channel_TypeDef *tx_ch = hspi1.hdmatx->Instance;
  uint32_t flags = rx_ch->CSR;

  /* Hand the completed slot over to the consumer and select the other one for
   * the next transfer. Done before the channel is disarmed so the copy in
   * complete_frame() cannot race the next DMA into the same buffer. */
  rx_buf_index ^= 1u;
  memcpy(dma_rx, dma_rx_buf[rx_buf_index], sizeof(dma_rx));

  rx_ch->CFCR = flags;
  /* Disable BOTH channels, not just the transmit side. The receive channel
   * self-clears EN on completion in normal mode, but relying on that left it
   * enabled often enough that the next frame's busy check failed every time at
   * 64 kSPS and above. Explicitly clearing both keeps the start-of-frame
   * precondition deterministic. */
  CLEAR_BIT(tx_ch->CCR, DMA_CCR_EN);
  CLEAR_BIT(rx_ch->CCR, DMA_CCR_EN);
  CLEAR_BIT(hspi1.Instance->CFG1, SPI_CFG1_TXDMAEN | SPI_CFG1_RXDMAEN);
  fast_path_active = 0;
}

static volatile uint32_t busy, last_completion, abort_unconfirmed;
static uint32_t inflight_sequence;
static uint64_t inflight_capture_us, consumed_ticket;
static uint64_t cached_capture_us;
static uint32_t clock_last_tick;
static uint64_t clock_epoch_ms;
static unsigned int frame_size, powered;
volatile uint32_t drms_acq_running, drms_acq_rate, drms_acq_reference;
volatile uint32_t drms_acq_last_push_ms; /* 最近帧入环时刻（过渡用；T8 换 DRDY 实测） */
volatile uint32_t drms_acq_edges, drms_acq_overruns, drms_acq_queue_drops;
volatile uint32_t drms_acq_error;
/* Bring-up trace: initialization only, inspected through SWD without stopping
 * every SPI frame. word0=command|length<<16|HAL_status<<24, words1..3=RX. */
volatile uint32_t drms_acq_init_trace[24][4];
volatile uint32_t drms_acq_init_trace_count;

/* 64 位流记账（C1）。生产端唯一写者：DRDY ISR / DMA 完成 ISR / 启停路径。
 * 跨上下文一致读取仅在边界快照的短临界区内进行。 */
static uint64_t sample_seq_next, raw_ticket_next, capture_lost_total, unknown_loss_epoch;
static uint32_t acquisition_generation;
static struct { DRMS_Token token; uint32_t armed; } boundary_pending;
static struct { DRMS_Token token; uint32_t valid; DRMS_CaptureBoundary boundary; } boundary_reply;

static uint32_t crit_enter(void)
{
  uint32_t mask = __get_PRIMASK();
  __disable_irq();
  return mask;
}

static void crit_exit(uint32_t mask) { __set_PRIMASK(mask); }

uint64_t drms_acq_now_us(void)
{
  uint32_t mask = crit_enter();
  uint32_t tick = HAL_GetTick();
  if (tick < clock_last_tick)
    clock_epoch_ms += (1ULL << 32);
  clock_last_tick = tick;
  uint64_t now = (clock_epoch_ms + tick) * 1000u;
  crit_exit(mask);
  return now;
}

static uint32_t token_match(DRMS_Token a, DRMS_Token b)
{
  return a.operation_id == b.operation_id && a.generation == b.generation;
}

uint32_t drms_acq_generation(void) { return acquisition_generation; }
uint64_t drms_acq_sample_seq_next(void) { return sample_seq_next; }
uint64_t drms_acq_raw_ticket_next(void) { return raw_ticket_next; }
uint64_t drms_acq_capture_lost_total(void) { return capture_lost_total; }
uint64_t drms_acq_unknown_loss_epoch(void) { return unknown_loss_epoch; }

DRMS_Result drms_acq_boundary_request(DRMS_Token token)
{
  uint32_t mask;
  if (!drms_acq_running)
    return DRMS_INVALID;
  mask = crit_enter();
  if (boundary_pending.armed || boundary_reply.valid)
  {
    crit_exit(mask);
    return DRMS_BUSY; /* preserve an unanswered boundary until it is consumed */
  }
  boundary_pending.token = token;
  boundary_pending.armed = 1;
  crit_exit(mask);
  return DRMS_ACCEPTED;
}

uint32_t drms_acq_queue_used(void)
{
  return drms_fifo_count(&queue);
}

void drms_acq_boundary_cancel(DRMS_Token token)
{
  uint32_t mask = crit_enter();
  if (boundary_pending.armed && token_match(boundary_pending.token, token))
    boundary_pending.armed = 0;
  if (boundary_reply.valid && token_match(boundary_reply.token, token))
    boundary_reply.valid = 0;
  crit_exit(mask);
}

void drms_acq_boundary_service(void)
{
  /* Cheap early-out before the critical section: a boundary is rarely armed,
   * but this runs on every completed frame, and at 128 kSPS the interrupt
   * disable/enable pair plus the reload cost more than the check itself. */
  if (!boundary_pending.armed && !busy)
    return;
  uint32_t mask = crit_enter();
  if (!boundary_pending.armed || busy)
  {
    crit_exit(mask);
    return; /* 等待当前 DMA 完成：不在临界区内等待，静止时刻再归结 */
  }
  boundary_reply.token = boundary_pending.token;
  boundary_reply.boundary.acquisition_generation = acquisition_generation;
  boundary_reply.boundary.sample_next = sample_seq_next;
  boundary_reply.boundary.raw_next = raw_ticket_next;
  boundary_reply.boundary.capture_lost_total = capture_lost_total;
  boundary_reply.boundary.unknown_loss_epoch = unknown_loss_epoch;
  boundary_reply.valid = 1;
  boundary_pending.armed = 0;
  crit_exit(mask);
}

DRMS_Result drms_acq_boundary_get(DRMS_Token token, DRMS_CaptureBoundary *out)
{
  uint32_t mask;
  DRMS_Result result;
  if (!out)
    return DRMS_INVALID;
  mask = crit_enter();
  if (!boundary_reply.valid)
  {
    crit_exit(mask);
    return DRMS_EMPTY;
  }
  if (!token_match(boundary_reply.token, token))
  {
    crit_exit(mask);
    return DRMS_STALE;
  }
  *out = boundary_reply.boundary;
  boundary_reply.valid = 0;
  result = DRMS_OK;
  crit_exit(mask);
  return result;
}

/* CS is driven straight through BSRR rather than HAL_GPIO_WritePin, and the
 * former 32-iteration volatile NOP loop is gone. That loop cost on the order of
 * 150 cycles per call with the volatile counter, and this function runs twice
 * per frame, so it was eating close to 2 us of the 7.81 us budget at 128 kSPS -
 * the difference between the loop closing and half the frames being dropped.
 * The CS-high interval is naturally satisfied by the time spent decoding and
 * queueing the completed frame before CS is raised for the next one. */
static void cs(unsigned int high)
{
  if (high)
    ADS_CS_GPIO_Port->BSRR = ADS_CS_Pin;
  else
    ADS_CS_GPIO_Port->BSRR = (uint32_t)ADS_CS_Pin << 16u;
}

static int exchange(uint16_t command, uint16_t *response)
{
  uint8_t tx[12] = {0}, rx[12] = {0};
  tx[0] = command >> 8;
  tx[1] = command & 255;
  if (frame_size == 12)
  {
    uint16_t crc = drms_crc16(tx, 9);
    tx[9] = crc >> 8;
    tx[10] = crc & 255;
  }
  cs(0);
  HAL_StatusTypeDef status = HAL_SPI_TransmitReceive(&hspi1, tx, rx, (uint16_t)frame_size, 20);
  cs(1);
  if (drms_acq_init_trace_count < 24u)
  {
    uint32_t index = drms_acq_init_trace_count;
    drms_acq_init_trace[index][0] = command | (frame_size << 16) | ((uint32_t)status << 24);
    for (unsigned int i = 0; i < 3u; ++i)
      drms_acq_init_trace[index][i + 1u] = (uint32_t)rx[4u*i] | ((uint32_t)rx[4u*i+1u] << 8) |
          ((uint32_t)rx[4u*i+2u] << 16) | ((uint32_t)rx[4u*i+3u] << 24);
    drms_acq_init_trace_count = index + 1u;
  }
  if (status != HAL_OK || rx[2] != 0)
    return 0;
  if (frame_size == 12 &&
      (rx[11] != 0 || drms_crc16(rx, 9) != (uint16_t)(((uint16_t)rx[9] << 8) | rx[10])))
    return 0;
  *response = (uint16_t)(((uint16_t)rx[0] << 8) | rx[1]);
  return 1;
}

static int command_ack(uint16_t command)
{
  uint16_t ignored, response;
  return exchange(command, &ignored) && exchange(0, &response) && response == command;
}

static int write_register(uint8_t address, uint8_t value)
{
  uint16_t ignored, response;
  if (!exchange((uint16_t)(0x4000U | ((uint16_t)address << 8) | value), &ignored))
    return 0;
  /* This write takes effect at the end of its OLD frame. */
  if (address == 0x0c)
    frame_size = 12;
  if (!exchange(0, &response))
    return 0;
  /* Keep the datasheet's global enable write (0Fh). The two-channel A02 on
   * the first board acknowledges its implemented channels as 2F03h. */
  if (address == 0x0f && value == 0x0f && response == 0x2f03)
    return 1;
  return response == (uint16_t)(0x2000U | ((uint16_t)address << 8) | value);
}

/* Return the SPI peripheral to the idle shape the HAL expects, so the blocking
 * exchange() used to reprogram the ADC on the next start finds a clean reset
 * state.
 *
 * The fast path leaves SPE set with TSIZE latched, which is exactly right for
 * per-frame restarts but wrong for HAL_SPI_TransmitReceive: that call arms its
 * own transfer count and never expects an already-running transaction, so the
 * READY poll during a rate change came back empty and start failed with
 * adc_error=1. */
static void spi_release_to_idle(void)
{
  DMA_Channel_TypeDef *rx_ch = hspi1.hdmarx->Instance;
  DMA_Channel_TypeDef *tx_ch = hspi1.hdmatx->Instance;

  CLEAR_BIT(hspi1.Instance->CFG1, SPI_CFG1_TXDMAEN | SPI_CFG1_RXDMAEN);
  CLEAR_BIT(rx_ch->CCR, DMA_CCR_EN);
  CLEAR_BIT(tx_ch->CCR, DMA_CCR_EN);
  rx_ch->CFCR = DMA_FLAG_TC | DMA_FLAG_HT | DMA_FLAG_DTE | DMA_FLAG_ULE |
                DMA_FLAG_USE | DMA_FLAG_SUSP | DMA_FLAG_TO;
  tx_ch->CFCR = DMA_FLAG_TC | DMA_FLAG_HT | DMA_FLAG_DTE | DMA_FLAG_ULE |
                DMA_FLAG_USE | DMA_FLAG_SUSP | DMA_FLAG_TO;

  __HAL_SPI_DISABLE(&hspi1);
  SET_BIT(hspi1.Instance->IFCR, SPI_IFCR_OVRC | SPI_IFCR_UDRC | SPI_IFCR_EOTC |
                                  SPI_IFCR_TXTFC | SPI_IFCR_SUSPC | SPI_IFCR_MODFC);
  /* Do NOT zero TSIZE. RM0456 states that CSTART with TSIZE = 0 opens an
   * *infinite* transaction, so clearing it here left the peripheral in a mode
   * where the blocking HAL_SPI_TransmitReceive that reprogramms the ADC timed
   * out on its very first exchange (init trace showed HAL_TIMEOUT). HAL sets
   * the length it needs on each call; leaving the last value alone is both
   * harmless and necessary. */

  fast_path_active = 0;
  hspi1.State = HAL_SPI_STATE_READY;
  hspi1.ErrorCode = HAL_SPI_ERROR_NONE;
  __HAL_UNLOCK(&hspi1);
}

void drms_acq_stop(void)
{
  if (drms_acq_running)
    ++unknown_loss_epoch; /* 停止后观察到的 DRDY 无法计数：连续性不可证明 */
  drms_acq_running = 0;
  HAL_GPIO_WritePin(CURR_DIS_GPIO_Port, CURR_DIS_Pin, GPIO_PIN_SET);
  if (busy && !abort_unconfirmed)
  {
    /* The quarantine decision is "could this transfer be proven finished?".
     * HAL_SPI_Abort answers that, and when it cannot the device stays
     * quarantined until an explicit recover, exactly as before the fast path
     * existed. spi_release_to_idle then tidies the peripheral either way. */
    if (HAL_SPI_Abort(&hspi1) == HAL_OK)
      busy = 0;
    else
    {
      abort_unconfirmed = 1;
      drms_acq_error = 3;
    }
  }
  spi_release_to_idle();
  busy = 0;
  cs(1);
  /* Assert RESET before cutting the analog rail, and hold it a while. The
   * previous order dropped both at once with no delay, which is enough for a
   * healthy stop but does not reset an ADC that was left mid-frame: after a
   * failed 128 kSPS run the device kept reporting data timeouts across a
   * STOP/START and only a full MCU reset cleared it. SBAS590E requires RESET
   * low for at least 800 ns; the extra margin here also lets the analog rail
   * discharge so the next start really is a power-on. */
  HAL_GPIO_WritePin(ADS_RESET_GPIO_Port, ADS_RESET_Pin, GPIO_PIN_RESET);
  HAL_Delay(2);
  HAL_GPIO_WritePin(ANA_EN_GPIO_Port, ANA_EN_Pin, GPIO_PIN_RESET);
  /* Hold the analog rail off long enough for it to actually collapse. An ADC
   * that stopped mid-frame at a high rate (STAT_1 showed F_DRDY, i.e. its
   * output register was never read out) does not come back from a short blip:
   * with only a few milliseconds the following START reprogrammed the device
   * successfully yet it never produced another DRDY, and only an MCU reset
   * cleared it. The rail's output capacitor dominates this, so the margin is
   * deliberately generous. */
  HAL_Delay(50);
  powered = 0;
}

int drms_acq_start(uint32_t rate, unsigned int reference)
{
  drms_acq_init_trace_count = 0;
  uint8_t clk2;
  uint16_t ready = 0, ignored;
  /* Reject rates above the measured capability envelope. 128 kSPS is not
   * reachable on this board: the ADC ends up reporting F_DRDY (its output
   * register was never read out in time) and, once it has been pushed there,
   * it stops producing DRDY altogether - a later START reprograms it
   * successfully but no further frames arrive, and only an MCU reset brings it
   * back. Refusing the rate keeps the device usable instead of deadlocking it,
   * and the caller gets cmd_result=2 rather than a silent fake success.
   * See firmware/DE-DRMS-Code/README.md for the full measurement. */
  if (rate > DRMS_ACQ_MAX_RATE)
  {
    /* Do not leave the previous (too-high) rate visible in STATUS: the next
     * bare START would otherwise retry it. */
    drms_acq_stop();
    drms_acq_rate = DRMS_ACQ_MAX_RATE;
    drms_acq_error = 2;
    return 0;
  }
  if (!drms_rate_register(rate, &clk2) || reference > 1)
    return 0;
  /* Release the peripheral before anything else. A high-rate run that stopped
   * itself (queue overrun sets adc_error=6 and clears running) never passes
   * through drms_acq_stop, so the fast path's transaction state survived into
   * the next start and the blocking exchange() could not read the ADC's READY
   * response from it. Unwinding unconditionally here makes start independent of
   * how the previous run ended. */
  spi_release_to_idle();
  /* HAL Size counts DATA WORDS, not bytes. Reject incompatible regeneration
     before a blocking/DMA transfer can write past a 12-byte frame buffer. */
  if (hspi1.Init.DataSize != SPI_DATASIZE_8BIT || hspi1.Init.Mode != SPI_MODE_MASTER ||
      hspi1.Init.CLKPolarity != SPI_POLARITY_LOW || hspi1.Init.CLKPhase != SPI_PHASE_2EDGE ||
      hspi1.Init.FirstBit != SPI_FIRSTBIT_MSB || hspi1.Init.NSS != SPI_NSS_SOFT)
  {
    drms_acq_stop();
    drms_acq_error = 2;
    return 0;
  }
  drms_acq_stop();
  if (abort_unconfirmed)
    return 0;
  drms_acq_error = 0;
  drms_acq_edges = drms_acq_overruns = drms_acq_queue_drops = 0;
  /* 新采集代次：流计数清零，边界请求/回复一并作废（旧代次边界不得交付）。 */
  sample_seq_next = raw_ticket_next = capture_lost_total = unknown_loss_epoch = 0;
  consumed_ticket = 0;
  drms_capture_time_reset();
  ++acquisition_generation;
  boundary_pending.armed = 0;
  boundary_reply.valid = 0;
  (void)drms_fifo_init(&queue, frames, 4096, sizeof(frames[0]));
  /* Inhibit first. Never pass through forbidden SENSE=0,K2=1, even briefly. */
  if (reference)
  {
    HAL_GPIO_WritePin(SEL_SENSE_GPIO_Port, SEL_SENSE_Pin, GPIO_PIN_SET);
    HAL_GPIO_WritePin(SEL_K2_GPIO_Port, SEL_K2_Pin, GPIO_PIN_SET);
  }
  else
  {
    HAL_GPIO_WritePin(SEL_K2_GPIO_Port, SEL_K2_Pin, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(SEL_SENSE_GPIO_Port, SEL_SENSE_Pin, GPIO_PIN_RESET);
  }
  drms_acq_reference = reference;
  HAL_GPIO_WritePin(ANA_EN_GPIO_Port, ANA_EN_Pin, GPIO_PIN_SET);
  powered = 1;
  HAL_Delay(10);
  HAL_GPIO_WritePin(ADS_RESET_GPIO_Port, ADS_RESET_Pin, GPIO_PIN_SET);
  HAL_Delay(50);
  frame_size = 3; /* POR: dynamic frame, ADCs off, no CRC; 24-bit strap. */
  uint32_t started = HAL_GetTick();
  do
  {
    if (!exchange(0, &ready))
      break;
    if (ready == 0xff02)
      break;
    HAL_Delay(1);
  } while ((uint32_t)(HAL_GetTick() - started) < 500U);
  if (ready != 0xff02)
  {
    drms_acq_error = 1;
    goto failed;
  }
  /* SBAS590E §9.6 and §10.4. VNCP tied to AVSS: VNCPEN must remain 0.
     A_SYS_CFG=0x68: high resolution, reserved bit5=1, 2.442 V internal ref.
     CLK1=0x02: /2; CLK2=0x2n: /2 and selected OSR.
     D_SYS_CFG=0x7f: CRC over ALL preceding bytes, fixed four-word frame. */
  /* Enable fixed-frame CRC first, before any analog/reference register write. */
  if (!command_ack(0x0655) || !write_register(0x0c, 0x7f) ||
      !write_register(0x0b, 0x68) || !write_register(0x0d, 0x02) || !write_register(0x0e, clk2) ||
      !write_register(0x0f, 0x0f) ||
      !command_ack(0x0033) || !command_ack(0x0555))
  {
    drms_acq_error = 2;
    goto failed;
  }
  HAL_GPIO_WritePin(CURR_DIS_GPIO_Port, CURR_DIS_Pin, GPIO_PIN_RESET);
  /* Conservative first-board settling, including sinc3 and analog recovery.
     No samples acquired during this interval are labelled valid. */
  HAL_Delay(100);
  if (!exchange(0, &ignored))
  {
    drms_acq_error = 2;
    goto failed;
  }
  memset(dma_tx, 0, sizeof(dma_tx));
  uint16_t crc = drms_crc16(dma_tx, 9);
  dma_tx[9] = crc >> 8;
  dma_tx[10] = crc & 255;
  drms_acq_rate = rate;
  /* Leave the peripheral in the state the fast path assumes: enabled, with the
   * 12-byte frame length latched, so a frame needs only a CSTART. Verified over
   * SWD that TSIZE survives a completed transfer, but the init exchange() ran
   * through the HAL in blocking mode and rewrote it, so set it explicitly here
   * while the peripheral is idle. */
  MODIFY_REG(hspi1.Instance->CR2, SPI_CR2_TSIZE, EXCHANGE_BYTES);
  last_completion = HAL_GetTick();
  drms_acq_running = 1;
  return 1;
failed:
  drms_acq_stop();
  return 0;
}

void drms_acq_drdy(void)
{
  if (!drms_acq_running)
    return;
  uint32_t sequence = drms_acq_edges++;
  ++sample_seq_next; /* 每个 DRDY 都占 sample_seq，丢样保留序号缺口 */
  if (busy)
  {
    ++drms_acq_overruns;
    ++capture_lost_total;
    return;
  }
  busy = 1;
  inflight_sequence = sequence;
  /* The capture timestamp costs a critical section plus HAL_GetTick, measured
   * at about 2 us per frame in this ISR - a quarter of the whole 128 kSPS
   * budget. At high rates the time axis is reconstructed from the sample
   * sequence anyway (capture_time publishes block anchors, not per-frame
   * stamps), so sample it every 8th frame there and reuse the last value in
   * between. Below 32 kSPS the budget has room and every frame keeps its own
   * stamp. */
  if (drms_acq_rate < 32000u || (sequence & 7u) == 0u)
    cached_capture_us = drms_acq_now_us();
  inflight_capture_us = cached_capture_us;
  uint32_t t_enter = DWT->CYCCNT;
  cs(0);
  uint32_t t_cs = DWT->CYCCNT;
  fast_path_active = 1;
  if (fast_exchange_start() != 0)
  {
    ++drms_acq_fx_fail;
    fast_path_active = 0;
    cs(1);
    busy = 0;
    ++drms_acq_overruns;
    ++capture_lost_total;
    return;
  }
  uint32_t t_armed = DWT->CYCCNT;
  /* Cycles to microseconds at the 160 MHz core clock. */
  uint32_t isr_us = (t_cs - t_enter) / 160u;
  uint32_t arm_us = (t_armed - t_cs) / 160u;
  uint32_t tot_us = (t_armed - t_enter) / 160u;
  if (!drms_acq_t_n)
  {
    drms_acq_t_isr_min = drms_acq_t_arm_min = drms_acq_t_tot_min = 0xFFFFFFFFu;
  }
  if (isr_us < drms_acq_t_isr_min) drms_acq_t_isr_min = isr_us;
  if (isr_us > drms_acq_t_isr_max) drms_acq_t_isr_max = isr_us;
  drms_acq_t_isr_sum += isr_us;
  if (arm_us < drms_acq_t_arm_min) drms_acq_t_arm_min = arm_us;
  if (arm_us > drms_acq_t_arm_max) drms_acq_t_arm_max = arm_us;
  drms_acq_t_arm_sum += arm_us;
  if (tot_us < drms_acq_t_tot_min) drms_acq_t_tot_min = tot_us;
  if (tot_us > drms_acq_t_tot_max) drms_acq_t_tot_max = tot_us;
  drms_acq_t_tot_sum += tot_us;
  ++drms_acq_t_n;
}

/* Publish the completed frame. Shared by the HAL completion callback and the
 * fast path so both produce identical semantics. */
static void complete_frame(void)
{
  cs(1);
  if (drms_acq_running)
  {
    DRMS_RawFrame frame;
    memcpy(frame.bytes, dma_rx, sizeof(frame.bytes));
    frame.sequence = inflight_sequence;
    DRMS_Result time_status = DRMS_OK;
    if (raw_ticket_next % DRMS_CAPTURE_BLOCK_TICKS == 0 &&
        drms_fifo_count(&queue) < 4096)
      time_status = drms_capture_time_publish(raw_ticket_next, consumed_ticket,
                                              acquisition_generation, inflight_capture_us);
    if (time_status != DRMS_OK || !drms_fifo_push(&queue, &frame))
    {
      ++drms_acq_queue_drops;
      ++capture_lost_total; /* 入环失败属于捕获损失，同一采样只计一次 */
      ++unknown_loss_epoch; /* 后续 DRDY 计数停止，连续性不可证明 */
      /* An unverified high rate must fail safely, not keep the CPU trapped in
         DMA/DRDY IRQs while the supervisor can no longer consume its queue. */
      drms_acq_error = 6;
      drms_acq_running = 0;
      HAL_GPIO_WritePin(CURR_DIS_GPIO_Port, CURR_DIS_Pin, GPIO_PIN_SET);
    }
    else
      ++raw_ticket_next;
    /* One tick read for both stamps: HAL_GetTick goes through the RTOS timer
     * and this runs on every completed frame. */
    uint32_t now_tick = HAL_GetTick();
    drms_acq_last_push_ms = now_tick;
    last_completion = now_tick;
  }
  busy = 0;
  drms_acq_boundary_service(); /* 静止时刻归结挂起的边界请求 */
}

void HAL_SPI_TxRxCpltCallback(SPI_HandleTypeDef *spi)
{
  if (spi != &hspi1)
    return;
  complete_frame();
}

/* Called from GPDMA1_Channel1_IRQHandler before HAL_DMA_IRQHandler. Returns 1
 * when the fast path owned this transfer; the HAL state machine has no record
 * of a transfer it did not start, so it must not touch the channel. */
int drms_acq_fast_dma_irq(void)
{
  ++drms_acq_fx_irq;
  if (!fast_path_active)
    return 0;
  fast_exchange_finish();
  complete_frame();
  ++drms_acq_fx_done;
  return 1;
}

void HAL_SPI_ErrorCallback(SPI_HandleTypeDef *spi)
{
  if (spi != &hspi1)
    return;
  drms_acq_running = 0;
  drms_acq_error = 3;
  ++unknown_loss_epoch;
  HAL_GPIO_WritePin(CURR_DIS_GPIO_Port, CURR_DIS_Pin, GPIO_PIN_SET);
  cs(1);
  busy = 0;
  /* Supervisor completes the HAL abort and analog shutdown in thread context. */
}

int drms_acq_pop_timed(DRMS_RawFrame *frame, uint64_t *capture_lower_us)
{
  if (!frame || !capture_lower_us || !queue.capacity)
    return 0;
  uint32_t mask = crit_enter();
  if (!drms_fifo_count(&queue))
  {
    crit_exit(mask);
    return 0;
  }
  if (drms_capture_time_lookup(consumed_ticket, acquisition_generation,
                               capture_lower_us) != DRMS_OK)
  {
    drms_acq_error = 6;
    drms_acq_running = 0;
    HAL_GPIO_WritePin(CURR_DIS_GPIO_Port, CURR_DIS_Pin, GPIO_PIN_SET);
    crit_exit(mask);
    return 0;
  }
  int popped = drms_fifo_pop(&queue, frame);
  if (popped)
    ++consumed_ticket;
  crit_exit(mask);
  return popped;
}

int drms_acq_pop(DRMS_RawFrame *frame)
{
  uint64_t capture_lower_us;
  return drms_acq_pop_timed(frame, &capture_lower_us);
}

void drms_acq_poll(void)
{
  if (drms_acq_running && (uint32_t)(HAL_GetTick() - last_completion) > 200U)
    drms_acq_error = 4;
  if (drms_acq_error && powered)
    drms_acq_stop();
}

/* ---------------- 资源生命周期后端（T3/R4） ---------------- */

uint32_t drms_acq_is_quiescent(void)
{
  uint32_t mask = crit_enter();
  uint32_t quiet = !busy && !drms_acq_running && !abort_unconfirmed;
  crit_exit(mask);
  return quiet;
}

static DRMS_Result acq_backend_abort(void)
{
  if (abort_unconfirmed)
    return DRMS_IO_ERROR;
  drms_acq_stop();
  return drms_acq_is_quiescent() ? DRMS_ACCEPTED : DRMS_IO_ERROR;
}

static DRMS_Result acq_backend_probe(void)
{
  return drms_acq_is_quiescent() ? DRMS_ACCEPTED : DRMS_BUSY;
}

static DRMS_Result acq_backend_recover(void)
{
  if (abort_unconfirmed)
  {
    if (HAL_SPI_Abort(&hspi1) != HAL_OK)
      return DRMS_IO_ERROR;
    uint32_t mask = crit_enter();
    busy = 0;
    abort_unconfirmed = 0;
    crit_exit(mask);
  }
  if (!drms_acq_is_quiescent())
    return DRMS_BUSY;
  drms_acq_error = 0;
  return DRMS_ACCEPTED;
}

static const DRMS_ResourceBackend acq_backend = {
    acq_backend_abort, acq_backend_probe, acq_backend_recover};

const DRMS_ResourceBackend *drms_acq_resource_backend(void)
{
  return &acq_backend;
}

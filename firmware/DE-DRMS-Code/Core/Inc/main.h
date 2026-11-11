/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.h
  * @brief          : Header for main.c file.
  *                   This file contains the common defines of the application.
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2026 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */

/* Define to prevent recursive inclusion -------------------------------------*/
#ifndef __MAIN_H
#define __MAIN_H

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/
#include "stm32u5xx_hal.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */

/* USER CODE END Includes */

/* Exported types ------------------------------------------------------------*/
/* USER CODE BEGIN ET */

/* USER CODE END ET */

/* Exported constants --------------------------------------------------------*/
/* USER CODE BEGIN EC */

/* USER CODE END EC */

/* Exported macro ------------------------------------------------------------*/
/* USER CODE BEGIN EM */

/* USER CODE END EM */

/* Exported functions prototypes ---------------------------------------------*/
void Error_Handler(void);

/* USER CODE BEGIN EFP */

/* USER CODE END EFP */

/* Private defines -----------------------------------------------------------*/
#define USB_VBUS_N_Pin GPIO_PIN_13
#define USB_VBUS_N_GPIO_Port GPIOC
#define BQ_EN_Pin GPIO_PIN_1
#define BQ_EN_GPIO_Port GPIOC
#define BQ_CHG_Pin GPIO_PIN_2
#define BQ_CHG_GPIO_Port GPIOC
#define ANA_EN_Pin GPIO_PIN_3
#define ANA_EN_GPIO_Port GPIOC
#define MEAS_BTN_Pin GPIO_PIN_0
#define MEAS_BTN_GPIO_Port GPIOA
#define MEAS_BTN_EXTI_IRQn EXTI0_IRQn
#define ADS_DONE_Pin GPIO_PIN_1
#define ADS_DONE_GPIO_Port GPIOA
#define ADS_RESET_Pin GPIO_PIN_2
#define ADS_RESET_GPIO_Port GPIOA
#define ADS_DRDY_Pin GPIO_PIN_3
#define ADS_DRDY_GPIO_Port GPIOA
#define ADS_DRDY_EXTI_IRQn EXTI3_IRQn
#define ADS_CS_Pin GPIO_PIN_4
#define ADS_CS_GPIO_Port GPIOA
#define CURR_DIS_Pin GPIO_PIN_4
#define CURR_DIS_GPIO_Port GPIOC
#define PWR_BTN_Pin GPIO_PIN_5
#define PWR_BTN_GPIO_Port GPIOC
#define PWR_BTN_EXTI_IRQn EXTI5_IRQn
#define SEL_K2_Pin GPIO_PIN_0
#define SEL_K2_GPIO_Port GPIOB
#define SEL_SENSE_Pin GPIO_PIN_1
#define SEL_SENSE_GPIO_Port GPIOB
#define LED_GREEN_Pin GPIO_PIN_13
#define LED_GREEN_GPIO_Port GPIOB
#define LED_YELLOW_Pin GPIO_PIN_14
#define LED_YELLOW_GPIO_Port GPIOB
#define LED_ORANGE_Pin GPIO_PIN_15
#define LED_ORANGE_GPIO_Port GPIOB
#define LED_RED_Pin GPIO_PIN_6
#define LED_RED_GPIO_Port GPIOC
#define PWR_LED_Pin GPIO_PIN_7
#define PWR_LED_GPIO_Port GPIOC
#define SD_CD_Pin GPIO_PIN_15
#define SD_CD_GPIO_Port GPIOA
#define SD_CD_EXTI_IRQn EXTI15_IRQn
#define BQ_PG_Pin GPIO_PIN_5
#define BQ_PG_GPIO_Port GPIOB

/* USER CODE BEGIN Private defines */
/* First-board card detect is unusable and stays bypassed.

 * PA15 itself is configured correctly (GPIOA MODER=00 input, PUPDR=01 pull-up,
 * confirmed over SWD) but reads high with the card fully inserted, so the
 * socket's CD contact never closes the R46 path to ground. Users decided to
 * keep the bypass rather than rework the socket, so treat the TF card as
 * permanently present.

 * Consequences to keep in mind:
 *  - Card removal is no longer detected. Pulling the card while recording
 *    only fails at the next I/O, and MSC export will not revoke on removal.
 *  - SD initialization is attempted even with no card; a missing or bad card
 *    surfaces as a mount failure (sd=0) instead of "no card".
 *  - An empty socket raises the standby current draw slightly.

 * Revisit this if the socket is ever reworked: set to 0 and the original
 * PA15-gated paths in sdmmc.c and drms_storage.c come back unchanged.
 */
#define DRMS_SD_DIAGNOSTIC_IGNORE_CD 1

/* USER CODE END Private defines */

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */

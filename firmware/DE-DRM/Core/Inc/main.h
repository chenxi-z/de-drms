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
/* DC prototype target (design appendix F): CS moved PA4 -> PA8; PA4 reserved.
 * Do not flash onto the unmodified V1.2 wiring. See CUBEMX_SETUP.md before
 * regenerating: the tracked IOC still describes the previous board mapping.
 */
#define VBAT_MON_Pin GPIO_PIN_0
#define VBAT_MON_GPIO_Port GPIOC
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
#define ADS_CS_Pin GPIO_PIN_8
#define ADS_CS_GPIO_Port GPIOA
#define SEL_K2_Pin GPIO_PIN_0
#define SEL_K2_GPIO_Port GPIOB
#define PWR_BTN_Pin GPIO_PIN_1
#define PWR_BTN_GPIO_Port GPIOB
#define PWR_BTN_EXTI_IRQn EXTI1_IRQn
#define SEL_SENSE_Pin GPIO_PIN_2
#define SEL_SENSE_GPIO_Port GPIOB
#define CURR_DIS_Pin GPIO_PIN_10
#define CURR_DIS_GPIO_Port GPIOB
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
#define USB_VBUS_N_Pin GPIO_PIN_13
#define USB_VBUS_N_GPIO_Port GPIOC
#define SD_CD_Pin GPIO_PIN_15
#define SD_CD_GPIO_Port GPIOA
#define SD_CD_EXTI_IRQn EXTI15_IRQn
#define BQ_PG_Pin GPIO_PIN_5
#define BQ_PG_GPIO_Port GPIOB

/* USER CODE BEGIN Private defines */

/* USER CODE END Private defines */

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */

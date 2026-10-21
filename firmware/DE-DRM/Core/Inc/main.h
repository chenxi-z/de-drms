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
#define VBAT_MON_Pin GPIO_PIN_0
#define VBAT_MON_GPIO_Port GPIOC
#define VBUS_MON_Pin GPIO_PIN_1
#define VBUS_MON_GPIO_Port GPIOC
#define ISET_HI_Pin GPIO_PIN_2
#define ISET_HI_GPIO_Port GPIOC
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
#define SD_PWR_EN_Pin GPIO_PIN_8
#define SD_PWR_EN_GPIO_Port GPIOA
#define SD_CD_Pin GPIO_PIN_15
#define SD_CD_GPIO_Port GPIOA
#define SD_CD_EXTI_IRQn EXTI15_IRQn
#define BQ_TS_Pin GPIO_PIN_5
#define BQ_TS_GPIO_Port GPIOB

/* USER CODE BEGIN Private defines */

/* USER CODE END Private defines */

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */

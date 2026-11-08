/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file    gpio.c
  * @brief   This file provides code for the configuration
  *          of all used GPIO pins.
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

/* Includes ------------------------------------------------------------------*/
#include "gpio.h"

/* USER CODE BEGIN 0 */

/* USER CODE END 0 */

/*----------------------------------------------------------------------------*/
/* Configure GPIO                                                             */
/*----------------------------------------------------------------------------*/
/* USER CODE BEGIN 1 */

/* USER CODE END 1 */

/** Configure pins
     PC14-OSC32_IN (PC14)   ------> RCC_OSC32_IN
     PC15-OSC32_OUT (PC15)   ------> RCC_OSC32_OUT
     PH0-OSC_IN (PH0)   ------> RCC_OSC_IN
     PH1-OSC_OUT (PH1)   ------> RCC_OSC_OUT
     PA13 (JTMS/SWDIO)   ------> DEBUG_JTMS-SWDIO
     PA14 (JTCK/SWCLK)   ------> DEBUG_JTCK-SWCLK
     PB3 (JTDO/TRACESWO)   ------> DEBUG_JTDO-SWO
*/
void MX_GPIO_Init(void)
{

  GPIO_InitTypeDef GPIO_InitStruct = {0};

  /* GPIO Ports Clock Enable */
  __HAL_RCC_GPIOC_CLK_ENABLE();
  __HAL_RCC_GPIOH_CLK_ENABLE();
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();
  __HAL_RCC_GPIOD_CLK_ENABLE();

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOC, BQ_EN_Pin|ANA_EN_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(ADS_RESET_GPIO_Port, ADS_RESET_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(ADS_CS_GPIO_Port, ADS_CS_Pin, GPIO_PIN_SET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOC, CURR_DIS_Pin|LED_RED_Pin|PWR_LED_Pin, GPIO_PIN_SET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOB, SEL_K2_Pin|SEL_SENSE_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOB, LED_GREEN_Pin|LED_YELLOW_Pin|LED_ORANGE_Pin, GPIO_PIN_SET);

  /*Configure GPIO pins : USB_VBUS_N_Pin BQ_CHG_Pin */
  GPIO_InitStruct.Pin = USB_VBUS_N_Pin|BQ_CHG_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_PULLUP;
  HAL_GPIO_Init(GPIOC, &GPIO_InitStruct);

  /*Configure GPIO pins : BQ_EN_Pin ANA_EN_Pin CURR_DIS_Pin LED_RED_Pin
                           PWR_LED_Pin */
  GPIO_InitStruct.Pin = BQ_EN_Pin|ANA_EN_Pin|CURR_DIS_Pin|LED_RED_Pin
                          |PWR_LED_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOC, &GPIO_InitStruct);

  /*Configure GPIO pins : MEAS_BTN_Pin ADS_DRDY_Pin */
  GPIO_InitStruct.Pin = MEAS_BTN_Pin|ADS_DRDY_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_IT_FALLING;
  GPIO_InitStruct.Pull = GPIO_PULLUP;
  HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

  /*Configure GPIO pin : ADS_DONE_Pin */
  GPIO_InitStruct.Pin = ADS_DONE_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  HAL_GPIO_Init(ADS_DONE_GPIO_Port, &GPIO_InitStruct);

  /*Configure GPIO pins : ADS_RESET_Pin ADS_CS_Pin */
  GPIO_InitStruct.Pin = ADS_RESET_Pin|ADS_CS_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

  /*Configure GPIO pin : PWR_BTN_Pin */
  GPIO_InitStruct.Pin = PWR_BTN_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_IT_FALLING;
  GPIO_InitStruct.Pull = GPIO_PULLUP;
  HAL_GPIO_Init(PWR_BTN_GPIO_Port, &GPIO_InitStruct);

  /*Configure GPIO pins : SEL_K2_Pin SEL_SENSE_Pin LED_GREEN_Pin LED_YELLOW_Pin
                           LED_ORANGE_Pin */
  GPIO_InitStruct.Pin = SEL_K2_Pin|SEL_SENSE_Pin|LED_GREEN_Pin|LED_YELLOW_Pin
                          |LED_ORANGE_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

  /*Configure GPIO pin : SD_CD_Pin */
  GPIO_InitStruct.Pin = SD_CD_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_IT_RISING_FALLING;
  GPIO_InitStruct.Pull = GPIO_PULLUP;
  HAL_GPIO_Init(SD_CD_GPIO_Port, &GPIO_InitStruct);

  /*Configure GPIO pin : BQ_PG_Pin */
  GPIO_InitStruct.Pin = BQ_PG_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_PULLUP;
  HAL_GPIO_Init(BQ_PG_GPIO_Port, &GPIO_InitStruct);

  /* EXTI interrupt init*/
  HAL_NVIC_SetPriority(EXTI0_IRQn, 11, 0);
  HAL_NVIC_EnableIRQ(EXTI0_IRQn);

  HAL_NVIC_SetPriority(EXTI3_IRQn, 5, 0);
  HAL_NVIC_EnableIRQ(EXTI3_IRQn);

  HAL_NVIC_SetPriority(EXTI5_IRQn, 11, 0);
  HAL_NVIC_EnableIRQ(EXTI5_IRQn);

  HAL_NVIC_SetPriority(EXTI15_IRQn, 10, 0);
  HAL_NVIC_EnableIRQ(EXTI15_IRQn);

}

/* USER CODE BEGIN 2 */

/* USER CODE END 2 */

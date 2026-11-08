#!/usr/bin/env python3
"""Restore known CubeMX template defects without changing the IOC or USER blocks.

Default is read-only. Run with --apply after Generate Code, then build and test.
Unknown template layouts fail closed instead of guessing an edit.
"""
import argparse
from pathlib import Path
import re

DEFAULT = Path(__file__).resolve().parents[1] / 'firmware/DE-DRMS-Code'
SOURCES = ('drms_usb', 'drms_storage', 'drms_msc', 'drms_console', 'drms_runtime', 'drms_cdc', 'drms_measurement', 'drms_fifo', 'drms_acquisition',
           'drms_calibration_codec', 'drms_calibration_journal', 'drms_calibration_flash', 'drms_log_codec', 'drms_logging', 'drms_time_codec', 'drms_aux', 'drms_command', 'drms_application', 'drms_power', 'drms_power_stm32')


def replace_known(text, old, new, name):
    if new in text:
        return text
    if old not in text:
        raise ValueError(f'{name}: unknown CubeMX template; manual review required')
    return text.replace(old, new, 1)


def repaired(relative, text):
    if relative == 'STM32U575xx_FLASH.ld':
        match = re.search(r'(ROM\s*\(rx\)\s*:\s*ORIGIN = 0x08000000,\s*LENGTH = )(\d+)K', text)
        if not match or match[2] not in ('1008', '1024', '2048'):
            raise ValueError('unknown Flash layout; check MCU capacity')
        text = text[:match.start(2)] + '1008' + text[match.end(2):]
        if 'CALDATA (rx)' not in text:
            text = text.replace('  SRAM4\t(xrw)',
                '  CALDATA (rx) : ORIGIN = 0x080FC000, LENGTH = 16K /* two 8 KiB settings slots */\n  SRAM4\t(xrw)', 1)
        if not re.search(r'CALDATA\s*\(rx\)\s*:\s*ORIGIN = 0x080FC000,\s*LENGTH = 16K', text):
            raise ValueError('unknown linker settings partition')
        return text
    if relative == 'Core/Src/sdmmc.c':
        if 'HAL_StatusTypeDef sd_init_status = HAL_ERROR;' not in text or 'static HAL_StatusTypeDef sd_startup_init(' not in text:
            raise ValueError('SD USER block lost its status definition; review before patching')
        return replace_known(text,
            '  if (HAL_SD_Init(&hsd1) != HAL_OK)\n  {\n    Error_Handler();\n  }',
            '  /* CubeMX regeneration guard: keep this failure nonfatal. */\n'
            '  sd_init_status = sd_startup_init(&hsd1);\n'
            '  if (sd_init_status != HAL_OK)\n  {\n'
            '    (void)HAL_SD_DeInit(&hsd1);\n    return;\n  }', relative)
    if relative == 'USBX/App/app_usbx_device.c':
        return replace_known(text,
            '  ux_dcd_stm32_initialize((ULONG)USB_OTG_FS, (ULONG)&hpcd_USB_OTG_FS);',
            '  ret = ux_dcd_stm32_initialize((ULONG)USB_OTG_FS, (ULONG)&hpcd_USB_OTG_FS);\n'
            '  if (ret != UX_SUCCESS)\n    return ret;', relative)
    if relative.endswith('ux_dcd_stm32_transfer_request.c'):
        text = replace_known(text, 'ULONG                   endpoint_type;\n',
            'ULONG                   endpoint_type;\nUX_INTERRUPT_SAVE_AREA\n', relative)
        old = ('    if (transfer_request -> ux_slave_transfer_request_phase == UX_TRANSFER_PHASE_DATA_OUT)\n'
               '    {\n        HAL_PCD_EP_Transmit')
        new = ('    /* The core publishes PENDING before calling this DCD. A reset/abort IRQ\n'
               '       may cancel it in between. Check and arm atomically, otherwise an already\n'
               '       aborted request could leave a fresh endpoint transfer behind. */\n'
               '    UX_DISABLE\n'
               '    if ((endpoint -> ux_slave_endpoint_descriptor.bEndpointAddress & (UINT)~UX_ENDPOINT_DIRECTION) != 0 &&\n'
               '        transfer_request -> ux_slave_transfer_request_status != UX_TRANSFER_STATUS_PENDING)\n'
               '    {\n        UX_RESTORE\n        return;\n    }\n' + old)
        text = replace_known(text, old, new, relative)
        old = ('                           transfer_request -> ux_slave_transfer_request_requested_length);\n'
               '    }\n}\n')
        new = old.replace('    }\n}\n', '    }\n    UX_RESTORE\n}\n')
        return replace_known(text, old, new, relative)
    if relative == 'Makefile':
        anchor = 'Core/Src/app_threadx.c \\\n'
        missing = [name for name in SOURCES
                   if not re.search(r'^Core/Src/' + name + r'\.c\s*\\?$', text, re.M)]
        if missing:
            if anchor not in text:
                raise ValueError('unknown Makefile source list')
            text = text.replace(anchor, anchor + ''.join(f'Core/Src/{name}.c \\\n' for name in missing), 1)
        return text
    if relative.endswith('fx_stm32_sd_driver.c'):
        text = replace_known(text,
            '      return 0;\n    }\n  }\n\n  return 1;',
            '      return 0;\n    }\n'
            '    /* FileX calls this from thread context; do not starve peers while busy. */\n'
            '    tx_thread_sleep(1);\n  }\n\n  return 1;', relative)
        text = replace_known(text,
            '  if (is_initialized == 1)\n  {',
            '  /* Cleanup must work after card removal and transfer errors. */\n'
            '  if (is_initialized == 1 &&\n'
            '      media_ptr->fx_media_driver_request != FX_DRIVER_UNINIT &&\n'
            '      media_ptr->fx_media_driver_request != FX_DRIVER_ABORT)\n  {', relative)
        return replace_known(text,
            '      else\n      {\n        is_initialized = 0;\n      }\n#endif',
            '      /* A failed deinit cannot leave an old card logically initialized. */\n'
            '      is_initialized = 0;\n#endif', relative)
    raise ValueError(relative)


FILES = ('Core/Src/sdmmc.c', 'USBX/App/app_usbx_device.c', 'STM32U575xx_FLASH.ld',
         'Makefile',
         'Middlewares/ST/usbx/common/usbx_stm32_device_controllers/ux_dcd_stm32_transfer_request.c',
         'Middlewares/ST/filex/common/drivers/fx_stm32_sd_driver.c')

HOOKS = {
    'Core/Src/app_threadx.c': ('drms_runtime_run();',),
    'Core/Src/sdmmc.c': ('sd->Init.ClockDiv = 1;', 'RCC_CLK48CLKSOURCE_HSI48',
        'RCC_SDMMCCLKSOURCE_CLK48'),
    'Core/Inc/sdmmc.h': ('extern HAL_StatusTypeDef sd_init_status;',),
    'Core/Inc/app_threadx.h': ('#define TX_APP_STACK_SIZE (4U * 1024U)',),
    'Core/Src/stm32u5xx_it.c': ('if (drms_calibration_nmi())',),
    'USBX/App/app_usbx_device.c': ('drms_usb_init()', 'drms_cdc_start()', 'TX_DISABLE\n      drms_usb_state_change'),
    'USBX/App/ux_device_cdc_acm.c': ('drms_cdc_activate(cdc_acm_instance);', 'drms_cdc_deactivate();',
        'drms_cdc_parameter_change(cdc_acm_instance);'),
    'USBX/App/app_usbx.h': ('#define USBX_MEMORY_STACK_SIZE (32U * 1024U)',),
    'AZURE_RTOS/App/app_azure_rtos_config.h': ('#define UX_APP_MEM_POOL_SIZE (40U * 1024U)',
        '#define FX_APP_MEM_POOL_SIZE (8U * 1024U)', '#define TX_APP_MEM_POOL_SIZE (8U * 1024U)'),
    'FileX/App/app_filex.c': ('drms_log_init();', 'drms_log_poll();', 'drms_storage_prepare_shutdown();', '#define FX_APP_THREAD_STACK_SIZE (4U * 1024U)'),
    'FileX/Target/fx_stm32_sd_driver_glue.c': ('if (hsd1.Instance != SDMMC1)',
        '__HAL_RCC_SDMMC1_FORCE_RESET();', 'ret = (sd_init_status == HAL_OK) ? 0 : 1;')
}


def verify_user_code(project):
    ioc = (project / 'DE-DRMS-Code.ioc').read_text()
    if 'Mcu.CPN=STM32U575RGT6\n' not in ioc or 'ProjectManager.KeepUserCode=true\n' not in ioc:
        raise ValueError('requires STM32U575RGT6 with Keep User Code enabled; IOC is not modified')
    for relative, markers in HOOKS.items():
        text = (project / relative).read_text()
        if any(marker not in text for marker in markers):
            raise ValueError(f'{relative}: required USER code lost; restore from your saved source')
    if 'MX_SDMMC1_SD_Init();' in (project / 'Core/Src/main.c').read_text():
        raise ValueError('SD initialization returned to main; keep its Generate Function Call disabled')
    for name in SOURCES:
        if not (project / f'Core/Src/{name}.c').is_file():
            raise ValueError(f'missing application source: {name}.c')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=DEFAULT)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    changes = []
    try:
        verify_user_code(args.project)
        # Compute all edits before writing anything; unsupported templates stop here.
        for relative in FILES:
            path = args.project / relative
            version = path.stat().st_mtime_ns
            text = path.read_text()
            result = repaired(relative, text)
            if result != text:
                changes.append((path, version, result))
        if args.apply:
            for path, version, result in changes:
                if path.stat().st_mtime_ns != version:
                    raise ValueError(f'{path}: changed concurrently; retry after review')
                path.write_text(result)
    except (OSError, ValueError) as error:
        print(f'ERROR: {error}')
        return 2
    for path, _, _ in changes:
        print(f'{"RESTORED" if args.apply else "NEEDS RESTORE"}: {path}')
    if not changes:
        print('OK: known CubeMX template fixes are present')
    return 0 if args.apply or not changes else 1


if __name__ == '__main__':
    raise SystemExit(main())

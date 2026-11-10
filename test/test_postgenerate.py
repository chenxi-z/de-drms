"""Simulate CubeMX replacing non-USER regions, then check safe restoration."""
import importlib.util
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'tools/firmware_postgenerate.py'
SPEC = importlib.util.spec_from_file_location('postgenerate', SCRIPT)
PG = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PG)


class PostgenerateTest(unittest.TestCase):
    def test_sram4_workspace_section_is_restored_after_regeneration(self):
        linker = self.project / 'STM32U575xx_FLASH.ld'
        text = linker.read_text()
        text = re.sub(r'  /\* DRMS SRAM4 workspace begin \*/.*?  /\* DRMS SRAM4 workspace end \*/\n', '', text, flags=re.S)
        linker.write_text(text)
        self.assertEqual(self.run_script(apply=True).returncode, 0)
        repaired = linker.read_text()
        self.assertIn('*(.drms_sram4_workspace)', repaired)
        self.assertRegex(repaired, r'\.drms_sram4_workspace\s*\(NOLOAD\)')
        self.assertIn('>SRAM4', repaired)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project = Path(self.tmp.name)
        source = ROOT / 'firmware/DE-DRMS-Code'
        files = set(PG.FILES) | set(PG.HOOKS) | {'DE-DRMS-Code.ioc', 'Core/Src/main.c', 'drms_sources.mk'}
        files |= set(PG.application_sources(source))
        for relative in files:
            target = self.project / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / relative, target)

    def tearDown(self):
        self.tmp.cleanup()

    def run_script(self, apply=False):
        return subprocess.run(['python3', str(SCRIPT), '--project', str(self.project),
                               *(['--apply'] if apply else [])], capture_output=True, text=True)

    def edit(self, relative, change):
        p = self.project / relative
        p.write_text(change(p.read_text()))

    def simulate_regeneration(self):
        self.edit('STM32U575xx_FLASH.ld', lambda text: re.sub(r'^.*CALDATA.*\n', '', text.replace('LENGTH = 1008K', 'LENGTH = 2048K'), flags=re.M))
        def generated_makefile(text):
            text = text.replace('include drms_sources.mk\n', '')
            text = re.sub(r'ifneq \(\$\(words \$\(notdir \$\(C_SOURCES\)\)\),.*?^endif\n',
                          '', text, count=1, flags=re.M | re.S)
            return text.replace('%.c Makefile drms_sources.mk |', '%.c Makefile |').replace(
                '$(OBJECTS) Makefile drms_sources.mk\n', '$(OBJECTS) Makefile\n')
        self.edit('Makefile', generated_makefile)
        self.edit('Core/Src/sdmmc.c', lambda text: re.sub(
            r'  /\* CubeMX regeneration guard:.*?\n  }\n',
            '  if (HAL_SD_Init(&hsd1) != HAL_OK)\n  {\n    Error_Handler();\n  }\n', text, count=1, flags=re.S))
        self.edit('USBX/App/app_usbx_device.c', lambda text: text.replace(
            '  ret = ux_dcd_stm32_initialize((ULONG)USB_OTG_FS, (ULONG)&hpcd_USB_OTG_FS);\n  if (ret != UX_SUCCESS)\n    return ret;',
            '  ux_dcd_stm32_initialize((ULONG)USB_OTG_FS, (ULONG)&hpcd_USB_OTG_FS);'))
        def original_dcd(text):
            text = text.replace('ULONG                   endpoint_type;\nUX_INTERRUPT_SAVE_AREA\n',
                                'ULONG                   endpoint_type;\n')
            text = re.sub(r'    /\* The core publishes PENDING.*?        return;\n    }\n', '', text, count=1, flags=re.S)
            return text.replace('    }\n    UX_RESTORE\n}\n', '    }\n}\n', 1)
        self.edit('Middlewares/ST/usbx/common/usbx_stm32_device_controllers/ux_dcd_stm32_transfer_request.c', original_dcd)
        def original_driver(text):
            text = text.replace('    /* FileX calls this from thread context; do not starve peers while busy. */\n    tx_thread_sleep(1);\n', '')
            text = text.replace(
                '  /* Cleanup must work after card removal and transfer errors. */\n'
                '  if (is_initialized == 1 &&\n'
                '      media_ptr->fx_media_driver_request != FX_DRIVER_UNINIT &&\n'
                '      media_ptr->fx_media_driver_request != FX_DRIVER_ABORT)\n  {',
                '  if (is_initialized == 1)\n  {')
            return text.replace(
                '      /* A failed deinit cannot leave an old card logically initialized. */\n      is_initialized = 0;\n#endif',
                '      else\n      {\n        is_initialized = 0;\n      }\n#endif')
        self.edit(PG.FILES[-1], original_driver)

    def snapshot(self):
        return {relative: (self.project / relative).read_bytes() for relative in PG.FILES}

    def test_clean_tree_and_repeated_apply_are_noops(self):
        before = self.snapshot()
        self.assertEqual(self.run_script().returncode, 0)
        self.assertEqual(self.run_script(apply=True).returncode, 0)
        self.assertEqual(self.snapshot(), before)

    def test_regeneration_can_be_detected_then_restored_without_user_block_changes(self):
        self.simulate_regeneration()
        before = self.snapshot()
        self.assertEqual(self.run_script().returncode, 1)
        self.assertEqual(self.snapshot(), before)  # default is read-only
        result = self.run_script(apply=True)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(self.run_script().returncode, 0)
        pattern = r'/\* USER CODE BEGIN.*?/\* USER CODE END[^*]*\*/'
        for relative, original in before.items():
            restored = (self.project / relative).read_bytes()
            self.assertEqual(re.findall(pattern, original.decode(), flags=re.S),
                             re.findall(pattern, restored.decode(), flags=re.S))

    def test_makefile_uses_single_source_manifest(self):
        makefile = (self.project / 'Makefile').read_text()
        self.assertIn('include drms_sources.mk', makefile)
        manifest = (self.project / 'drms_sources.mk').read_text()
        self.assertIn('Core/Src/drms_application.c', manifest)
        self.assertIsNone(re.search(r'^Core/Src/drms_application\.c', makefile, re.M))

    def test_duplicate_application_source_name_is_rejected(self):
        self.edit('drms_sources.mk', lambda text: text.rstrip() + ' \\\nApp/other/drms_application.c\n')
        result = self.run_script(apply=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn('duplicate application source basenames', result.stdout)

    def test_unknown_manifest_source_is_rejected(self):
        self.edit('drms_sources.mk', lambda text: text.rstrip() + ' \\\nApp/missing.c\n')
        result = self.run_script(apply=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn('missing application source', result.stdout)

    def test_lost_user_hook_blocks_all_edits(self):
        self.simulate_regeneration()
        self.edit('Core/Src/app_threadx.c', lambda text: text.replace('drms_runtime_run();', ''))
        before = self.snapshot()
        result = self.run_script(apply=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn('USER code lost', result.stdout)
        self.assertEqual(self.snapshot(), before)

    def test_unreviewed_sd_kernel_clock_blocks_fixed_divider_assumption(self):
        self.simulate_regeneration()
        self.edit('Core/Src/sdmmc.c', lambda text: text.replace('RCC_SDMMCCLKSOURCE_CLK48', 'RCC_SDMMCCLKSOURCE_PLL1'))
        before = self.snapshot()
        self.assertEqual(self.run_script(apply=True).returncode, 2)
        self.assertEqual(self.snapshot(), before)


if __name__ == '__main__':
    unittest.main()

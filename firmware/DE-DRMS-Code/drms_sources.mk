# Application sources, maintained outside CubeMX-generated files.
C_SOURCES += \
App/interfaces/local_ui/drms_button.c \
App/platform/stm32/drms_identity.c \
App/platform/stm32/drms_entropy.c \
App/interfaces/cdc/drms_cdc_frame.c \
App/interfaces/cdc/drms_config_wire.c \
App/interfaces/cdc/drms_cdc_v2.c \
Core/Src/drms_usb.c \
Core/Src/drms_storage.c \
Core/Src/drms_msc.c \
Core/Src/drms_control.c \
Core/Src/drms_record_session.c \
Core/Src/drms_capture_time.c \
Core/Src/drms_resource_lifecycle.c \
Core/Src/drms_user_config.c \
Core/Src/drms_user_backend.c \
App/application/measurement/drms_monitor.c \
App/application/measurement/drms_filter.c \
App/application/measurement/drms_classifier.c \
App/application/measurement/drms_baseline.c \
Core/Src/drms_console.c \
Core/Src/drms_runtime.c \
Core/Src/drms_cdc.c \
Core/Src/drms_measurement.c \
Core/Src/drms_fifo.c \
Core/Src/drms_acquisition.c \
Core/Src/drms_calibration_codec.c \
Core/Src/drms_calibration_journal.c \
Core/Src/drms_calibration_flash.c \
Core/Src/drms_log_codec.c \
Core/Src/drms_logging.c \
Core/Src/drms_time_codec.c \
Core/Src/drms_aux.c \
Core/Src/drms_command.c \
Core/Src/drms_application.c \
Core/Src/drms_power.c \
Core/Src/drms_power_stm32.c

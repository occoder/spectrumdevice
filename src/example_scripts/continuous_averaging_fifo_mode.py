"""Continuous Multi-FIFO mode (SPC_REC_FIFO_MULTI) example. The function defined here is used by the tests module as an
integration test."""
import datetime
from time import monotonic
from typing import List, Optional

from spectrumdevice import MockSpectrumDigitiserCard, SpectrumDigitiserCard
from spectrumdevice.measurement import Measurement
from spectrumdevice.settings import (
    AcquisitionMode,
    CardType,
    TriggerSource,
    ExternalTriggerMode,
    TriggerSettings,
    AcquisitionSettings,
)


def continuous_averaging_multi_fifo_example(
    mock_mode: bool,
    acquisition_duration_in_seconds: float,
    num_averages: int,
    trigger_source: TriggerSource,
    device_number: int,
    ip_address: Optional[str] = None,
) -> List[Measurement]:

    if not mock_mode:
        # Connect to a networked device. To connect to a local (PCIe) device, do not provide an ip_address.
        card = SpectrumDigitiserCard(device_number=device_number, ip_address=ip_address)
    else:
        # Set up a mock device
        card = MockSpectrumDigitiserCard(
            device_number=device_number,
            card_type=CardType.TYP_M2P5966_X4,
            mock_source_frame_rate_hz=1.0,
            num_modules=2,
            num_channels_per_module=4,
        )

    # Trigger settings
    trigger_settings = TriggerSettings(
        trigger_sources=[trigger_source],
        external_trigger_mode=ExternalTriggerMode.SPC_TM_POS,
        external_trigger_level_in_mv=2000,
    )

    # Acquisition settings
    acquisition_settings = AcquisitionSettings(
        acquisition_mode=AcquisitionMode.SPC_REC_FIFO_AVERAGE,
        sample_rate_in_hz=40000000,
        acquisition_length_in_samples=400,
        pre_trigger_length_in_samples=0,
        timeout_in_ms=1000,
        enabled_channels=[0],
        vertical_ranges_in_mv=[200],
        vertical_offsets_in_percent=[0],
        timestamping_enabled=True,
        number_of_averages=num_averages,
    )

    # Apply settings
    card.configure_trigger(trigger_settings)
    card.configure_acquisition(acquisition_settings)

    # Execute acquisition
    start_time = monotonic()
    card.execute_continuous_fifo_acquisition()

    # Retrieve streamed waveform data until desired time has elapsed
    measurements_list = []
    while (monotonic() - start_time) < acquisition_duration_in_seconds:
        measurements_list.append(Measurement(waveforms=card.get_waveforms(), timestamp=card.get_timestamp()))
        if measurements_list[-1].timestamp is not None:
            print(
                f"Got measurement triggered at {measurements_list[-1].timestamp.time()} (acquisition latency of"
                f" {(datetime.datetime.now() - measurements_list[-1].timestamp).microseconds * 1e-3} ms)"
            )

    # Stop the acquisition (and streaming)
    card.stop()

    card.reset()
    card.disconnect()
    return measurements_list


if __name__ == "__main__":

    from matplotlib.pyplot import plot, show, figure, title, xlabel, ylabel, tight_layout

    measurements = continuous_averaging_multi_fifo_example(
        mock_mode=True,
        acquisition_duration_in_seconds=1.0,
        num_averages=8,
        trigger_source=TriggerSource.SPC_TMASK_EXT0,
        device_number=0,
    )

    # Plot waveforms
    for n, measurement in enumerate(measurements):
        figure()
        title(f"Measurement {n}")
        for waveform in measurement.waveforms:
            plot(waveform)
            xlabel("Time (samples)")
            ylabel("Amplitude (Volts)")
            tight_layout()

    print(f"Completed {len(measurements)} measurements each containing {len(measurements[0].waveforms)} waveforms.")
    print(f"Waveforms had the following shape: {measurements[0].waveforms[0].shape}")

    show()

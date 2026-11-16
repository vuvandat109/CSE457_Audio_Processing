"""Generate the simulated fan noise used in the enhancement tests."""
from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile

ROOT = Path(__file__).resolve().parent / "lab5_data"
SR = 16000
def save(path, samples):
    wavfile.write(path, SR, np.round(samples * 32767).astype(np.int16))


def main():
    (ROOT / "noise").mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(457)
    t = np.arange(8 * SR) / SR
    airflow = signal.sosfilt(
        signal.butter(3, [200, 4200], fs=SR, btype="bandpass", output="sos"),
        rng.standard_normal(t.size),
    )
    hum = sum(np.sin(2 * np.pi * frequency * t) / order
              for order, frequency in enumerate((95, 190, 285, 380), 1))
    fan = 0.32 * airflow + 0.21 * hum
    save(ROOT / "noise" / "fan.wav", 0.7 * fan / np.max(np.abs(fan)))


if __name__ == "__main__":
    main()

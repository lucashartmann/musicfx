import numpy as np
from .pedal import Pedal


class BossDD3Delay(Pedal):
    def __init__(self, sample_rate: int = 48000):
        super().__init__("Boss DD-3 Digital Delay")
        self.sample_rate = sample_rate
        self.time = 0.4
        self.feedback = 0.35
        self.effect_level = 0.5
        self._max_delay = int(sample_rate * 1.0)
        self._delay_buffer = np.zeros(self._max_delay, dtype=np.float32)
        self._write_index = 0
        self._last_delay_samples = -1

    def set_time(self, valor: float):
        self.time = float(np.clip(valor, 0.0, 1.0))

    def set_feedback(self, valor: float):
        self.feedback = float(np.clip(valor, 0.0, 0.92))

    def set_effect_level(self, valor: float):
        self.effect_level = float(np.clip(valor, 0.0, 1.0))

    def processar(self, audio_data):
        if not self.ativo:
            return audio_data
        if isinstance(audio_data, (bytes, bytearray)):
            samples = np.frombuffer(audio_data, dtype=np.int16).astype(
                np.float32) / 32768.0
            retornar_bytes = True
        else:
            samples = np.asarray(audio_data, dtype=np.float32)
            if samples.ndim > 1:
                samples = samples[:, 0]
            retornar_bytes = False
        out = self._aplicar_dd3(samples)
        if retornar_bytes:
            return (np.clip(out, -1.0, 1.0) * 32767).astype(np.int16).tobytes()
        return np.clip(out, -1.0, 1.0)

    def _aplicar_dd3(self, samples: np.ndarray) -> np.ndarray:
        delay_ms = 50 + self.time * 750
        delay_samples = int(self.sample_rate * delay_ms / 1000.0)
        n = len(samples)
        out = np.empty(n, dtype=np.float32)
        buf = self._delay_buffer
        idx = self._write_index
        for i in range(n):
            read_idx = (idx - delay_samples) % len(buf)
            delayed = buf[int(read_idx)]
            dry = samples[i]
            wet = delayed
            out[i] = dry + wet * self.effect_level
            fb = dry + wet * self.feedback
            buf[idx] = np.clip(fb * 0.96, -1.0, 1.0)
            idx = (idx + 1) % len(buf)
        self._write_index = idx
        return out

import numpy as np
from .pedal import Pedal, TipoPedal


class BossDD3Delay(Pedal):
    def __init__(self, sample_rate: int = 48000):
        super().__init__("Boss DD-3 Digital Delay")
        self.sample_rate = sample_rate
        self.time = 0.4
        self.feedback = 0.35
        self.effect_level = 0.5
        self.mode = "800ms"
        self.hold = False
        self._max_delay = int(sample_rate * 1.0)
        self._delay_buffer = np.zeros(self._max_delay, dtype=np.float32)
        self._write_index = 0
        self.tipo = TipoPedal.DELAY

    def set_time(self, valor: float):
        self.time = float(np.clip(valor, 0.0, 1.0))

    def set_feedback(self, valor: float):
        self.feedback = float(np.clip(valor, 0.0, 0.92))

    def set_effect_level(self, valor: float):
        self.effect_level = float(np.clip(valor, 0.0, 1.0))

    def set_mode(self, mode: str):
        allowed = {"50ms", "200ms", "800ms", "hold"}
        if mode not in allowed:
            raise ValueError(
                "mode deve ser '50ms', '200ms', '800ms' ou 'hold'")
        self.mode = mode
        self.hold = mode == "hold"

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
        out = np.clip(out, -1.0, 1.0)
        if retornar_bytes:
            return (out * 32767).astype(np.int16).tobytes()
        return out

    def _aplicar_dd3(self, samples: np.ndarray) -> np.ndarray:
        if self.mode == "50ms":
            delay_ms = 12.5 + self.time * 37.5
        elif self.mode == "200ms":
            delay_ms = 50.0 + self.time * 150.0
        elif self.mode == "hold":
            delay_ms = 800.0
        else:
            delay_ms = 200.0 + self.time * 600.0
        delay_samples = int(self.sample_rate * delay_ms / 1000.0)
        delay_samples = min(delay_samples, self._max_delay - 1)
        n = len(samples)
        out = np.empty(n, dtype=np.float32)
        buf = self._delay_buffer
        idx = self._write_index
        feedback = 0.995 if self.hold else self.feedback
        for i in range(n):
            read_idx = (idx - delay_samples) % len(buf)
            delayed = buf[int(read_idx)]
            dry = samples[i]
            out[i] = dry + delayed * self.effect_level
            fb = dry + delayed * feedback
            buf[idx] = float(np.clip(fb * 0.96, -1.0, 1.0))
            idx = (idx + 1) % len(buf)
        self._write_index = idx
        return out

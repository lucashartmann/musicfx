import numpy as np
from .pedal import Pedal


class BossCE5Chorus(Pedal):
    def __init__(self, sample_rate: int = 48000):
        super().__init__("Boss CE-5 Chorus")
        self.sample_rate = sample_rate
        self.rate = 0.35
        self.depth = 0.45
        self.mix = 0.55
        self.high_eq = 0.5
        self.low_eq = 0.5
        self._buffer = np.zeros(int(sample_rate * 0.06), dtype=np.float32)
        self._index = 0
        self._phase = 0.0

    def set_rate(self, valor: float):   self.rate = float(
        np.clip(valor, 0.0, 1.0))

    def set_depth(self, valor: float):  self.depth = float(
        np.clip(valor, 0.0, 1.0))

    def set_mix(self, valor: float):    self.mix = float(
        np.clip(valor, 0.0, 1.0))

    def processar(self, audio_data):
        if not self.ativo:
            return audio_data
        try:
            if isinstance(audio_data, (bytes, bytearray)):
                samples = np.frombuffer(audio_data, dtype=np.int16).astype(
                    np.float32) / 32768.0
                retornar_bytes = True
            else:
                samples = np.asarray(audio_data, dtype=np.float32)
                if samples.ndim > 1:
                    samples = samples[:, 0]
                retornar_bytes = False
            out = self._aplicar_ce5(samples)
            np.clip(out, -1.0, 1.0, out=out)
            if retornar_bytes:
                return (out * 32767).astype(np.int16).tobytes()
            return out
        except Exception as e:
            print(f"Erro em BossCE5Chorus.processar: {e}")
            return audio_data

    def _aplicar_ce5(self, samples: np.ndarray) -> np.ndarray:
        n = len(samples)
        out = np.empty(n, dtype=np.float32)
        buf = self._buffer
        idx = self._index
        phase = self._phase
        freq = 0.15 + self.rate * 5.5
        for i in range(n):
            lfo = np.sin(phase) * self.depth
            delay = 8 + lfo * 18
            delay_samples = int(self.sample_rate * delay / 1000.0)
            read_idx = (idx - delay_samples) % len(buf)
            delayed = buf[int(read_idx)]
            dry = samples[i]
            wet = delayed * (0.8 + self.high_eq * 0.4) * \
                (0.9 + self.low_eq * 0.3)
            out[i] = dry * (1.0 - self.mix) + wet * self.mix
            buf[idx] = dry
            idx = (idx + 1) % len(buf)
            phase += 2 * np.pi * freq / self.sample_rate
        self._index = idx
        self._phase = phase % (2 * np.pi)
        return out

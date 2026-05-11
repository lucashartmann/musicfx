import numpy as np
from .pedal import Pedal, TipoPedal


class BossRV6Reverb(Pedal):
    def __init__(self, sample_rate: int = 48000):
        super().__init__("Boss RV-6 Reverb")
        self.sample_rate = sample_rate
        self.time = 0.5
        self.level = 0.45
        self.tone = 0.6
        self.mode = "hall"
        self.decay = self.time
        self.mix = self.level
        self._comb_delays = [0.029, 0.037, 0.043, 0.051]
        self._comb_buffers = [
            np.zeros(int(sample_rate * d), dtype=np.float32)
            for d in self._comb_delays
        ]
        self._comb_idx = [0] * 4
        self._ap_delays = [0.005, 0.007, 0.011]
        self._ap_buffers = [
            np.zeros(int(sample_rate * d), dtype=np.float32)
            for d in self._ap_delays
        ]
        self._ap_idx = [0] * 3
        self._phase = 0.0
        self.tipo = TipoPedal.REVERB

    def set_decay(self, valor: float):
        self.time = float(np.clip(valor, 0.0, 1.0))
        self.decay = self.time

    def set_mix(self, valor: float):
        self.mix = float(np.clip(valor, 0.0, 1.0))
        self.level = self.mix

    def set_time(self, valor: float):
        self.set_decay(valor)

    def set_level(self, valor: float):
        self.set_mix(valor)

    def set_mode(self, mode: str):
        allowed = {"room", "hall", "plate", "spring",
                   "modulate", "shimmer", "dynamic", "delay"}
        if mode not in allowed:
            raise ValueError("mode deve ser um dos modos do RV-6")
        self.mode = mode

    def set_tone(self, valor: float):
        self.tone = float(np.clip(valor, 0.0, 1.0))

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
            out = self._aplicar_rv6(samples)
            np.clip(out, -1.0, 1.0, out=out)
            if retornar_bytes:
                return (out * 32767).astype(np.int16).tobytes()
            return out
        except Exception as e:
            print(f"Erro em BossRV6Reverb.processar: {e}")
            return audio_data

    def _aplicar_rv6(self, samples: np.ndarray) -> np.ndarray:
        n = len(samples)
        out = np.empty(n, dtype=np.float32)
        g = 0.60 + self.time * 0.30
        mod_depth = 0.0008 if self.mode == "modulate" else 0.0003
        for i in range(n):
            x = samples[i]
            rev = 0.0
            for j in range(4):
                idx = self._comb_idx[j]
                delayed = self._comb_buffers[j][idx]
                rev += delayed
                fb = x * 0.25 + delayed * g
                self._comb_buffers[j][idx] = float(np.clip(fb, -1.0, 1.0))
                self._comb_idx[j] = (idx + 1) % len(self._comb_buffers[j])
            rev *= 0.25
            for j in range(3):
                idx = self._ap_idx[j]
                mod = np.sin(self._phase * (j + 1)) * \
                    mod_depth * self.sample_rate
                read = (idx - int(mod)) % len(self._ap_buffers[j])
                delayed = self._ap_buffers[j][int(read)]
                self._ap_buffers[j][idx] = float(
                    np.clip(rev * 0.5 + delayed * (-0.5), -1.0, 1.0))
                rev = delayed + rev * 0.5
                self._ap_idx[j] = (idx + 1) % len(self._ap_buffers[j])
            rev *= (0.5 + self.tone * 0.5)
            if self.mode == "shimmer":
                rev += rev * 0.25 * np.sin(self._phase * 6)
            out[i] = x * (1.0 - self.level) + rev * self.level
            self._phase += 2 * np.pi * 0.8 / self.sample_rate
        return out

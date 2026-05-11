import numpy as np
from .pedal import Pedal, TipoPedal


class DunlopCryBabyGCB95(Pedal):

    _FC_MIN = 450.0
    _FC_MAX = 1600.0
    _Q_BASE = 4.5
    _GAIN_DB = 12.0

    def __init__(self, sample_rate: int = 48000):
        super().__init__("Dunlop Cry Baby GCB-95")
        self.sample_rate = sample_rate
        self.tipo = TipoPedal.WAH
        self.wah = 0.5
        self._z1 = 0.0
        self._z2 = 0.0
        self._last_wah = -1.0
        self._b0 = 0.0
        self._b1 = 0.0
        self._b2 = 0.0
        self._a1 = 0.0
        self._a2 = 0.0
        self._hp_z = 0.0
        self._hp_alpha = self._calc_hp_alpha()

    def set_wah(self, valor: float):
        self.wah = float(np.clip(valor, 0.0, 1.0))

    def get_wah(self):
        return self.wah

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
            out = self._aplicar_gcb95(samples)
            np.clip(out, -1.0, 1.0, out=out)
            if retornar_bytes:
                return (out * 32767).astype(np.int16).tobytes()
            return out
        except Exception as e:
            print(f"Erro em DunlopCryBabyGCB95.processar: {e}")
            return audio_data

    def _aplicar_gcb95(self, samples: np.ndarray) -> np.ndarray:
        n = len(samples)
        out = np.empty(n, dtype=np.float32)
        if abs(self.wah - self._last_wah) > 0.001:
            self._calcular_coeficientes()
            self._last_wah = self.wah
        b0 = self._b0
        b1 = self._b1
        b2 = self._b2
        a1 = self._a1
        a2 = self._a2
        z1 = self._z1
        z2 = self._z2
        ganho_pos = 0.5 + 0.5 * np.sin(np.pi * self.wah)
        makeup = 1.0 + ganho_pos * (10 ** (self._GAIN_DB / 20.0) - 1.0) * 0.4
        alpha = self._hp_alpha
        hp_z = self._hp_z
        for i in range(n):
            x = samples[i]
            hp_out = x - hp_z
            hp_z = hp_z + alpha * (x - hp_z)
            y = b0 * hp_out + z1
            z1 = b1 * hp_out - a1 * y + z2
            z2 = b2 * hp_out - a2 * y
            out[i] = y * makeup
        self._z1 = z1
        self._z2 = z2
        self._hp_z = hp_z
        return out

    def _calcular_coeficientes(self):
        fc = self._FC_MIN * (self._FC_MAX / self._FC_MIN) ** self.wah
        L1 = 0.5
        R7 = 33e3
        Q_lc = R7 / (2.0 * np.pi * fc * L1)
        Q = np.clip(Q_lc / 3.0, 1.5, 8.0)
        w0 = 2.0 * np.pi * fc
        wd = 2.0 * self.sample_rate * np.tan(w0 / (2.0 * self.sample_rate))
        K = wd / (2.0 * self.sample_rate)
        norm = 1.0 + K / Q + K * K
        self._b0 = float(K / Q / norm)
        self._b1 = 0.0
        self._b2 = float(-K / Q / norm)
        self._a1 = float(2.0 * (K * K - 1.0) / norm)
        self._a2 = float((1.0 - K / Q + K * K) / norm)

    def _calc_hp_alpha(self) -> float:
        fc = 1.0 / (2.0 * np.pi * 0.01e-6 * 990e3)
        wc = 2.0 * np.pi * fc / self.sample_rate
        return 1.0 - np.exp(-wc)

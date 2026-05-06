import numpy as np
from .pedal import Pedal


class KlonCentaur(Pedal):

    def __init__(self, sample_rate: int = 48000):
        super().__init__("Klon Centaur")
        self.sample_rate = sample_rate
        self.gain = 0.5
        self.tom = 0.5
        self.volume = 0.7
        self.intensidade = self.gain
        self._Vref = 1.0
        self._buf_z = np.zeros(1)
        self._mh_z = np.zeros(2)
        self._ff1_z = np.zeros(1)
        self._sum_z = np.zeros(1)
        self._tone_z = np.zeros(2)
        self._last_tom = -1
        self._tone_b = None
        self._tone_a = None

    def set_intensidade(self, valor: float):
        self.intensidade = float(np.clip(valor, 0.0, 1.0))
        self.gain = self.intensidade

    def set_tom(self, valor: float):
        self.tom = float(np.clip(valor, 0.0, 1.0))

    def set_volume(self, valor: float):
        self.volume = float(np.clip(valor, 0.0, 1.0))

    @staticmethod
    def _lfilter(b, a, x, z):
        from scipy.signal import lfilter, lfilter_zi
        y, z_new = lfilter(b, a, x, zi=z)
        return y.astype(np.float32), z_new

    def _first_order_hp_coeffs(self, fc: float):
        wc = 2.0 * np.pi * fc
        K = wc / (2.0 * self.sample_rate)
        b0 = 1.0 / (1.0 + K)
        a1 = (K - 1.0) / (1.0 + K)
        b = np.array([b0, -b0], dtype=np.float64)
        a = np.array([1.0, a1], dtype=np.float64)
        return b, a

    def _first_order_lp_coeffs(self, fc: float):
        wc = 2.0 * np.pi * fc
        K = wc / (2.0 * self.sample_rate)
        b0 = K / (1.0 + K)
        a1 = (K - 1.0) / (1.0 + K)
        b = np.array([b0, b0], dtype=np.float64)
        a = np.array([1.0, a1], dtype=np.float64)
        return b, a

    def _peaking_biquad_coeffs(self, fc: float, Q: float, gain_db: float):
        A = 10.0 ** (gain_db / 40.0)
        w0 = 2.0 * np.pi * fc / self.sample_rate
        cos_w0 = np.cos(w0)
        sin_w0 = np.sin(w0)
        alpha = sin_w0 / (2.0 * Q)
        b0 = 1.0 + alpha * A
        b1 = -2.0 * cos_w0
        b2 = 1.0 - alpha * A
        a0 = 1.0 + alpha / A
        a1 = -2.0 * cos_w0
        a2 = 1.0 - alpha / A
        b = np.array([b0/a0, b1/a0, b2/a0], dtype=np.float64)
        a = np.array([1.0,   a1/a0, a2/a0], dtype=np.float64)
        return b, a

    def _highshelf_biquad_coeffs(self, fc: float, gain_db: float, S: float = 1.0):
        A = 10.0 ** (gain_db / 40.0)
        w0 = 2.0 * np.pi * fc / self.sample_rate
        cos_w0 = np.cos(w0)
        sin_w0 = np.sin(w0)
        alpha = sin_w0 / 2.0 * np.sqrt((A + 1.0/A) * (1.0/S - 1.0) + 2.0)
        b0 = A * ((A+1) + (A-1)*cos_w0 + 2.0*np.sqrt(A)*alpha)
        b1 = -2.0 * A * ((A-1) + (A+1)*cos_w0)
        b2 = A * ((A+1) + (A-1)*cos_w0 - 2.0*np.sqrt(A)*alpha)
        a0 = ((A+1) - (A-1)*cos_w0 + 2.0*np.sqrt(A)*alpha)
        a1 = 2.0 * ((A-1) - (A+1)*cos_w0)
        a2 = ((A+1) - (A-1)*cos_w0 - 2.0*np.sqrt(A)*alpha)
        b = np.array([b0/a0, b1/a0, b2/a0], dtype=np.float64)
        a = np.array([1.0,   a1/a0, a2/a0], dtype=np.float64)
        return b, a

    def processar(self, audio_data):
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
            s = self._input_buffer(samples)
            if not self.ativo:
                out = s
            else:
                distorted = self._gain_stage(s)
                ff1 = self._feedforward_network1(s)
                ff2 = self._feedforward_network2(s)
                summed = self._summing_stage(distorted, ff1, ff2)
                toned = self._tone_control(summed)
                out = toned * self.volume
            np.clip(out, -1.0, 1.0, out=out)
            if retornar_bytes:
                return (out * 32767).astype(np.int16).tobytes()
            return out
        except Exception as e:
            print(f"Erro em KlonCentaur.processar: {e}")
            return audio_data

    def _input_buffer(self, samples: np.ndarray) -> np.ndarray:
        fc = 1.0 / (2.0 * np.pi * 0.1e-6 * 1e6)
        b, a = self._first_order_hp_coeffs(fc)
        out, self._buf_z = self._lfilter(
            b, a, samples.astype(np.float64), self._buf_z)
        return out

    def _gain_stage(self, samples: np.ndarray) -> np.ndarray:
        drive = 2.0 + self.gain * 98.0
        peak_db = -3.0 + self.gain * 23.0
        b, a = self._peaking_biquad_coeffs(fc=950.0, Q=0.5, gain_db=peak_db)
        shaped, self._mh_z = self._lfilter(
            b, a, samples.astype(np.float64), self._mh_z)
        amplified = shaped * drive
        Vf = 0.35
        clipped = (Vf / self._Vref) * np.tanh(amplified * self._Vref / Vf)
        return clipped.astype(np.float32)

    def _feedforward_network1(self, samples: np.ndarray) -> np.ndarray:
        fc = 1.0 / (2.0 * np.pi * 1500.0 * 390e-9)
        b, a = self._first_order_lp_coeffs(fc)
        out, self._ff1_z = self._lfilter(
            b, a, samples.astype(np.float64), self._ff1_z)
        return out.astype(np.float32) * 0.4

    def _feedforward_network2(self, samples: np.ndarray) -> np.ndarray:
        peso = (1.0 - self.gain) * 0.55
        return samples * peso

    def _summing_stage(self,
                       distorted: np.ndarray,
                       ff1: np.ndarray,
                       ff2: np.ndarray) -> np.ndarray:
        mixed = distorted + ff1 + ff2
        fc = 1.0 / (2.0 * np.pi * 392e3 * 820e-12)
        b, a = self._first_order_lp_coeffs(fc)
        filtered, self._sum_z = self._lfilter(
            b, a, mixed.astype(np.float64), self._sum_z)
        Av = - (392e3 / 47e3)
        amplified = filtered * Av
        rail_pos = 1.8
        rail_neg = -0.96
        center = (rail_pos + rail_neg) / 2.0
        span = (rail_pos - rail_neg) / 2.0
        x_norm = (amplified - center) / span
        clipped = np.tanh(x_norm * 1.1) * span + center
        return clipped.astype(np.float32)

    def _tone_control(self, samples: np.ndarray) -> np.ndarray:
        fc = 408.0
        if self.tom <= 0.5:
            gain_db = -8.0 + (self.tom * 16.0)
        else:
            gain_db = (self.tom - 0.5) * 36.48
        if abs(self.tom - self._last_tom) > 0.005 or self._tone_b is None:
            self._tone_b, self._tone_a = self._highshelf_biquad_coeffs(
                fc=fc, gain_db=gain_db, S=1.0)
            self._last_tom = self.tom
        out, self._tone_z = self._lfilter(
            self._tone_b, self._tone_a, samples.astype(np.float64), self._tone_z)
        return (-out).astype(np.float32)

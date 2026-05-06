import numpy as np
from abc import ABC, abstractmethod


class Amplificador(ABC):

    def __init__(self, nome: str, sample_rate: int = 48000):
        self.nome = nome
        self.sample_rate = sample_rate
        self.ativo = True
        self.volume = 0.5
        self.bass = 0.5
        self.mid = 0.5
        self.treble = 0.5
        self.presence = 0.5
        self.gain = 0.5

    def set_gain(self, valor: float):
        self.gain = float(np.clip(valor, 0.0, 1.0))

    def set_volume(self, valor: float):
        self.volume = float(np.clip(valor, 0.0, 1.0))

    def set_bass(self, valor: float):
        self.bass = float(np.clip(valor, 0.0, 1.0))

    def set_mid(self, valor: float):
        self.mid = float(np.clip(valor, 0.0, 1.0))

    def set_treble(self, valor: float):
        self.treble = float(np.clip(valor, 0.0, 1.0))

    def set_presence(self, valor: float):
        self.presence = float(np.clip(valor, 0.0, 1.0))

    def ligar(self):
        self.ativo = True

    def desligar(self):
        self.ativo = False

    def __repr__(self):
        return (
            f"<{self.__class__.__name__} nome='{self.nome}' "
            f"ativo={self.ativo} sr={self.sample_rate}Hz>"
        )

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
            if not self.ativo:
                out = samples
            else:
                out = self._pipeline(samples)
            np.clip(out, -1.0, 1.0, out=out)
            if retornar_bytes:
                return (out * 32767).astype(np.int16).tobytes()
            return out
        except Exception as e:
            print(f"Erro em {self.__class__.__name__}.processar: {e}")
            return audio_data

    def _pipeline(self, samples: np.ndarray) -> np.ndarray:
        s = self._preamp(samples)
        s = self._tonestack(s)
        s = self._phase_inverter(s)
        s = self._power_amp(s)
        return s * self.volume

    @abstractmethod
    def _preamp(self, samples: np.ndarray) -> np.ndarray:
        pass

    @abstractmethod
    def _tonestack(self, samples: np.ndarray) -> np.ndarray:
        pass

    @abstractmethod
    def _phase_inverter(self, samples: np.ndarray) -> np.ndarray:
        pass

    @abstractmethod
    def _power_amp(self, samples: np.ndarray) -> np.ndarray:
        pass

    @staticmethod
    def _lfilter(b, a, x: np.ndarray, z: np.ndarray):
        from scipy.signal import lfilter
        y, z_new = lfilter(b, a, x.astype(np.float64), zi=z)
        return y.astype(np.float32), z_new

    @staticmethod
    def _bilinear_lp(fc: float, fs: float):
        wc = 2.0 * np.pi * fc
        K = wc / (2.0 * fs)
        b0 = K / (1.0 + K)
        a1 = (K - 1.0) / (1.0 + K)
        return np.array([b0, b0]), np.array([1.0, a1])

    @staticmethod
    def _bilinear_hp(fc: float, fs: float):
        wc = 2.0 * np.pi * fc
        K = wc / (2.0 * fs)
        b0 = 1.0 / (1.0 + K)
        a1 = (K - 1.0) / (1.0 + K)
        return np.array([b0, -b0]), np.array([1.0, a1])

    @staticmethod
    def _peaking_biquad(fc: float, Q: float, gain_db: float, fs: float):
        A = 10.0 ** (gain_db / 40.0)
        w0 = 2.0 * np.pi * fc / fs
        sin_w0 = np.sin(w0)
        cos_w0 = np.cos(w0)
        alpha = sin_w0 / (2.0 * Q)
        b0 = 1.0 + alpha * A
        b1 = -2.0 * cos_w0
        b2 = 1.0 - alpha * A
        a0 = 1.0 + alpha / A
        a1 = -2.0 * cos_w0
        a2 = 1.0 - alpha / A
        return np.array([b0/a0, b1/a0, b2/a0]), np.array([1.0, a1/a0, a2/a0])

    @staticmethod
    def _highshelf_biquad(fc: float, gain_db: float, S: float, fs: float):
        A = 10.0 ** (gain_db / 40.0)
        w0 = 2.0 * np.pi * fc / fs
        sin_w0 = np.sin(w0)
        cos_w0 = np.cos(w0)
        alpha = sin_w0 / 2.0 * np.sqrt((A + 1.0/A) * (1.0/S - 1.0) + 2.0)
        b0 = A * ((A+1) + (A-1)*cos_w0 + 2.0*np.sqrt(A)*alpha)
        b1 = -2.0 * A * ((A-1) + (A+1)*cos_w0)
        b2 = A * ((A+1) + (A-1)*cos_w0 - 2.0*np.sqrt(A)*alpha)
        a0 = ((A+1) - (A-1)*cos_w0 + 2.0*np.sqrt(A)*alpha)
        a1 = 2.0 * ((A-1) - (A+1)*cos_w0)
        a2 = ((A+1) - (A-1)*cos_w0 - 2.0*np.sqrt(A)*alpha)
        return np.array([b0/a0, b1/a0, b2/a0]), np.array([1.0, a1/a0, a2/a0])

    @staticmethod
    def _triode_ecc83(x: np.ndarray, gain: float = 60.0,
                      vp_norm: float = 1.0, knee: float = 0.7) -> np.ndarray:
        amplified = x * gain
        offset = 0.015 * vp_norm
        x_shifted = amplified + offset
        saturated = vp_norm * np.tanh(x_shifted / (vp_norm * knee))
        saturated -= np.tanh(offset / (vp_norm * knee)) * vp_norm
        return saturated.astype(np.float32)

    @staticmethod
    def _el34_power(x: np.ndarray, bias: float = 0.45,
                    vp_norm: float = 1.0) -> np.ndarray:
        push = np.clip(x + bias, 0.0, None)
        pull = np.clip(-(x - bias), 0.0, None)

        push_sat = vp_norm * np.tanh(push / (vp_norm * 0.8))
        pull_sat = vp_norm * np.tanh(pull / (vp_norm * 0.8))

        combined = push_sat - pull_sat

        combined = np.where(
            combined > 0,
            combined * (1.0 - 0.04 * combined),
            combined
        )

        return combined.astype(np.float32)

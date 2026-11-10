"""Blocos de DSP compartilhados pelos pedais.

Convenção de nível: 1.0 digital ~= 1 V de pico no circuito. Isso permite usar
diretamente os valores de componentes dos esquemas (tensão de joelho de diodo,
trilhos de alimentação etc.).
"""
import numpy as np
from scipy.signal import bilinear, firwin, lfilter, lfilter_zi

VT = 0.02585  # tensão térmica (V) a ~27 °C

# Parâmetros SPICE aproximados dos diodos usados nos pedais
DIODO_1N4148 = {"Is": 2.52e-9, "n": 1.752}   # silício (DS-1)
DIODO_1N34A = {"Is": 2.0e-7, "n": 1.3}       # germânio (Klon Centaur)


def para_float(audio_data):
    """Converte bytes int16 ou array em float32 mono. Retorna (amostras, era_bytes)."""
    if isinstance(audio_data, (bytes, bytearray)):
        return np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0, True
    samples = np.asarray(audio_data, dtype=np.float32)
    if samples.ndim > 1:
        samples = samples[:, 0]
    return samples, False


def float_para_bytes(samples: np.ndarray) -> bytes:
    return (np.clip(samples, -1.0, 1.0) * 32767).astype(np.int16).tobytes()


def analogico_para_digital(b_s, a_s, fs: float, f_warp: float | None = None):
    """Transformada bilinear de H(s) = B(s)/A(s) (coeficientes em potências
    decrescentes de s). Com f_warp, faz pre-warping nessa frequência."""
    b_s = np.atleast_1d(np.asarray(b_s, dtype=np.float64))
    a_s = np.atleast_1d(np.asarray(a_s, dtype=np.float64))
    if f_warp is not None and f_warp > 0:
        w = 2.0 * np.pi * f_warp
        fs_eff = w / (2.0 * np.tan(w / (2.0 * fs)))
    else:
        fs_eff = fs
    return bilinear(b_s, a_s, fs=fs_eff)


def rc_passa_baixa(fc: float, fs: float):
    return analogico_para_digital([1.0], [1.0 / (2 * np.pi * fc), 1.0], fs, fc)


def rc_passa_altas(fc: float, fs: float):
    tau = 1.0 / (2 * np.pi * fc)
    return analogico_para_digital([tau, 0.0], [tau, 1.0], fs, fc)


def shelf_agudos(fc: float, ganho_db: float, fs: float, S: float = 1.0):
    """High-shelf RBJ (Audio EQ Cookbook)."""
    A = 10.0 ** (ganho_db / 40.0)
    w0 = 2.0 * np.pi * fc / fs
    c, s = np.cos(w0), np.sin(w0)
    alpha = s / 2.0 * np.sqrt((A + 1.0 / A) * (1.0 / S - 1.0) + 2.0)
    sa = 2.0 * np.sqrt(A) * alpha
    b = [A * ((A + 1) + (A - 1) * c + sa), -2 * A * ((A - 1) + (A + 1) * c), A * ((A + 1) + (A - 1) * c - sa)]
    a = [(A + 1) - (A - 1) * c + sa, 2 * ((A - 1) - (A + 1) * c), (A + 1) - (A - 1) * c - sa]
    return np.array(b) / a[0], np.array(a) / a[0]


def shelf_graves(fc: float, ganho_db: float, fs: float, S: float = 1.0):
    """Low-shelf RBJ (Audio EQ Cookbook)."""
    A = 10.0 ** (ganho_db / 40.0)
    w0 = 2.0 * np.pi * fc / fs
    c, s = np.cos(w0), np.sin(w0)
    alpha = s / 2.0 * np.sqrt((A + 1.0 / A) * (1.0 / S - 1.0) + 2.0)
    sa = 2.0 * np.sqrt(A) * alpha
    b = [A * ((A + 1) - (A - 1) * c + sa), 2 * A * ((A - 1) - (A + 1) * c), A * ((A + 1) - (A - 1) * c - sa)]
    a = [(A + 1) + (A - 1) * c + sa, -2 * ((A - 1) + (A + 1) * c), (A + 1) + (A - 1) * c - sa]
    return np.array(b) / a[0], np.array(a) / a[0]


class Filtro:
    """Filtro IIR com estado persistente entre blocos.

    Ao trocar coeficientes de mesma ordem o estado é mantido, evitando cliques
    quando um knob é girado."""

    def __init__(self, b=None, a=None):
        self.b = None
        self.a = None
        self.z = None
        if b is not None:
            self.set_coef(b, a)

    def set_coef(self, b, a):
        b = np.asarray(b, dtype=np.float64)
        a = np.asarray(a, dtype=np.float64)
        ordem = max(len(a), len(b)) - 1
        if self.z is None or len(self.z) != ordem:
            self.z = np.zeros(ordem)
        self.b, self.a = b, a

    def reset(self):
        if self.z is not None:
            self.z[:] = 0.0

    def __call__(self, x: np.ndarray) -> np.ndarray:
        if self.b is None or len(self.z) == 0:
            return x * (self.b[0] / self.a[0] if self.b is not None else 1.0)
        y, self.z = lfilter(self.b, self.a, x, zi=self.z)
        return y


class Sobreamostragem:
    """Sobreamostragem com estado (zero-stuffing + FIR passa-baixa) para que o
    clipping não gere aliasing audível."""

    def __init__(self, fator: int = 4, taps: int = 48):
        self.fator = fator
        self.h = firwin(taps, 0.9 / fator)
        self._z_up = np.zeros(taps - 1)
        self._z_down = np.zeros(taps - 1)

    def subir(self, x: np.ndarray) -> np.ndarray:
        L = self.fator
        up = np.zeros(len(x) * L)
        up[::L] = x * L
        y, self._z_up = lfilter(self.h, 1.0, up, zi=self._z_up)
        return y

    def descer(self, x: np.ndarray) -> np.ndarray:
        y, self._z_down = lfilter(self.h, 1.0, x, zi=self._z_down)
        return y[:: self.fator]


def clipper_diodos(x: np.ndarray, R: float, diodo: dict, diodo_neg: dict | None = None,
                   iteracoes: int = 6) -> np.ndarray:
    """Clipper com par de diodos anti-paralelos para o terra alimentado por um
    resistor série R (solução estática da equação de Shockley).

        x = y + R * Is * (exp(y / nVt) - 1)    (y > 0)

    Resolve com Newton partindo de um limite superior da raiz (f é convexa),
    o que garante convergência monotônica. Se `diodo_neg` for dado, usa outro
    diodo no semiciclo negativo (clipping assimétrico)."""
    x = np.asarray(x, dtype=np.float64)
    ax = np.abs(x)
    neg = diodo_neg if diodo_neg is not None else diodo
    Is = np.where(x >= 0, diodo["Is"], neg["Is"])
    nvt = np.where(x >= 0, diodo["n"], neg["n"]) * VT
    k = R * Is
    y = np.minimum(ax, nvt * np.log1p(ax / k))
    for _ in range(iteracoes):
        e = np.exp(np.minimum(y / nvt, 80.0))
        f = y + k * (e - 1.0) - ax
        df = 1.0 + k / nvt * e
        y = np.maximum(y - f / df, 0.0)
    return np.sign(x) * y


def saturacao_trilho(x: np.ndarray, trilho: float) -> np.ndarray:
    """Saturação suave de um amp-op/transistor ao se aproximar do trilho."""
    return trilho * np.tanh(x / trilho)


def coef_tempo(ms: float, fs: float) -> float:
    """Coeficiente de um seguidor de envelope de 1ª ordem com constante de tempo `ms`."""
    return 1.0 - np.exp(-1.0 / max(fs * ms / 1000.0, 1e-9))


def ler_fracionario(buf: np.ndarray, pos: np.ndarray) -> np.ndarray:
    """Leitura com interpolação linear em buffer circular."""
    n = len(buf)
    i0 = np.floor(pos).astype(np.int64)
    frac = pos - i0
    i0 %= n
    i1 = (i0 + 1) % n
    return buf[i0] * (1.0 - frac) + buf[i1] * frac


def escrever_circular(buf: np.ndarray, idx: int, dados: np.ndarray) -> int:
    n = len(buf)
    m = len(dados)
    fim = idx + m
    if fim <= n:
        buf[idx:fim] = dados
    else:
        k = n - idx
        buf[idx:] = dados[:k]
        buf[: m - k] = dados[k:]
    return fim % n

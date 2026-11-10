import numpy as np
from scipy.signal import butter

from .pedal import Pedal, TipoPedal
from .dsp import (Filtro, escrever_circular, ler_fracionario, rc_passa_altas,
                  shelf_agudos, shelf_graves)


class BossCE5Chorus(Pedal):
    """BOSS CE-5 Chorus Ensemble.

    Mesma arquitetura dos chorus BBD da BOSS (ver a análise do CE-2 em
    https://electrosmash.mas-effects.com/boss-ce-2-analysis):

    - Caminho de efeito: passa-altas ~48 Hz -> filtro anti-aliasing passa-baixa
      de 3ª ordem (~6,6 kHz) -> BBD de 1024 estágios (MN3207) com o clock
      modulado por um LFO TRIANGULAR -> filtro de reconstrução de 3ª ordem
      (~6,6 kHz) -> controles FILTER (HIGH / LOW) -> E.LEVEL.
    - O sinal seco passa direto e é somado ao efeito (no máximo 50/50).
    - RATE: ~0,1 Hz a ~6 Hz. DEPTH: excursão do delay em torno de ~7 ms.

    A pré/de-ênfase em volta do BBD se cancela num modelo linear e foi omitida.
    """

    _DELAY_BASE_MS = 7.0
    _EXCURSAO_MAX_MS = 5.0
    _RATE_MIN = 0.1
    _RATE_MAX = 6.0

    def __init__(self, sample_rate: int = 44100):
        super().__init__("Boss CE-5 Chorus", sample_rate)
        self.rate = 0.35
        self.depth = 0.45
        self.level = 0.55
        self.high = 0.5
        self.low = 0.5
        self.mix = self.level
        self.high_cut = self.high
        self.low_cut = self.low
        self.intensidade = self.level
        self.tipo = TipoPedal.CHORUS

        self._buffer = np.zeros(int(sample_rate * 0.05) + 1024)
        self._idx = 0
        self._fase = 0.0

        self._hp = Filtro(*rc_passa_altas(48.0, sample_rate))
        self._aa = Filtro(*butter(3, 6600.0, fs=sample_rate))
        self._rec = Filtro(*butter(3, 6600.0, fs=sample_rate))
        self._f_low = Filtro()
        self._f_high = Filtro()
        self._filtros_calc = None

    def set_intensidade(self, valor: float):
        self.set_level(valor)

    def set_rate(self, valor: float):
        self.rate = float(np.clip(valor, 0.0, 1.0))

    def set_depth(self, valor: float):
        self.depth = float(np.clip(valor, 0.0, 1.0))

    def set_mix(self, valor: float):
        self.mix = float(np.clip(valor, 0.0, 1.0))
        self.level = self.mix
        self.intensidade = self.mix

    def set_level(self, valor: float):
        self.set_mix(valor)

    def set_high(self, valor: float):
        self.high = float(np.clip(valor, 0.0, 1.0))
        self.high_cut = self.high

    def set_low(self, valor: float):
        self.low = float(np.clip(valor, 0.0, 1.0))
        self.low_cut = self.low

    def set_high_cut(self, valor: float):
        self.set_high(valor)

    def set_low_cut(self, valor: float):
        self.set_low(valor)

    def _atualizar_filtros(self):
        chave = (self.high, self.low)
        if chave == self._filtros_calc:
            return
        # Centro = plano; extremos = +-10 dB no sinal de efeito.
        self._f_low.set_coef(*shelf_graves(200.0, (self.low - 0.5) * 20.0, self.sample_rate))
        self._f_high.set_coef(*shelf_agudos(2500.0, (self.high - 0.5) * 20.0, self.sample_rate))
        self._filtros_calc = chave

    def _processar(self, samples: np.ndarray) -> np.ndarray:
        self._atualizar_filtros()
        n = len(samples)
        fs = self.sample_rate

        entrada_bbd = self._aa(self._hp(samples))
        inicio = self._idx
        self._idx = escrever_circular(self._buffer, inicio, entrada_bbd)

        freq = self._RATE_MIN * (self._RATE_MAX / self._RATE_MIN) ** self.rate
        fases = self._fase + np.arange(1, n + 1) * (freq / fs)
        self._fase = float(fases[-1] % 1.0)
        triangulo = 4.0 * np.abs((fases % 1.0) - 0.5) - 1.0  # -1..1

        delay_ms = self._DELAY_BASE_MS + triangulo * self._EXCURSAO_MAX_MS * self.depth
        delay = delay_ms * fs / 1000.0
        pos = inicio + np.arange(n) - delay
        molhado = ler_fracionario(self._buffer, pos)

        molhado = self._f_high(self._f_low(self._rec(molhado)))
        return samples + molhado * self.level

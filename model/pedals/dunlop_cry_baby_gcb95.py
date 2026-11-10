import numpy as np

from .pedal import Pedal, TipoPedal
from .dsp import Filtro, rc_passa_altas


class DunlopCryBabyGCB95(Pedal):
    """Dunlop Cry Baby GCB-95. Valores conforme a análise da ElectroSmash
    (https://electrosmash.mas-effects.com/crybaby-gcb-95.html):

    - Buffer de entrada Q0 (MPSA13, seguidor de emissor, ganho unitário).
    - Acoplamento C1 0,01u / R1 68k -> passa-altas de ~234 Hz na entrada do
      filtro ativo.
    - Filtro ativo Q1 (MPSA18) com ressonador LC: L1 500 mH, C2 0,01u, pot
      VR1 100k. Passa-faixa ressonante que varre de ~450 Hz (calcanhar) a
      ~1,6 kHz (ponta), ~750 Hz no meio, com até ~18 dB no pico.
    - Q definido por R7 (33k) em paralelo com L1: Q ~ R7 / (2*pi*f*L1),
      reduzido pela carga do circuito (menor Q nas frequências altas).
    - Saída Q2 (seguidor de emissor) tirada antes do VR1: o volume não muda
      com a posição do pedal.

    O filtro é um SVF de topologia TPT (Zavalishin), estável mesmo com a
    frequência mudando a cada amostra, sem "zipper noise" ao varrer o pedal.
    """

    _FC_MIN = 450.0
    _FC_MAX = 1600.0
    _L1 = 0.5
    _R7 = 33e3
    _FATOR_CARGA = 3.0  # carga do circuito sobre o Q ideal do tanque LC
    _GANHO_PICO_DB = 18.0

    def __init__(self, sample_rate: int = 44100):
        super().__init__("Dunlop Cry Baby GCB-95", sample_rate)
        self.tipo = TipoPedal.WAH
        self.wah = 0.5
        self.intensidade = self.wah
        self._hp = Filtro(*rc_passa_altas(1.0 / (2 * np.pi * 68e3 * 0.01e-6), sample_rate))
        self._ic1 = 0.0
        self._ic2 = 0.0
        self._fc_atual = self._frequencia(self.wah)

    def set_wah(self, valor: float):
        self.wah = float(np.clip(valor, 0.0, 1.0))
        self.intensidade = self.wah

    def set_intensidade(self, valor: float):
        self.set_wah(valor)

    def get_wah(self):
        return self.wah

    def _frequencia(self, posicao: float) -> float:
        # Pot de 100k com curva de áudio: ~750 Hz com o pedal no meio do curso.
        return self._FC_MIN * (self._FC_MAX / self._FC_MIN) ** (posicao ** 1.2)

    def _q(self, fc):
        q = self._R7 / (2.0 * np.pi * fc * self._L1) / self._FATOR_CARGA
        return np.clip(q, 1.5, 8.0)

    def _processar(self, samples: np.ndarray) -> np.ndarray:
        n = len(samples)
        x = self._hp(samples)

        # Rampa logarítmica da frequência ao longo do bloco (pedal "suave").
        fc_alvo = self._frequencia(self.wah)
        fc = np.geomspace(self._fc_atual, fc_alvo, n + 1)[1:]
        self._fc_atual = fc_alvo
        q = self._q(fc)

        g = np.tan(np.pi * np.minimum(fc, 0.45 * self.sample_rate) / self.sample_rate)
        k = 1.0 / q
        a1 = 1.0 / (1.0 + g * (g + k))
        a2 = g * a1
        a3 = g * a2

        ic1, ic2 = self._ic1, self._ic2
        bp = np.empty(n)
        xs = x.tolist()
        a1l, a2l, a3l, kl = a1.tolist(), a2.tolist(), a3.tolist(), k.tolist()
        for i in range(n):
            v3 = xs[i] - ic2
            v1 = a1l[i] * ic1 + a2l[i] * v3
            v2 = ic2 + a2l[i] * ic1 + a3l[i] * v3
            ic1 = 2.0 * v1 - ic1
            ic2 = 2.0 * v2 - ic2
            bp[i] = kl[i] * v1  # passa-faixa com ganho unitário no pico
        self._ic1, self._ic2 = ic1, ic2

        return bp * 10.0 ** (self._GANHO_PICO_DB / 20.0)

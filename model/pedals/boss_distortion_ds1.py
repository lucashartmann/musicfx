import numpy as np

from .pedal import Pedal, TipoPedal
from .dsp import (DIODO_1N4148, Filtro, Sobreamostragem, analogico_para_digital,
                  clipper_diodos, rc_passa_altas, rc_passa_baixa, saturacao_trilho)


class BossDistortionDS1(Pedal):
    """BOSS DS-1, seguindo os estágios do esquema:

    Valores conforme a análise da ElectroSmash
    (https://electrosmash.mas-effects.com/boss-ds1-analysis.html).

    1. Buffer de entrada (Q1) - passa-altas C1 47n / R2 470k (~7,2 Hz).
    2. Booster a transistor (Q2, 2SC2240) - ganho de ~35 dB (56x) com
       realimentação R7 470k || C4 250p (passa-baixa ~1,36 kHz) e passa-altas
       C2/R4 (3,3 Hz) e C3/R5 (33 Hz). Com sinal forte já satura nos trilhos.
    3. Estágio de ganho com amp-op (TA7136), não-inversor, com passa-altas
       de entrada C5 68n / R10 100k (~23 Hz):
       Av(s) = 1 + Zf/Zg, Zf = DIST(100kB) || C7(100p), Zg = R13(4k7) + C8(0,47u)
       -> corte de graves em ~72 Hz e de agudos em ~16 kHz com DIST no máximo.
    4. Clipping: par de 1N4148 anti-paralelos ao terra via R14 (2k2) com
       C10 (10n) -> clipping duro e SIMÉTRICO (~±0,7 V) + passa-baixa ~7,2 kHz.
    5. Tone (estilo Big Muff): passa-baixa R16 6k8 / C12 0,1u (~234 Hz)
       misturado pelo pot TONE (20kB) com passa-altas C11 0,022u / R17 6k8
       (~1,06 kHz) -> "scoop" em ~500 Hz; perda total do tone ~-12 dB.
    6. Pot LEVEL (100kB) + buffer de saída (Q3, seguidor de emissor).
       Há um ganho digital de compensação para recuperar a perda do tone.

    Os estágios não-lineares rodam com sobreamostragem 4x para reduzir aliasing.
    """

    _R13 = 4.7e3
    _C8 = 0.47e-6
    _C7 = 100e-12
    _R_DIST = 100e3
    _R14 = 2.2e3
    _C10 = 10e-9
    _GANHO_BOOSTER = 56.0
    _TRILHO = 4.0  # 9 V com bias em 4,5 V

    def __init__(self, sample_rate: int = 44100):
        super().__init__("BOSS DS-1 Distortion", sample_rate)
        self.distortion = 0.5
        self.tone = 0.5
        self.level = 0.7
        self.intensidade = self.distortion
        self.tom = self.tone
        self.volume = self.level
        self.tipo = TipoPedal.DISTORTION

        self._os = Sobreamostragem(4)
        fs_os = sample_rate * self._os.fator
        self._fs_os = fs_os
        self._hp_entrada = Filtro(*rc_passa_altas(7.2, sample_rate))
        self._hp_booster = Filtro(*rc_passa_altas(33.0, fs_os))
        self._lp_booster = Filtro(*rc_passa_baixa(1.0 / (2 * np.pi * 470e3 * 250e-12), fs_os))
        self._hp_opamp = Filtro(*rc_passa_altas(1.0 / (2 * np.pi * 100e3 * 68e-9), fs_os))
        self._opamp = Filtro()
        self._lp_clip = Filtro(*rc_passa_baixa(1.0 / (2 * np.pi * self._R14 * self._C10), fs_os))
        self._tone_lp = Filtro(*rc_passa_baixa(1.0 / (2 * np.pi * 6.8e3 * 0.1e-6), sample_rate))
        self._tone_hp = Filtro(*rc_passa_altas(1.0 / (2 * np.pi * 6.8e3 * 0.022e-6), sample_rate))
        self._dist_calc = None

    def set_intensidade(self, valor: float):
        self.distortion = float(np.clip(valor, 0.0, 1.0))
        self.intensidade = self.distortion

    def set_tone(self, valor: float):
        self.tone = float(np.clip(valor, 0.0, 1.0))
        self.tom = self.tone

    def set_tom(self, valor: float):
        self.set_tone(valor)

    def set_volume(self, valor: float):
        self.level = float(np.clip(valor, 0.0, 1.0))
        self.volume = self.level

    def set_level(self, valor: float):
        self.set_volume(valor)

    def _atualizar_opamp(self):
        if self._dist_calc == self.distortion:
            return
        rd = self._R_DIST * self.distortion + 100.0
        t1 = rd * self._C7
        t2 = self._R13 * self._C8
        num = [t1 * t2, t1 + t2 + rd * self._C8, 1.0]
        den = [t1 * t2, t1 + t2, 1.0]
        self._opamp.set_coef(*analogico_para_digital(num, den, self._fs_os))
        self._dist_calc = self.distortion

    def _processar(self, samples: np.ndarray) -> np.ndarray:
        self._atualizar_opamp()
        x = self._hp_entrada(samples)

        s = self._os.subir(x)
        s = self._lp_booster(self._hp_booster(s)) * self._GANHO_BOOSTER
        s = saturacao_trilho(s, self._TRILHO)
        s = saturacao_trilho(self._opamp(self._hp_opamp(s)), self._TRILHO)
        s = clipper_diodos(s, self._R14, DIODO_1N4148)
        s = self._lp_clip(s)
        s = self._os.descer(s)

        t = self.tone
        s = (1.0 - t) * self._tone_lp(s) + t * self._tone_hp(s)
        s *= 0.25  # perda de ~-12 dB do tone/level (1,4 Vpp -> 350 mVpp)
        # LEVEL com curva quadrática (mais natural ao ouvido) e +18 dB de
        # compensação digital no máximo, para o pedal não ficar baixo demais.
        return s * 8.0 * self.level ** 2

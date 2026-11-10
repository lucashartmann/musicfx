import numpy as np

from .pedal import Pedal, TipoPedal
from .dsp import (DIODO_1N34A, Filtro, Sobreamostragem, analogico_para_digital,
                  clipper_diodos, rc_passa_altas, rc_passa_baixa, saturacao_trilho,
                  shelf_agudos)


class KlonCentaur(Pedal):
    """Klon Centaur, seguindo os blocos do esquema. Valores conforme a análise
    da ElectroSmash (https://electrosmash.mas-effects.com/klon-centaur-analysis.html).

    1. Buffer de entrada TL072 (C1 0,1u / R2 1M -> passa-altas 1,5 Hz).
       Bypass bufferizado: o buffer atua mesmo com o pedal desligado.
    2. Caminho de clipping: amp-op com corcova de médios em ~1 kHz e ganho
       máximo de ~40 dB (100x), controlado pela seção GAIN1 do pot duplo;
       par de diodos de GERMÂNIO 1N34A (Vf ~0,35 V) ao terra após R13 ->
       clipping suave e simétrico. Este estágio roda em 9 V.
    3. Feed-forward 1 (R7/C16/R19): sinal limpo passa-baixa em ~106 Hz que
       devolve o corpo dos graves.
    4. Feed-forward 2: sinal limpo de banda larga atenuado pela seção GAIN2 do
       pot duplo -> quanto mais GAIN, menos sinal limpo na mistura.
    5. Amplificador somador inversor (392k || 820p -> passa-baixa ~495 Hz).
    6. Treble ativo: shelf em ~408 Hz, de ~-8 dB a ~+18 dB.
    7. Pot OUTPUT (10k) ao terra. O somador roda em +18 V / -9 V (charge
       pump MAX1044): 27 V de headroom, não clipa em uso normal.
    """

    bypass_bufferizado = True
    _TRILHO_9V = 4.0     # estágio de ganho: 9 V com bias em 4,5 V
    _TRILHO_18V = 13.0   # somador: +18 V / -9 V com bias em 4,5 V

    def __init__(self, sample_rate: int = 44100):
        super().__init__("Klon Centaur", sample_rate)
        self.gain = 0.5
        self.treble = 0.5
        self.output = 0.7
        self.intensidade = self.gain
        self.tom = self.treble
        self.volume = self.output
        self.tipo = TipoPedal.OVERDRIVE

        self._os = Sobreamostragem(4)
        self._fs_os = sample_rate * self._os.fator
        self._buffer = Filtro(*rc_passa_altas(1.0 / (2 * np.pi * 0.1e-6 * 1e6), sample_rate))
        self._ganho = Filtro()
        self._ff1 = Filtro(*rc_passa_baixa(106.0, sample_rate))
        self._soma = Filtro(*rc_passa_baixa(1.0 / (2 * np.pi * 392e3 * 820e-12), sample_rate))
        self._tone = Filtro()
        self._gain_calc = None
        self._treble_calc = None

    def set_intensidade(self, valor: float):
        self.intensidade = float(np.clip(valor, 0.0, 1.0))
        self.gain = self.intensidade

    def set_gain(self, valor: float):
        self.set_intensidade(valor)

    def set_treble(self, valor: float):
        self.treble = float(np.clip(valor, 0.0, 1.0))
        self.tom = self.treble

    def set_tom(self, valor: float):
        self.set_treble(valor)

    def set_tone(self, valor: float):
        self.set_treble(valor)

    def set_volume(self, valor: float):
        self.output = float(np.clip(valor, 0.0, 1.0))
        self.volume = self.output

    def set_output(self, valor: float):
        self.set_volume(valor)

    def _atualizar_coeficientes(self):
        if self._gain_calc != self.gain:
            # Av(s) = 1 + K * passa-faixa(1 kHz, Q 0,5): ganho unitário em DC
            # e nos agudos extremos, corcova de médios proporcional ao GAIN
            # (até ~40 dB em 1 kHz com GAIN no máximo).
            k = 1.0 + 98.0 * self.gain ** 2
            w0 = 2 * np.pi * 950.0
            q = 0.5
            num = [1.0, w0 / q * (1.0 + k), w0 * w0]
            den = [1.0, w0 / q, w0 * w0]
            self._ganho.set_coef(*analogico_para_digital(num, den, self._fs_os, 950.0))
            self._gain_calc = self.gain
        if self._treble_calc != self.treble:
            t = self.treble
            ganho_db = -8.0 + 16.0 * t if t <= 0.5 else (t - 0.5) * 36.48
            self._tone.set_coef(*shelf_agudos(408.0, ganho_db, self.sample_rate))
            self._treble_calc = self.treble

    def _processar(self, samples: np.ndarray) -> np.ndarray:
        x = self._buffer(samples)
        if not self.ativo:
            return x
        self._atualizar_coeficientes()

        s = self._os.subir(x)
        s = saturacao_trilho(self._ganho(s), self._TRILHO_9V)
        s = clipper_diodos(s, 1e3, DIODO_1N34A)
        distorcido = self._os.descer(s)

        ff1 = self._ff1(x) * 0.4
        ff2 = x * (1.0 - self.gain) * 0.55
        mix = self._soma(distorcido + ff1 + ff2) * (392e3 / 47e3)
        mix = saturacao_trilho(-mix, self._TRILHO_18V)  # somador é inversor
        s = self._tone(mix)
        # OUTPUT calibrado: com GAIN no zero e OUTPUT no meio, ganho ~unitário;
        # no máximo, ~+12 dB de boost limpo (o Klon é muito usado como boost).
        return s * 0.37 * self.output ** 2

import numpy as np

from .pedal import Pedal, TipoPedal
from .dsp import Filtro, ler_fracionario, rc_passa_altas, rc_passa_baixa, saturacao_trilho


class BossDD3Delay(Pedal):
    """BOSS DD-3 Digital Delay.

    - MODE: S (12,5-50 ms), M (50-200 ms), L (200-800 ms) e HOLD.
    - O sinal seco passa direto; E.LEVEL controla só as repetições.
    - O conversor tem filtros anti-aliasing (~7 kHz) dentro do loop de
      realimentação, então cada repetição fica um pouco mais escura.
    - Girar o TIME muda o delay suavemente (como o pitch "escorregando" no
      pedal real), em vez de pular e gerar cliques.
    - HOLD: grava um trecho do tamanho do delay e repete indefinidamente,
      sem decair e sem gravar sinal novo por cima.
    """

    _FAIXAS_MS = {"50ms": (12.5, 50.0), "200ms": (50.0, 200.0), "800ms": (200.0, 800.0)}
    _HOLD_MS = 800.0
    _GLIDE = 0.002  # fração do caminho até o novo tempo percorrida por amostra

    def __init__(self, sample_rate: int = 44100):
        super().__init__("Boss DD-3 Digital Delay", sample_rate)
        self.time = 0.4
        self.feedback = 0.35
        self.effect_level = 0.5
        self.intensidade = self.effect_level
        self.mode = "800ms"
        self.hold = False
        self.tipo = TipoPedal.DELAY

        self._buf = np.zeros(int(sample_rate * 1.0) + 4096)
        self._idx = 0
        self._delay_atual = self._delay_alvo()
        self._hold_restante = 0
        self._lp_loop = Filtro(*rc_passa_baixa(7000.0, sample_rate))
        self._hp_loop = Filtro(*rc_passa_altas(40.0, sample_rate))

    def set_intensidade(self, valor: float):
        self.set_effect_level(valor)

    def set_time(self, valor: float):
        self.time = float(np.clip(valor, 0.0, 1.0))

    def set_feedback(self, valor: float):
        self.feedback = float(np.clip(valor, 0.0, 0.98))

    def set_effect_level(self, valor: float):
        self.effect_level = float(np.clip(valor, 0.0, 1.0))
        self.intensidade = self.effect_level

    def set_mode(self, mode: str):
        allowed = {"50ms", "200ms", "800ms", "hold"}
        if mode not in allowed:
            raise ValueError(
                "mode deve ser '50ms', '200ms', '800ms' ou 'hold'")
        if mode == "hold" and self.mode != "hold":
            self._hold_restante = int(self.sample_rate * self._HOLD_MS / 1000.0)
        self.mode = mode
        self.hold = mode == "hold"

    def _delay_alvo(self) -> float:
        if self.mode == "hold":
            ms = self._HOLD_MS
        else:
            lo, hi = self._FAIXAS_MS[self.mode]
            ms = lo * (hi / lo) ** self.time  # pot com curva logarítmica
        return ms * self.sample_rate / 1000.0

    def _processar(self, samples: np.ndarray) -> np.ndarray:
        out = np.empty_like(samples)
        alvo = self._delay_alvo()
        if self.hold:
            self._delay_atual = alvo
        pos = 0
        n = len(samples)
        while pos < n:
            # Blocos menores que o delay: toda leitura cai em amostras já escritas.
            m = min(n - pos, max(1, int(min(self._delay_atual, alvo)) - 1))
            x = samples[pos:pos + m]
            k = np.arange(1, m + 1)
            delays = alvo + (self._delay_atual - alvo) * (1.0 - self._GLIDE) ** k
            self._delay_atual = float(delays[-1])
            idxs = self._idx + np.arange(m)
            lido = ler_fracionario(self._buf, idxs - delays)

            if self.hold:
                if self._hold_restante > 0:
                    escrever = x.copy()
                    self._hold_restante -= m
                else:
                    escrever = lido
            else:
                escrever = self._hp_loop(self._lp_loop(x + lido * self.feedback))
                escrever = saturacao_trilho(escrever, 1.0)

            self._buf[idxs % len(self._buf)] = escrever
            self._idx = int((self._idx + m) % len(self._buf))
            out[pos:pos + m] = x + lido * self.effect_level
            pos += m
        return out

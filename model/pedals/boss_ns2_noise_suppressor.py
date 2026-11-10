import math

import numpy as np

from .pedal import Pedal, TipoPedal
from .dsp import coef_tempo


class NS2NoiseSuppressor(Pedal):
    """BOSS NS-2 Noise Suppressor.

    Circuito: detector de envelope (retificador + RC, ataque rápido) que
    controla um VCA. Abaixo do THRESHOLD o VCA fecha suavemente com o tempo de
    DECAY (é um expansor descendente, não um gate liga/desliga), o que evita
    cortar a cauda das notas de forma abrupta.

    Modos (chave MODE):
    - "reduction": supressão de ruído normal.
    - "mute": com o pedal ligado, a saída é silenciada (usado para afinar).
    """

    _ATAQUE_MS = 1.0
    _HISTERESE_DB = 3.0
    _HOLD_MS = 20.0
    _RAZAO_EXPANSAO = 4.0  # 1:4 abaixo do threshold
    _ATENUACAO_MAX_DB = -80.0

    def __init__(self, sample_rate: int = 44100):
        super().__init__("NS-2 Noise Suppressor", sample_rate)
        self.threshold = 0.35
        self.decay = 0.40
        self.mode = "reduction"
        self.intensidade = self.threshold
        self.tipo = TipoPedal.NOISE_SUPPRESSOR
        self._env = 0.0
        self._ganho_db = self._ATENUACAO_MAX_DB
        self._aberto = False
        self._hold = 0

    def set_intensidade(self, valor: float):
        self.threshold = float(np.clip(valor, 0.0, 1.0))
        self.intensidade = self.threshold

    def set_threshold(self, valor: float):
        self.set_intensidade(valor)

    def set_decay(self, valor: float):
        self.decay = float(np.clip(valor, 0.0, 1.0))

    def set_mode(self, mode: str):
        allowed = {"reduction", "mute"}
        if mode not in allowed:
            raise ValueError("mode deve ser 'reduction' ou 'mute'")
        self.mode = mode

    def _processar(self, samples: np.ndarray) -> np.ndarray:
        if self.mode == "mute":
            return np.zeros_like(samples)

        fs = self.sample_rate
        # THRESHOLD: de -80 dBFS (mínimo) a -20 dBFS (máximo).
        limiar_db = -80.0 + self.threshold * 60.0
        limiar_abre = 10.0 ** ((limiar_db + self._HISTERESE_DB / 2) / 20.0)
        limiar_fecha = 10.0 ** ((limiar_db - self._HISTERESE_DB / 2) / 20.0)
        # DECAY: de ~10 ms a ~1 s para o VCA fechar.
        release_ms = 10.0 * (100.0 ** self.decay)
        c_ataque = coef_tempo(self._ATAQUE_MS, fs)
        c_env_release = coef_tempo(10.0, fs)
        # Velocidade do VCA em dB por amostra.
        db_por_amostra_abre = 60.0 / (fs * 0.002)
        db_por_amostra_fecha = 60.0 / (fs * release_ms / 1000.0)
        hold_amostras = int(fs * self._HOLD_MS / 1000.0)

        env, ganho_db = self._env, self._ganho_db
        aberto, hold = self._aberto, self._hold
        ganhos = np.empty(len(samples))
        for i, x in enumerate(np.abs(samples).tolist()):
            env += (c_ataque if x > env else c_env_release) * (x - env)
            if env > limiar_abre:
                aberto = True
                hold = hold_amostras
            elif env < limiar_fecha:
                if hold > 0:
                    hold -= 1
                else:
                    aberto = False
            if aberto:
                alvo = 0.0
            elif env > 1e-9:
                # Expansão descendente: cada dB abaixo do limiar vira RAZAO dB.
                alvo = min(0.0, max((20.0 * math.log10(env) - limiar_db) * (self._RAZAO_EXPANSAO - 1.0),
                                    self._ATENUACAO_MAX_DB))
            else:
                alvo = self._ATENUACAO_MAX_DB
            if alvo > ganho_db:
                ganho_db = min(alvo, ganho_db + db_por_amostra_abre)
            else:
                ganho_db = max(alvo, ganho_db - db_por_amostra_fecha)
            ganhos[i] = ganho_db
        self._env, self._ganho_db = env, ganho_db
        self._aberto, self._hold = aberto, hold
        return samples * 10.0 ** (ganhos / 20.0)

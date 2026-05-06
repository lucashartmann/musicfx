import numpy as np
from .pedal import Pedal, TipoPedal


class NS2NoiseSuppressor(Pedal):

    def __init__(self, sample_rate: int = 48000):
        super().__init__("NS-2 Noise Suppressor")
        self.sample_rate = sample_rate
        self.threshold = 0.35
        self.decay = 0.40
        self.mode = "reduction"
        self.intensidade = self.threshold
        self._env_rms = 0.0
        self._gate_gain = 0.0
        self._gate_open = False
        self._hold_counter = 0
        self._last_decay = -1.0
        self._attack_coef = 0.0
        self._decay_coef = 0.0
        self._vca_coef_fast = 0.0
        self._vca_coef_slow = 0.0
        self.tipo = TipoPedal.NOISE_SUPPRESSOR

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

    def _aplicar_gate(self, samples: np.ndarray) -> np.ndarray:
        if abs(self.decay - self._last_decay) > 0.008:
            attack_ms = 1.2
            release_ms = 12.0 + self.decay * 680.0
            self._attack_coef = 1.0 - \
                np.exp(-1.0 / (self.sample_rate * attack_ms / 1000.0))
            self._decay_coef = 1.0 - \
                np.exp(-1.0 / (self.sample_rate * release_ms / 1000.0))
            self._vca_coef_fast = 1.0 - \
                np.exp(-1.0 / (self.sample_rate * 4.0 / 1000.0))
            self._vca_coef_slow = 1.0 - \
                np.exp(-1.0 / (self.sample_rate * release_ms * 0.65 / 1000.0))
            self._last_decay = self.decay
        threshold = self.threshold * 0.38 + 0.002
        hysteresis = 0.09
        hold_samples = int(self.sample_rate * 0.018)
        limiar_abre = threshold * (1.0 + hysteresis)
        limiar_fecha = threshold * (1.0 - hysteresis)
        n = len(samples)
        out = np.empty(n, dtype=np.float32)
        env = self._env_rms
        gate_gain = self._gate_gain
        gate_open = self._gate_open
        hold = self._hold_counter
        for i in range(n):
            x = samples[i]
            abs_x = abs(x)
            env = env * 0.92 + abs_x * abs_x * 0.08
            env_rms = np.sqrt(env) if env > 1e-12 else 0.0
            if not gate_open:
                if env_rms > limiar_abre:
                    gate_open = True
                    hold = hold_samples
            else:
                if env_rms < limiar_fecha:
                    if hold > 0:
                        hold -= 1
                    else:
                        gate_open = False
                else:
                    hold = hold_samples
            target = 1.0 if gate_open else 0.0
            vca_coef = self._vca_coef_fast if target > gate_gain else self._vca_coef_slow
            gate_gain += vca_coef * (target - gate_gain)
            out[i] = 0.0 if self.mode == "mute" and not gate_open else x * gate_gain
        self._env_rms = env
        self._gate_gain = gate_gain
        self._gate_open = gate_open
        self._hold_counter = hold
        return out

import numpy as np
from scipy.signal import lfilter

from .pedal import Pedal, TipoPedal
from .dsp import Filtro, escrever_circular, ler_fracionario, rc_passa_altas, rc_passa_baixa


class _Linha:
    """Linha de atraso circular."""

    def __init__(self, tamanho: int):
        self.buf = np.zeros(int(tamanho))
        self.idx = 0

    def ler(self, atraso, m: int) -> np.ndarray:
        pos = self.idx + np.arange(m) - atraso
        if np.isscalar(atraso) and float(atraso).is_integer():
            return self.buf[pos.astype(np.int64) % len(self.buf)]
        return ler_fracionario(self.buf, pos)

    def escrever(self, dados: np.ndarray):
        self.idx = escrever_circular(self.buf, self.idx, dados)


# Tempos (amostras a 44,1 kHz) da rede de Schroeder/Moorer usada no Freeverb.
_COMBS = (1116, 1188, 1277, 1356, 1422, 1491, 1557, 1617)
_ALLPASS = (556, 441, 341, 225)

# Parâmetros por modo: tamanho, faixa de realimentação (TIME), amortecimento,
# difusão dos allpass, pré-delay (ms) e ganho de saída (normaliza o nível do
# efeito entre os modos: com E.LEVEL no máximo, efeito ~ seco).
_MODOS = {
    "room":     dict(tamanho=0.45, fb=(0.70, 0.88), damp=0.45, difusao=0.5, pre=4.0, ganho=3.5),
    "hall":     dict(tamanho=1.00, fb=(0.80, 0.975), damp=0.30, difusao=0.5, pre=18.0, ganho=2.9),
    "plate":    dict(tamanho=0.75, fb=(0.78, 0.96), damp=0.08, difusao=0.7, pre=0.0, ganho=1.0),
    "spring":   dict(tamanho=0.35, fb=(0.74, 0.90), damp=0.20, difusao=0.6, pre=0.0, ganho=2.6),
    "modulate": dict(tamanho=1.00, fb=(0.80, 0.975), damp=0.30, difusao=0.5, pre=18.0, ganho=2.9),
    "shimmer":  dict(tamanho=1.00, fb=(0.82, 0.975), damp=0.25, difusao=0.6, pre=18.0, ganho=2.5),
    "dynamic":  dict(tamanho=1.00, fb=(0.80, 0.975), damp=0.30, difusao=0.5, pre=18.0, ganho=2.9),
    "delay":    dict(tamanho=0.75, fb=(0.78, 0.95), damp=0.30, difusao=0.5, pre=0.0, ganho=1.5),
}


class BossRV6Reverb(Pedal):
    """BOSS RV-6 Reverb (pedal digital).

    Rede de reverb com 8 filtros comb em paralelo, cada um com um passa-baixa
    no loop (as altas decaem mais rápido, como numa sala), seguidos de 4
    allpass em série para difusão. Cada MODE ajusta tamanho, decaimento,
    brilho e pré-delay; alguns adicionam processamento próprio:

    - modulate: allpass com atraso modulado (cauda com chorus).
    - spring:   cadeia de allpass dispersivos (o "chirp" da mola).
    - shimmer:  pitch shift de +1 oitava realimentado no reverb.
    - dynamic:  a cauda é abafada enquanto se toca e cresce nas pausas.
    - delay:    delay de ~400 ms antes do reverb.

    O sinal seco passa direto; E.LEVEL controla só o efeito. TONE ajusta o
    brilho da cauda.
    """

    _DELAY_MODO_MS = 400.0

    def __init__(self, sample_rate: int = 44100):
        super().__init__("Boss RV-6 Reverb", sample_rate)
        self.time = 0.5
        self.level = 0.45
        self.tone = 0.6
        self.mode = "hall"
        self.decay = self.time
        self.mix = self.level
        self.intensidade = self.level
        self.tipo = TipoPedal.REVERB

        esc = sample_rate / 44100.0
        self._combs = [_Linha(int(d * esc) + 8) for d in _COMBS]
        self._comb_lp = [np.zeros(1) for _ in _COMBS]
        self._aps = [_Linha(int(d * esc) + 64) for d in _ALLPASS]
        self._esc = esc
        self._pre = _Linha(int(sample_rate * 0.05) + 4096)
        self._delay = _Linha(int(sample_rate * self._DELAY_MODO_MS / 1000.0) + 4096)
        self._shift = _Linha(8192)
        self._shift_fase = 0.0
        self._shimmer_retorno = np.zeros(0)
        self._spring_z = [np.zeros(1) for _ in range(6)]
        self._mod_fase = 0.0
        self._env = np.zeros(1)
        self._hp = Filtro(*rc_passa_altas(80.0, sample_rate))
        self._lp = Filtro()
        self._tone_calc = None

    def set_intensidade(self, valor: float):
        self.set_mix(valor)

    def set_decay(self, valor: float):
        self.time = float(np.clip(valor, 0.0, 1.0))
        self.decay = self.time

    def set_mix(self, valor: float):
        self.mix = float(np.clip(valor, 0.0, 1.0))
        self.level = self.mix
        self.intensidade = self.mix

    def set_time(self, valor: float):
        self.set_decay(valor)

    def set_level(self, valor: float):
        self.set_mix(valor)

    def set_mode(self, mode: str):
        if mode not in _MODOS:
            raise ValueError("mode deve ser um dos modos do RV-6")
        self.mode = mode

    def set_tone(self, valor: float):
        self.tone = float(np.clip(valor, 0.0, 1.0))

    # --- blocos ---------------------------------------------------------

    def _rede(self, x: np.ndarray, p: dict) -> np.ndarray:
        """Combs em paralelo + allpass em série, em sub-blocos menores que o
        menor atraso realimentado (assim tudo é vetorizado)."""
        tam = p["tamanho"]
        fb = p["fb"][0] + (p["fb"][1] - p["fb"][0]) * self.time
        damp = p["damp"] + (1.0 - self.tone) * 0.3
        g = p["difusao"]
        d_combs = [max(1, int(d * self._esc * tam)) for d in _COMBS]
        d_aps = [max(1, int(d * self._esc * tam)) for d in _ALLPASS]
        modula = self.mode == "modulate"
        prof_mod = 12.0 * self._esc if modula else 0.0
        bloco = max(1, min(min(d_combs), min(d_aps)) - int(prof_mod) - 2)

        out = np.empty_like(x)
        pos = 0
        while pos < len(x):
            m = min(bloco, len(x) - pos)
            entrada = x[pos:pos + m] * 0.015
            soma = np.zeros(m)
            for j, linha in enumerate(self._combs):
                lido = linha.ler(d_combs[j], m)
                filt, self._comb_lp[j] = lfilter([1.0 - damp], [1.0, -damp], lido, zi=self._comb_lp[j])
                linha.escrever(entrada + filt * fb)
                soma += lido
            s = soma
            for j, linha in enumerate(self._aps):
                atraso = d_aps[j]
                if modula:
                    fases = self._mod_fase + np.arange(m) * (0.7 + 0.3 * j) / self.sample_rate
                    atraso = atraso - prof_mod * (0.5 + 0.5 * np.sin(2 * np.pi * fases))
                lido = linha.ler(atraso, m)
                linha.escrever(s + lido * g)
                s = lido - s * g
            if modula:
                self._mod_fase += m / self.sample_rate
            out[pos:pos + m] = s
            pos += m
        return out * 3.0

    def _mola(self, x: np.ndarray) -> np.ndarray:
        """Allpass de 1ª ordem em cascata: atrasam mais os graves que os
        agudos (dispersão), gerando o 'chirp' característico da mola."""
        for j in range(len(self._spring_z)):
            a = -0.65
            x, self._spring_z[j] = lfilter([a, 1.0], [1.0, a], x, zi=self._spring_z[j])
        return x

    def _oitava_acima(self, x: np.ndarray) -> np.ndarray:
        """Pitch shift de +12 semitons com duas leituras cruzadas (granular)."""
        m = len(x)
        inicio = self._shift.idx
        self._shift.escrever(x)
        janela = 2048.0
        fases = (self._shift_fase + np.arange(m)) % janela
        self._shift_fase = float((self._shift_fase + m) % janela)
        saida = np.zeros(m)
        for desloc in (0.0, janela / 2):
            f = (fases + desloc) % janela
            atraso = 1.0 + (janela - f)  # razão 2: o atraso cai 1 amostra/amostra
            peso = np.sin(np.pi * f / janela) ** 2
            saida += peso * ler_fracionario(self._shift.buf, inicio + np.arange(m) - atraso)
        return saida

    def _atualizar_tone(self):
        if self._tone_calc != self.tone:
            self._lp.set_coef(*rc_passa_baixa(2000.0 * 6.0 ** self.tone, self.sample_rate))
            self._tone_calc = self.tone

    def _processar(self, samples: np.ndarray) -> np.ndarray:
        self._atualizar_tone()
        p = _MODOS.get(self.mode, _MODOS["hall"])
        n = len(samples)
        fs = self.sample_rate

        x = self._hp(samples)
        if self.mode == "delay":
            d = fs * self._DELAY_MODO_MS / 1000.0
            eco = np.empty(n)
            pos = 0
            while pos < n:
                m = min(n - pos, int(d) - 1)
                lido = self._delay.ler(d, m)
                self._delay.escrever(x[pos:pos + m] + lido * 0.35)
                eco[pos:pos + m] = lido
                pos += m
            x = x + eco
        if self.mode == "shimmer" and len(self._shimmer_retorno) == n:
            x = x + self._shimmer_retorno

        self._pre.escrever(x)
        x = self._pre.ler(n + int(fs * p["pre"] / 1000.0), n)

        molhado = self._rede(x, p)
        if self.mode == "spring":
            molhado = self._mola(molhado) * 1.3
        if self.mode == "shimmer":
            # Realimentação limitada (tanh) para a cauda crescer sem divergir.
            self._shimmer_retorno = np.tanh(self._oitava_acima(molhado) * 0.6) * 0.05
        if self.mode == "dynamic":
            c = 1.0 - np.exp(-1.0 / (fs * 0.15))
            env, self._env = lfilter([c], [1.0, c - 1.0], np.abs(samples), zi=self._env)
            molhado = molhado / (1.0 + 12.0 * env)
        if self.mode == "delay":
            molhado = molhado * 0.7 + eco * 0.6

        molhado = self._lp(molhado) * p["ganho"]
        return samples + molhado * self.level

from enum import Enum

import numpy as np

from .dsp import para_float, float_para_bytes


class TipoPedal(Enum):
    DISTORTION = "Distortion"
    DELAY = "Delay"
    REVERB = "Reverb"
    CHORUS = "Chorus"
    NOISE_GATE = "Noise Gate"
    NOISE_SUPPRESSOR = "Noise Suppressor"
    OVERDRIVE = "Overdrive"
    FUZZ = "Fuzz"
    WAH = "Wah"


class Pedal:
    # Pedais com bypass bufferizado (ex.: Klon) processam o buffer de entrada
    # mesmo desligados; os demais são true bypass / bypass eletrônico limpo.
    bypass_bufferizado = False

    def __init__(self, nome, sample_rate: int = 44100):
        self.nome = nome
        self.sample_rate = sample_rate
        self.ativo = False
        self.intensidade = 0.5
        self.tipo = None

    def set_tipo(self, tipo: TipoPedal):
        self.tipo = tipo

    def get_tipo(self):
        if self.tipo is None:
            return None
        else:
            return self.tipo.value

    def get_nome(self):
        return self.nome

    def set_nome(self, nome):
        self.nome = nome

    def ligar(self):
        self.ativo = True

    def desligar(self):
        self.ativo = False

    def get_intensidade(self):
        return self.intensidade

    def set_intensidade(self, valor):
        self.intensidade = valor

    def processar(self, audio_data):
        """Aceita bytes int16 ou array float e devolve no mesmo formato."""
        if not self.ativo and not self.bypass_bufferizado:
            return audio_data
        samples, era_bytes = para_float(audio_data)
        if len(samples) == 0:
            return audio_data
        try:
            out = np.asarray(self._processar(samples.astype(np.float64)), dtype=np.float32)
        except Exception as e:
            print(f"Erro em {self.__class__.__name__}.processar: {e}")
            return audio_data
        if era_bytes:
            return float_para_bytes(out)
        return out

    def _processar(self, samples: np.ndarray) -> np.ndarray:
        return samples

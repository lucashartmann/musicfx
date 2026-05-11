from enum import Enum


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
    def __init__(self, nome):
        self.nome = nome
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
        return audio_data

class Pedal:
    def __init__(self, nome):
        self.nome = nome
        self.ativo = False
        self.intensidade = 0.5

    def set_intensidade(self, valor):
        self.intensidade = valor

    def processar(self, audio_data):
        return audio_data

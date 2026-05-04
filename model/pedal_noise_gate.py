import struct
from .pedal import Pedal

class NoiseGate(Pedal):
    def __init__(self):
        super().__init__("Noise Gate")
        self.limiar = 0.5
    
    def processar(self, audio_data):
        """Aplica gate de ruído: silencia sinais abaixo do limiar."""
        if not self.ativo:
            return audio_data
        
        try:
            # Desempacota samples int16
            num_samples = len(audio_data) // 2
            samples = struct.unpack(f'<{num_samples}h', audio_data)
            
            # Calcula limiar
            limiar_absoluto = int(32768.0 * self.intensidade)
            
            # Silencia amostras abaixo do limiar
            processados = [sample if abs(sample) > limiar_absoluto else 0 for sample in samples]
            
            # Reempacota em bytes
            return struct.pack(f'<{num_samples}h', *processados)
        except Exception as e:
            print(f"Erro em NoiseGate.processar: {e}")
            return audio_data
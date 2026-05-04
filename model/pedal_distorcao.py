import struct
from .pedal import Pedal

class Distorcao(Pedal):
    def __init__(self):
        super().__init__("Distorção")
        self.ganho = 0.5
        self.intensidade = 0.5
        
    def set_ganho(self, valor):
        self.ganho = valor
    
    def processar(self, audio_data):
        """Aplica distorção agressiva (Metallica/Pantera style)."""
        if not self.ativo:
            return audio_data
        
        try:
            num_samples = len(audio_data) // 2
            samples = struct.unpack(f'<{num_samples}h', audio_data)
            
            # Drive extremo para heavy metal (0 a 1 = 5x a 50x)
            drive = 20.0 + self.intensidade * 45.0
            
            processados = []
            for sample in samples:
                # Amplifica brutal
                amplificado = int(sample * drive)
                
                # Hard clipping agressivo para sons pesados
                if amplificado > 32767:
                    clipped = 32767
                elif amplificado < -32768:
                    clipped = -32768
                else:
                    clipped = amplificado
                
                processados.append(clipped)
            
            return struct.pack(f'<{num_samples}h', *processados)
        except Exception as e:
            print(f"Erro em Distorcao.processar: {e}")
            return audio_data

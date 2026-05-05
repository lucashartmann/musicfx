import numpy as np
from .pedal import Pedal


class NoiseGate(Pedal):

    def __init__(self, sample_rate: int = 48000):
        super().__init__("Noise Gate")
        self.sample_rate = sample_rate
        self.intensidade = 0.3  
        self.decay       = 0.3  
        self._envelope  = 0.0
        self._gate_gain = 0.0
        self._gate_open = False   

 
    def set_intensidade(self, valor: float):
        self.intensidade = float(np.clip(valor, 0.0, 1.0))

    def set_decay(self, valor: float):
        self.decay = float(np.clip(valor, 0.0, 1.0))

    def processar(self, audio_data):
        if not self.ativo:
            return audio_data
        try:
            if isinstance(audio_data, (bytes, bytearray)):
                samples = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
                retornar_bytes = True
            else:
                samples = np.asarray(audio_data, dtype=np.float32)
                if samples.ndim > 1:
                    samples = samples[:, 0]
                retornar_bytes = False

            out = self._aplicar_gate(samples)

            if retornar_bytes:
                return (out * 32767).clip(-32768, 32767).astype(np.int16).tobytes()
            return out

        except Exception as e:
            print(f"Erro em NoiseGate.processar: {e}")
            return audio_data


    def _aplicar_gate(self, samples: np.ndarray) -> np.ndarray:
    
        attack_ms = 1.0
        decay_ms  = 10.0 + self.decay * 490.0   
        attack_coef = 1.0 - np.exp(-1.0 / (self.sample_rate * attack_ms / 1000.0))
        decay_coef  = 1.0 - np.exp(-1.0 / (self.sample_rate * decay_ms  / 1000.0))
        limiar      = self.intensidade * 0.5
        limiar_abre = limiar * 1.10
        limiar_fecha = limiar * 0.90
        vca_attack = attack_coef * 4.0  
        vca_decay  = decay_coef
        n = len(samples)
        gains = np.empty(n, dtype=np.float32)
        env       = self._envelope
        gate_gain = self._gate_gain
        gate_open = self._gate_open

        for i in range(n):
            amplitude = abs(samples[i])

            
            if amplitude > env:
                env += attack_coef * (amplitude - env)
            else:
                env += decay_coef  * (amplitude - env)

            
            if not gate_open and env > limiar_abre:
                gate_open = True
            elif gate_open and env < limiar_fecha:
                gate_open = False

            
            target = 1.0 if gate_open else 0.0
            if target > gate_gain:
                gate_gain += vca_attack * (target - gate_gain)
            else:
                gate_gain += vca_decay  * (target - gate_gain)

            gains[i] = gate_gain

        
        self._envelope  = env
        self._gate_gain = gate_gain
        self._gate_open = gate_open

        return samples * gains
import numpy as np
from .pedal import Pedal


class Distorcao(Pedal):
  
    def __init__(self, sample_rate: int = 48000):
        super().__init__("Distorção")
        self.sample_rate = sample_rate
        self.intensidade = 0.5
        self.tom = 0.5
        self.volume = 0.7
        self._tone_z1 = 0.0
        self._tone_z2 = 0.0
        self._pre_z1  = 0.0  

    def set_intensidade(self, valor: float):
        self.intensidade = float(np.clip(valor, 0.0, 1.0))

    def set_tom(self, valor: float):
        self.tom = float(np.clip(valor, 0.0, 1.0))

    def set_volume(self, valor: float):
        self.volume = float(np.clip(valor, 0.0, 1.0))


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

            out = self._estagio_pre_ganho(samples)
            out = self._estagio_clipping(out)
            out = self._estagio_tone(out)
            out = out * self.volume

            np.clip(out, -1.0, 1.0, out=out)

            if retornar_bytes:
                return (out * 32767).astype(np.int16).tobytes()
            return out

        except Exception as e:
            print(f"Erro em Distorcao.processar: {e}")
            return audio_data


    def _estagio_pre_ganho(self, samples: np.ndarray) -> np.ndarray:
      
        fc = 20.0  # Hz
        alpha = 1.0 - np.exp(-2.0 * np.pi * fc / self.sample_rate)
        hp = np.empty_like(samples)
        z = self._pre_z1
        for i, s in enumerate(samples):
            z = z + alpha * (s - z)
            hp[i] = s - z
        self._pre_z1 = z

       
        drive = 2.0 + self.intensidade * 199.0
        return hp * drive


    def _estagio_clipping(self, samples: np.ndarray) -> np.ndarray:
       
        vf_germanio = 0.30   
        vf_silicio   = 0.65  

        out = np.where(
            samples >= 0,
            vf_germanio * np.tanh(samples / vf_germanio),
            vf_silicio  * np.tanh(samples / vf_silicio),
        )
        return out

   

    def _estagio_tone(self, samples: np.ndarray) -> np.ndarray:
       
        fc = 1000.0   
        w0 = 2.0 * np.pi * fc / self.sample_rate
        K  = np.tan(w0 / 2.0)

        
        gain_db  = (self.tom - 0.5) * 24.0
        gain_lin = 10.0 ** (gain_db / 20.0)

        if gain_db >= 0:
           
            b0 = (gain_lin + K) / (1.0 + K)
            b1 = (gain_lin - K) / (1.0 + K)
            a1 = (K - 1.0)     / (1.0 + K)
        else:
            
            b0 = (1.0 + K)               / (gain_lin + K)
            b1 = (K - 1.0)               / (gain_lin + K)
            a1 = (K - gain_lin)           / (gain_lin + K)

        
        out = np.empty_like(samples)
        z1, z2 = self._tone_z1, self._tone_z2
        for i, x in enumerate(samples):
            y = b0 * x + z1
            z1 = b1 * x - a1 * y + z2
            z2 = 0.0           
            out[i] = y
        self._tone_z1 = z1
        self._tone_z2 = z2

        return out
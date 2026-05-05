import sounddevice as sd
import numpy as np
import threading


class Audio:

    def __init__(self):
        self.entrada = None
        self.saida = None
        self.pedais = []
        self._stream = None
        self._thread_ativa = False
        self._chunk = 128  
        self._sample_rate = 44100
        self._channels = 1

    def get_pedais(self):
        return self.pedais

    def get_entrada(self):
        return self.entrada

    def get_saida(self):
        return self.saida

    def set_entrada(self, dispositivo):
        self.entrada = int(dispositivo)

    def set_saida(self, dispositivo):
        self.saida = int(dispositivo)

    def add_pedal(self, pedal):
        if pedal not in self.pedais:
            self.pedais.append(pedal)
            return True
        return False

    def remove_pedal(self, pedal):
        if pedal in self.pedais:
            self.pedais.remove(pedal)
            return True
        return False

    def _processar_audio(self, input_data):
        resultado = input_data
        for pedal in self.pedais:
            if pedal.ativo:
                resultado = pedal.processar(resultado)
        return resultado
    
    def _callback(self, indata, outdata, frames, time, status):
        if status:
            print(f"Status: {status}")

        try:
            mono = indata[:, 0:1] if indata.ndim > 1 else indata.reshape(-1, 1)
            
            raw_bytes = (mono * 32767).astype(np.int16).tobytes()
            processed_bytes = self._processar_audio(raw_bytes)
            
            audio_float = np.frombuffer(processed_bytes, dtype=np.int16).astype(np.float32) / 32767.0
        
            if audio_float.ndim == 1:
                audio_float = audio_float.reshape(-1, 1)
            outdata[:] = np.tile(audio_float, (1, outdata.shape[1]))
            
        except Exception as e:
            print(f"Erro no callback: {e}")
            outdata.fill(0)
            
    def listar_dispositivos_audio(self):
        dispositivos = sd.query_devices()
        hostapis = sd.query_hostapis()

        dicionario = {"entrada": [], "saida": []}

        print("\n=== DISPOSITIVOS DISPONÍVEIS ===")
        for i, dev in enumerate(dispositivos):
            api = hostapis[dev['hostapi']]['name']
            nome = dev['name']
            print(f"  [{i:2d}] {nome} | {api} | In:{dev['max_input_channels']} Out:{dev['max_output_channels']}")

            if "BEHRINGER" in nome.upper():
                if dev['max_input_channels'] > 0:
                    dicionario["entrada"].append((i, nome))
                if dev['max_output_channels'] > 0:
                    dicionario["saida"].append((i, nome))

        return dicionario

    def iniciar(self):
        if self.entrada is None or self.saida is None:
            print("Erro: Dispositivo de entrada ou saída não definido.")
            return False

        try:
            if self._stream is not None:
                self.parar()

            print(f"Iniciando stream: entrada [{self.entrada}] / saída [{self.saida}]")

            self._stream = sd.Stream(
                device=(self.entrada, self.saida),
                samplerate=self._sample_rate,
                blocksize=self._chunk,        
                dtype='float32',
                channels=(1, 2),              
                callback=self._callback,
                latency='low'
            )
            self._stream.start()
            print("Stream iniciado com sucesso!")
            return True

        except Exception as e:
            print(f"Erro ao iniciar stream: {e}")
            import traceback
            traceback.print_exc()
            return False

    def parar(self):
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
                self._stream = None
                print("Stream parado.")
                return True
            except Exception as e:
                print(f"Erro ao parar stream: {e}")
                return False
        else:
            print("Erro: Stream não iniciado.")
            return False
import sounddevice as sd
import numpy as np
import wave


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
        self.volume = 0.5
        self.amps = []
        self.gravando = False
        self._gravacao_pausada = False
        self._gravacao_buffer = bytearray()
        
    def iniciar_gravacao(self):
        if self.gravando:
            print("Gravação já está ativa.")
            return False

        if not self._gravacao_pausada:
            self._gravacao_buffer.clear()

        self.gravando = True
        self._gravacao_pausada = False
        return True

    def parar_gravacao(self):
        if not self.gravando and not self._gravacao_pausada:
            print("Gravação não está ativa.")
            return False

        self.gravando = False
        self._gravacao_pausada = False

        if self._gravacao_buffer:
            with wave.open("gravacao.wav", "wb") as arquivo:
                arquivo.setnchannels(self._channels)
                arquivo.setsampwidth(np.dtype(np.int16).itemsize)
                arquivo.setframerate(self._sample_rate)
                arquivo.writeframes(bytes(self._gravacao_buffer))

        self._gravacao_buffer.clear()
        return True

    def pausar_gravacao(self):
        if not self.gravando:
            print("Gravação não está ativa.")
            return False

        self.gravando = False
        self._gravacao_pausada = True
        return True

    def gravacao_ativa(self):
        return self.gravando or self._gravacao_pausada

    def add_amp(self, amp):
        if amp not in self.amps:
            self.amps.append(amp)
            return True
        return False

    def remove_amp(self, amp):
        if amp in self.amps:
            self.amps.remove(amp)
            return True
        return False

    def get_amps(self):
        return self.amps

    def set_volume(self, valor: float):
        self.volume = float(np.clip(valor, 0.0, 1.0))

    def get_volume(self):
        return self.volume

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
        for amp in self.amps:
            if amp.ativo:
                resultado = amp.processar(resultado)
        return resultado

    def _callback(self, indata, outdata, frames, time, status):
        if status:
            print(f"Status: {status}")

        try:
            mono = indata[:, 0:1] if indata.ndim > 1 else indata.reshape(-1, 1)

            raw_bytes = (mono * 32767).astype(np.int16).tobytes()
            processed_bytes = self._processar_audio(raw_bytes)

            audio_float = np.frombuffer(
                processed_bytes, dtype=np.int16).astype(np.float32) / 32767.0

            if audio_float.ndim == 1:
                audio_float = audio_float.reshape(-1, 1)
            audio_float = np.clip(audio_float * self.volume, -1.0, 1.0)
            outdata[:] = np.tile(audio_float, (1, outdata.shape[1]))

            if self.gravando:
                self._gravacao_buffer.extend((audio_float * 32767).astype(np.int16).tobytes())

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
            nome = f"[{i:2d}] {nome} | {api} | In:{dev['max_input_channels']} Out:{dev['max_output_channels']}"

            
            if dev['max_input_channels'] > 0:
                if (i, nome) not in dicionario["entrada"]:
                    dicionario["entrada"].append((i, nome))
            if dev['max_output_channels'] > 0:
                if (i, nome) not in dicionario["saida"]:
                    dicionario["saida"].append((i, nome))

        return dicionario

    def iniciar(self):
        if self.entrada is None or self.saida is None:
            print("Erro: Dispositivo de entrada ou saída não definido.")
            return False

        try:
            if self._stream is not None:
                self.parar()

            print(
                f"Iniciando stream: entrada [{self.entrada}] / saída [{self.saida}]")

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

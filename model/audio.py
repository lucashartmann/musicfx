import pyaudio
import threading


class Audio:

    def __init__(self):
        self.entrada = None
        self.saida = None
        self.pedais = []
        self.input_stream = None
        self.output_stream = None
        self._pa = None
        self._thread_ativa = False
        self._thread = None
        self._chunk = 256

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
        """Aplica todos os pedais ativos ao áudio."""
        resultado = input_data
        for pedal in self.pedais:
            if pedal.ativo:
                resultado = pedal.processar(resultado)
        return resultado

    def _thread_audio(self):
        """Thread de processamento de áudio."""
        while self._thread_ativa:
            try:
                data = self.input_stream.read(self._chunk, exception_on_overflow=False)
                processado = self._processar_audio(data)
                self.output_stream.write(processado)
            except Exception as e:
                print(f"Erro no thread de áudio: {e}")
                break

    def _obter_info_dispositivo(self, indice):
        return self._pa.get_device_info_by_index(indice) 

    def iniciar(self):
        if self.entrada is not None and self.saida is not None:
            try:
                if self.input_stream or self.output_stream:
                    self.parar()
                self._pa = pyaudio.PyAudio()
                
                # Valida índices
                devices = self.listar_dispositivos_audio()
                entrada_valida = any(idx == self.entrada for idx, _ in devices["entrada"])
                saida_valida = any(idx == self.saida for idx, _ in devices["saida"])
                
                if not entrada_valida:
                    print(f"Erro: Índice de entrada {self.entrada} inválido.")
                    self._fechar_pyaudio()
                    return False
                if not saida_valida:
                    print(f"Erro: Índice de saída {self.saida} inválido.")
                    self._fechar_pyaudio()
                    return False
                
                input_info = self._pa.get_device_info_by_index(self.entrada)
                output_info = self._pa.get_device_info_by_index(self.saida)

                sample_rate = int(min(
                    input_info.get("defaultSampleRate", 44100),
                    output_info.get("defaultSampleRate", 44100)
                ))

                # Usar os canais reais do dispositivo, mínimo 1
                input_channels = min(int(input_info.get("maxInputChannels", 1)), 2)
                output_channels = min(int(output_info.get("maxOutputChannels", 1)), 2)

                print(
                    f"Iniciando streams: entrada [{self.entrada}] / saída [{self.saida}] / "
                    f"rate {sample_rate} / in {input_channels}ch / out {output_channels}ch..."
                )
                
                self.input_stream = self._pa.open(
                    format=pyaudio.paInt16,
                    channels=input_channels,   # <-- dinâmico
                    rate=sample_rate,
                    input=True,
                    input_device_index=self.entrada,
                    frames_per_buffer=self._chunk,
                )

                self.output_stream = self._pa.open(
                    format=pyaudio.paInt16,
                    channels=output_channels,  # <-- dinâmico
                    rate=sample_rate,
                    output=True,
                    output_device_index=self.saida,
                    frames_per_buffer=self._chunk,
                )
                                
                # Inicia thread de processamento
                self._thread_ativa = True
                self._thread = threading.Thread(target=self._thread_audio, daemon=True)
                self._thread.start()
                
                print("Stream iniciado com sucesso!")
                return True
            except Exception as e:
                print(f"Erro ao iniciar stream de áudio: {e}")
                import traceback
                traceback.print_exc()
                self._fechar_pyaudio()
                return False
        else:
            print("Erro: Dispositivo de entrada ou saída não definido.", self.entrada, self.saida)
            return False

    def _fechar_pyaudio(self):
        if self._pa is not None:
            self._pa.terminate()
            self._pa = None

    def parar(self):
        self._thread_ativa = False
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None
        if self.input_stream:
            self.input_stream.stop_stream()
            self.input_stream.close()
            self.input_stream = None
        if self.output_stream:
            self.output_stream.stop_stream()
            self.output_stream.close()
            self.output_stream = None
        if self._pa:
            self._fechar_pyaudio()
            return True
        else:
            print("Erro: Stream de áudio não iniciado.")
            return False

    def listar_dispositivos_audio(self):
        p = pyaudio.PyAudio()
        numdevices = p.get_device_count()  # <-- índice global
        dicionario = {"entrada": [], "saida": []}

        for i in range(numdevices):
            device_info = p.get_device_info_by_index(i)  # <-- índice global
            device_name = device_info.get('name')
            max_input = device_info.get('maxInputChannels')
            max_output = device_info.get('maxOutputChannels')

            print(f"  [{i}] {device_name} | Input: {max_input} | Output: {max_output}")

            if max_input > 0:
                dicionario["entrada"].append((i, device_name))
            if max_output > 0:
                dicionario["saida"].append((i, device_name))

        p.terminate()
        return dicionario


from textual.app import App
from textual.containers import Container, Horizontal, Grid
from textual.widgets import Static, Select, Checkbox, Tab, Tabs, ProgressBar, Button
from .widgets.slider import Slider
from .config import ConfigScreen
from textual import on
from textual.events import ScreenResume
from textual.screen import Screen
from model import Init
from textual.binding import Binding
from .equipamentos import EquipamentosScreen


class InicioScreen(Screen):

    CSS_PATH = ["css/base.tcss", "css/app.tcss"]

    @on(ScreenResume)
    def on_screen_resume(self, event: ScreenResume):
        self.query_one(Tabs).active = self.query_one(
            "#tab_inicio", Tab).id

    def on_mount(self):
        dicionario = self.app.audio.listar_dispositivos_audio()
        if "entrada" in dicionario.keys() and len(dicionario["entrada"]) > 0:
            self.mount(Select(((nome, indice)
                       for indice, nome in dicionario["entrada"]), id="input_select"), after=self.query_one("#input_label"))
        if "saida" in dicionario.keys() and len(dicionario["saida"]) > 0:
            self.mount(Select(((nome, indice)
                       for indice, nome in dicionario["saida"]), id="output_select"), after=self.query_one("#output_label"))

        dispositivos = self.app.banco.listar_dispositivos()
        if dispositivos:
            for dicionario in dispositivos:
                tipo = dicionario["tipo"]
                nome = dicionario["nome"]
                if tipo == "entrada":
                    try:
                        self.query_one("#input_select").value = nome
                    except Exception as e:
                        print(f"Erro ao definir valor do select de entrada: {e}")
                elif tipo == "saida":
                    try:
                        self.query_one("#output_select").value = nome
                    except Exception as e:
                        print(f"Erro ao definir valor do select de saída: {e}")

    def compose(self):
        yield Tabs(Tab("Inicio", id="tab_inicio"), Tab("Configurações", id="tab_configuracoes"), Tab("Equipamentos", id="tab_equipamentos"), id="tabs", active="tab_inicio")
        with Horizontal(id="dispositivos"):
            yield Static("Input:", id="input_label")
            yield Static("Output:", id="output_label")

        with Grid(id="equipamentos"):

            with Container(id="boss_ce5_chorus"):
                yield Static("BOSS CE-5 Chorus", classes="titulo_pedal")
                yield Checkbox("Ativar", id="boss_ce5_chorus_checkbox")
                with Horizontal():
                    yield Static("Efeito:")
                    yield Slider(id="boss_ce5_chorus_slider")
                with Horizontal():
                    yield Static("Rate:")
                    yield Slider(id="boss_ce5_chorus_rate_slider")
                with Horizontal():
                    yield Static("Depth:")
                    yield Slider(id="boss_ce5_chorus_depth_slider")
                with Horizontal():
                    yield Static("Mix:")
                    yield Slider(id="boss_ce5_chorus_mix_slider")

            with Container(id="boss_dd3_delay"):
                yield Static("BOSS DD-3 Delay", classes="titulo_pedal")
                yield Checkbox("Ativar", id="boss_dd3_delay_checkbox")
                with Horizontal():
                    yield Static("Efeito:")
                    yield Slider(id="boss_dd3_delay_slider")
                with Horizontal():
                    yield Static("Feedback:")
                    yield Slider(id="boss_dd3_delay_feedback_slider")

            with Container(id="boss_rv6_reverb"):
                yield Static("BOSS RV-6 Reverb", classes="titulo_pedal")
                yield Checkbox("Ativar", id="boss_rv6_reverb_checkbox")
                with Horizontal():
                    yield Static("Decay:")
                    yield Slider(id="boss_rv6_reverb_decay_slider")
                with Horizontal():
                    yield Static("Mix:")
                    yield Slider(id="boss_rv6_reverb_mix_slider")
                with Horizontal():
                    yield Static("Tone:")
                    yield Slider(id="boss_rv6_reverb_tone_slider")

            with Container(id="boss_distortion_ds1"):
                yield Static("BOSS DS-1 Distortion", classes="titulo_pedal")
                yield Checkbox("Ativar", id="boss_distortion_ds1_checkbox")
                with Horizontal():
                    yield Static("Efeito:")
                    yield Slider(id="boss_distortion_ds1_slider")
                with Horizontal():
                    yield Static("Tom:")
                    yield Slider(id="boss_distortion_ds1_tom_slider")

            with Container(id="boss_ns2_noise_suppressor"):
                yield Static("BOSS NS-2 Noise Suppressor", classes="titulo_pedal")
                yield Checkbox("Ativar", id="boss_ns2_noise_suppressor_checkbox")
                with Horizontal():
                    yield Static("Efeito:")
                    yield Slider(id="boss_ns2_noise_suppressor_slider")
                with Horizontal():
                    yield Static("Tom:")
                    yield Slider(id="boss_ns2_noise_suppressor_decay_slider")

            with Container(id="klon_centaur"):
                yield Static("Klon Centaur", classes="titulo_pedal")
                yield Checkbox("Ativar", id="klon_centaur_checkbox")
                with Horizontal():
                    yield Static("Efeito:")
                    yield Slider(id="klon_centaur_slider")
                with Horizontal():
                    yield Static("Tom:")
                    yield Slider(id="klon_centaur_tom_slider")

            with Container(id="marshall_plexi_super_lead_1959"):
                yield Static("Marshall Plexi Super Lead 1959", classes="titulo_amp")
                yield Checkbox("Ativar", id="marshall_plexi_super_lead_1959_checkbox")
                with Horizontal():
                    yield Static("Volume:")
                    yield Slider(id="marshall_plexi_super_lead_1959_volume_slider")
                with Horizontal():
                    yield Static("Gain:")
                    yield Slider(id="marshall_plexi_super_lead_1959_gain_slider")
                with Horizontal():
                    yield Static("Bass:")
                    yield Slider(id="marshall_plexi_super_lead_1959_bass_slider")
                with Horizontal():
                    yield Static("Mid:")
                    yield Slider(id="marshall_plexi_super_lead_1959_mid_slider")
                with Horizontal():
                    yield Static("Treble:")
                    yield Slider(id="marshall_plexi_super_lead_1959_treble_slider")

        with Horizontal(id="volume_control"):
            yield Static("Volume:")
            yield Slider(id="volume_slider")
            yield Checkbox("Ativar Áudio", id="iniciar_checkbox")
            yield Static("Gravar:")
            yield Button("🔴", id="gravar_button")
            yield Button("⏹️", id="parar_button")
            yield ProgressBar(id="gravar_progress")

    def progress_bar_update(self, valor: float):
        if not self.app.audio.gravando:
            valor = 0.0
            return

        progress_bar = self.query_one("#gravar_progress", ProgressBar)
        progress_bar.update(valor)

    def on_button_pressed(self, event: Button.Pressed):
        match event.button.id:
            case "gravar_button":
                if event.button.label == "⏸️":
                    if self.app.audio.gravando:
                        self.app.audio.pausar_gravacao()
                        event.button.label = "▶️"
                        self.notify("Gravação pausada.")
                        return
                if not self.app.audio.gravando:
                    # TODO: adicionar algo q fica fazendo update do valor enquanto ta gravando mas n pode atrapalhar o textual que já é um loop e n pode ser bloqueado

                    self.app.audio.iniciar_gravacao()
                    self.query_one("#parar_button",
                                   Button).style.display = "block"
                    event.button.label = "⏸️"
                    self.notify("Gravação iniciada.")
                else:
                    self.app.audio.parar_gravacao()
                    event.button.label = "🔴"
                    self.query_one("#parar_button",
                                   Button).style.display = "none"
                    self.notify("Gravação parada.")

    def on_checkbox_changed(self, evento: Checkbox.Changed):
        match evento._sender.id:
            case "boss_distortion_ds1_checkbox":
                self.app.boss_distortion_ds1.ativo = evento.value
                if self.app.boss_distortion_ds1 not in self.app.audio.get_pedais():
                    self.app.audio.add_pedal(self.app.boss_distortion_ds1)
            case "iniciar_checkbox":
                if evento.value:
                    if self.app.audio.iniciar():
                        self.notify("Áudio iniciado com sucesso.")
                    else:
                        self.notify("Falha ao iniciar o áudio.")
                else:
                    if self.app.audio.parar():
                        self.notify("Áudio parado com sucesso.")
                    else:
                        self.notify("Falha ao parar o áudio.")
            case "boss_ns2_noise_suppressor_checkbox":
                self.app.boss_ns2_noise_suppressor.ativo = evento.value
                if self.app.boss_ns2_noise_suppressor not in self.app.audio.get_pedais():
                    self.app.audio.add_pedal(
                        self.app.boss_ns2_noise_suppressor)
            case "klon_centaur_checkbox":
                self.app.klon_centaur.ativo = evento.value
                if self.app.klon_centaur not in self.app.audio.get_pedais():
                    self.app.audio.add_pedal(self.app.klon_centaur)
            case "boss_ce5_chorus_checkbox":
                self.app.boss_ce5_chorus.ativo = evento.value
                if self.app.boss_ce5_chorus not in self.app.audio.get_pedais():
                    self.app.audio.add_pedal(self.app.boss_ce5_chorus)
            case "boss_dd3_delay_checkbox":
                self.app.boss_dd3_delay.ativo = evento.value
                if self.app.boss_dd3_delay not in self.app.audio.get_pedais():
                    self.app.audio.add_pedal(self.app.boss_dd3_delay)
            case "boss_rv6_reverb_checkbox":
                self.app.boss_rv6_reverb.ativo = evento.value
                if self.app.boss_rv6_reverb not in self.app.audio.get_pedais():
                    self.app.audio.add_pedal(self.app.boss_rv6_reverb)
            case "marshall_plexi_super_lead_1959_checkbox":
                self.app.marshall_plexi_super_lead_1959.ativo = evento.value
                if self.app.marshall_plexi_super_lead_1959 not in self.app.audio.get_amps():
                    self.app.audio.add_amp(
                        self.app.marshall_plexi_super_lead_1959)

    def on_select_changed(self, evento: Select.Changed):
        match evento.select.id:
            case "input_select":
                idx = evento.select.value
                self.app.audio.set_entrada(idx)
                dicionario = self.app.audio.listar_dispositivos_audio()
                nome_entrada = next(
                    (nome for i, nome in dicionario["entrada"] if i == int(idx)), "Desconhecido")
                self.app.banco.adicionar_dispositivo(nome_entrada, "entrada")
                self.notify(f"Entrada: [{idx}] {nome_entrada}")
            case "output_select":
                idx = evento.select.value
                self.app.audio.set_saida(idx)
                dicionario = self.app.audio.listar_dispositivos_audio()
                nome_saida = next(
                    (nome for i, nome in dicionario["saida"] if i == int(idx)), "Desconhecido")
                self.app.banco.adicionar_dispositivo(nome_saida, "saida")
                self.notify(f"Saída: [{idx}] {nome_saida}")

    def on_slider_changed(self, evento: Slider.Changed):
        match evento._sender.id:
            case "marshall_plexi_super_lead_1959_slider":
                self.app.marshall_plexi_super_lead_1959.set_volume(
                    evento.value)
            case "marshall_plexi_super_lead_1959_gain_slider":
                self.app.marshall_plexi_super_lead_1959.set_gain(evento.value)
            case "marshall_plexi_super_lead_1959_bass_slider":
                self.app.marshall_plexi_super_lead_1959.set_bass(evento.value)
            case "marshall_plexi_super_lead_1959_mid_slider":
                self.app.marshall_plexi_super_lead_1959.set_mid(evento.value)
            case "marshall_plexi_super_lead_1959_treble_slider":
                self.app.marshall_plexi_super_lead_1959.set_treble(
                    evento.value)
            case "boss_distortion_ds1_slider":
                self.app.boss_distortion_ds1.set_intensidade(evento.value)
            case "boss_ns2_noise_suppressor_slider":
                self.app.boss_ns2_noise_suppressor.set_intensidade(
                    evento.value)
            case "boss_ns2_noise_suppressor_decay_slider":
                self.app.boss_ns2_noise_suppressor.set_decay(evento.value)
            case "boss_distortion_ds1_tom_slider":
                self.app.boss_distortion_ds1.set_tom(evento.value)
            case "klon_centaur_slider":
                self.app.klon_centaur.set_intensidade(evento.value)
            case "klon_centaur_tom_slider":
                self.app.klon_centaur.set_tom(evento.value)
            case "volume_slider":
                self.app.audio.set_volume(evento.value)
            case "boss_ce5_chorus_rate_slider":
                self.app.boss_ce5_chorus.set_rate(evento.value)
            case "boss_ce5_chorus_depth_slider":
                self.app.boss_ce5_chorus.set_depth(evento.value)
            case "boss_ce5_chorus_mix_slider":
                self.app.boss_ce5_chorus.set_mix(evento.value)
            case "boss_dd3_delay_slider":
                self.app.boss_dd3_delay.set_intensidade(evento.value)
            case "boss_dd3_delay_feedback_slider":
                self.app.boss_dd3_delay.set_feedback(evento.value)
            case "boss_rv6_reverb_decay_slider":
                self.app.boss_rv6_reverb.set_decay(evento.value)
            case "boss_rv6_reverb_mix_slider":
                self.app.boss_rv6_reverb.set_mix(evento.value)
            case "boss_rv6_reverb_tone_slider":
                self.app.boss_rv6_reverb.set_tone(evento.value)


class App(App):
    def on_mount(self):
        self.push_screen(InicioScreen())

    BINDINGS = [
        Binding("ctrl+c", "sair", "Sair"),
    ]

    def on_action_sair(self):
        Init.salvar_pedais()
        self.banco.fechar_conexao()
        self.exit()

    SCREENS = {
        "configuracoes": ConfigScreen,
        "inicio": InicioScreen,
        "equipamentos": EquipamentosScreen
    }

    def __init__(self):
        super().__init__()
        self.audio = Init.audio
        self.boss_distortion_ds1 = Init.boss_distortion_ds12
        self.boss_ns2_noise_suppressor = Init.boss_ns2_noise_suppressor
        self.klon_centaur = Init.klon_centaur
        self.boss_ce5_chorus = Init.boss_ce5_chorus
        self.boss_dd3_delay = Init.boss_dd3_delay
        self.boss_rv6_reverb = Init.boss_rv6_reverb
        self.marshall_plexi_super_lead_1959 = Init.marshall_plexi_super_lead_1959
        self.app.banco = Init.banco
        self.app.banco.conectar()
        self.app.banco.criar_tabelas()
        self.current_screen = "inicio"

    def on_tabs_tab_activated(self, event: Tabs.TabActivated):
        match event.tabs.active:
            case "tab_inicio":
                self.switch_screen("inicio")
            case "tab_configuracoes":
                self.switch_screen("configuracoes")
            case "tab_equipamentos":
                self.switch_screen("equipamentos")

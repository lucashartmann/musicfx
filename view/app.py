from textual.app import App
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Button, Static, Select, Checkbox, Tab, Tabs
from .widgets.slider import Slider
from model import audio, pedal, pedal_distorcao, pedal_noise_gate
from database import banco
from .config import ConfigScreen
from textual import on
from textual.events import ScreenResume
from textual.screen import Screen



class InicioScreen(Screen):

    CSS_PATH = ["css/base.tcss", "css/app.tcss"]
                    
    @on(ScreenResume)
    def on_screen_resume(self, event: ScreenResume):
        self.query_one(Tabs).active = self.query_one(
            "#tab_inicio", Tab).id
        self.current_screen = "inicio"

    def on_mount(self):
        
        dicionario = self.app.audio.listar_dispositivos_audio()
        if "entrada" in dicionario.keys() and len(dicionario["entrada"]) > 0:
            self.mount(Select(((nome, indice)
                       for indice, nome in dicionario["entrada"]), id="input_select"), after=self.query_one("#input_label"))
        if "saida" in dicionario.keys() and len(dicionario["saida"]) > 0:
            self.mount(Select(((nome, indice)
                       for indice, nome in dicionario["saida"]), id="output_select"), after=self.query_one("#output_label"))

    def compose(self):
        yield Tabs(Tab("Inicio", id="tab_inicio"), Tab("Configurações", id="tab_configuracoes"), id="tabs", active="tab_inicio")
        with Horizontal(id="dispositivos"):
            yield Static("Input:", id="input_label")
            yield Static("Output:", id="output_label")

        with Horizontal(id="pedais"):

            with Container(id="pedal_distorcao"):
                yield Static("Pedal de Distorção", classes="titulo_pedal")
                yield Checkbox("Ativar", id="distorcao_checkbox")
                with Horizontal():
                    yield Static("Efeito:")
                    yield Slider(id="distorcao_slider")

            with Container(id="pedal_noise_gate"):
                yield Static("Pedal de Noise Gate", classes="titulo_pedal")
                yield Checkbox("Ativar", id="noise_gate_checkbox")
                with Horizontal():
                    yield Static("Efeito:")
                    yield Slider(id="noise_gate_slider")

        with Horizontal(id="volume_control"):
            yield Static("Volume:")
            yield Slider(id="volume_slider")
            yield Checkbox("Ativar Áudio", id="iniciar_checkbox")

    def on_checkbox_changed(self, evento: Checkbox.Changed):
        match evento._sender.id:
            case "distorcao_checkbox":
                self.app.pedal_distorcao.ativo = evento.value
                if self.app.pedal_distorcao not in self.app.audio.get_pedais():
                    self.app.audio.add_pedal(self.app.pedal_distorcao)
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
            case "noise_gate_checkbox":
                self.app.pedal_noise_gate.ativo = evento.value
                if self.app.pedal_noise_gate not in self.app.audio.get_pedais():
                    self.app.audio.add_pedal(self.app.pedal_noise_gate)

    def on_select_changed(self, evento: Select.Changed):
        match evento.select.id:
            case "input_select":
                idx = evento.select.value
                self.app.audio.set_entrada(idx)
                dicionario = self.app.audio.listar_dispositivos_audio()
                nome_entrada = next((nome for i, nome in dicionario["entrada"] if i == int(idx)), "Desconhecido")
                self.notify(f"Entrada: [{idx}] {nome_entrada}")
            case "output_select":
                idx = evento.select.value
                self.app.audio.set_saida(idx)
                dicionario = self.app.audio.listar_dispositivos_audio()
                nome_saida = next((nome for i, nome in dicionario["saida"] if i == int(idx)), "Desconhecido")
                self.notify(f"Saída: [{idx}] {nome_saida}")

    def on_slider_changed(self, evento: Slider.Changed):
        match evento._sender.id:
            case "distorcao_slider":
                print(f"Distorção: {evento.value:.2f}")
                self.app.pedal_distorcao.set_intensidade(evento.value)
            case "noise_gate_slider":
                self.app.pedal_noise_gate.set_intensidade(evento.value)
            case "volume_slider":
                print(f"Volume: {evento.value:.2f}")
                # self.app.audio.set_volume(evento.value)
                
                
class App(App):
    def on_mount(self):
        self.push_screen(InicioScreen())
        
    SCREENS = {
        "configuracoes": ConfigScreen,
        "inicio": InicioScreen
    }

    def __init__(self):
        super().__init__()
        self.audio = audio.Audio()
        self.pedal_distorcao = pedal_distorcao.Distorcao()
        self.pedal_noise_gate = pedal_noise_gate.NoiseGate()
        self.banco = banco.Banco()
        self.banco.conectar()
        self.banco.criar_tabelas()
        self.current_screen = "inicio"
        
    def on_tabs_tab_activated(self, event: Tabs.TabActivated):
        match event.tabs.active:
            case "tab_inicio":
              
                    self.switch_screen("inicio")
            case "tab_configuracoes":
        
                    self.switch_screen("configuracoes")
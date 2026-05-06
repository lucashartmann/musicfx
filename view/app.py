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
import re
import unicodedata
from time import monotonic


def sanitize_id(name: str) -> str:
    name = unicodedata.normalize('NFKD', name)
    name = name.encode('ASCII', 'ignore').decode('ASCII')
    name = name.lower().replace(" ", "_").replace("-", "_")
    name = re.sub(r'[^a-z0-9_]', '', name)
    return name


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
                        for option in self.query_one("#input_select", Select)._options:
                            if option[0] == nome:
                                self.query_one("#input_select",
                                               Select).value = option[1]
                                break

                    except Exception as e:
                        print(
                            f"Erro ao definir valor do select de entrada: {e}")
                elif tipo == "saida":
                    try:
                        for option in self.query_one("#output_select", Select)._options:
                            if option[0] == nome:
                                self.query_one("#output_select",
                                               Select).value = option[1]
                                break
                    except Exception as e:
                        print(f"Erro ao definir valor do select de saída: {e}")

        container = self.query_one("#equipamentos", Grid)
        for pedal in self.app.audio.get_pedais():
            pedal_id = sanitize_id(pedal.get_nome())
            novo_container = Container(id=pedal_id)
            container.mount(novo_container)
            novo_container.mount(
                Static(pedal.get_nome(), classes="titulo_pedal"))
            checkbox = Checkbox("Ativar", id=f"{pedal_id}_checkbox")
            checkbox.value = pedal.ativo
            novo_container.mount(checkbox)
            horizontal = Horizontal()
            novo_container.mount(horizontal)
            horizontal.mount(Static("Efeito:"))
            slider = Slider(id=f"{pedal_id}_slider")
            slider.value = pedal.get_intensidade()
            horizontal.mount(slider)
            if hasattr(pedal, 'repeat'):
                horizontal = Horizontal()
                novo_container.mount(horizontal)
                horizontal.mount(Static("Repeat:"))
                slider = Slider(id=f"{pedal_id}_repeat_slider")
                slider.value = getattr(pedal, 'repeat', 0.5)
                horizontal.mount(slider)
            if hasattr(pedal, 'feedback'):
                horizontal = Horizontal()
                novo_container.mount(horizontal)
                horizontal.mount(Static("Feedback:"))
                slider = Slider(id=f"{pedal_id}_feedback_slider")
                slider.value = getattr(pedal, 'feedback', 0.5)
                horizontal.mount(slider)
            if hasattr(pedal, 'tone') or hasattr(pedal, 'tom'):
                horizontal = Horizontal()
                novo_container.mount(horizontal)
                horizontal.mount(Static("Tone:"))
                slider = Slider(id=f"{pedal_id}_tone_slider")
                slider.value = getattr(pedal, 'tone', 0.5)
                horizontal.mount(slider)
            if hasattr(pedal, 'high'):
                horizontal = Horizontal()
                novo_container.mount(horizontal)
                horizontal.mount(Static("High:"))
                slider = Slider(id=f"{pedal_id}_high_slider")
                slider.value = getattr(pedal, 'high', 0.5)
                horizontal.mount(slider)
            if hasattr(pedal, 'low'):
                horizontal = Horizontal()
                novo_container.mount(horizontal)
                horizontal.mount(Static("Low:"))
                slider = Slider(id=f"{pedal_id}_low_slider")
                slider.value = getattr(pedal, 'low', 0.5)
                horizontal.mount(slider)
            if hasattr(pedal, 'echo'):
                horizontal = Horizontal()
                novo_container.mount(horizontal)
                horizontal.mount(Static("Echo:"))
                slider = Slider(id=f"{pedal_id}_echo_slider")
                slider.value = getattr(pedal, 'echo', 0.5)
                horizontal.mount(slider)
            if hasattr(pedal, 'time'):
                horizontal = Horizontal()
                novo_container.mount(horizontal)
                horizontal.mount(Static("Time:"))
                slider = Slider(id=f"{pedal_id}_time_slider")
                slider.value = getattr(pedal, 'time', 0.5)
                horizontal.mount(slider)
            if hasattr(pedal, 'e_level'):
                horizontal = Horizontal()
                novo_container.mount(horizontal)
                horizontal.mount(Static("Effect Level:"))
                slider = Slider(id=f"{pedal_id}_e_level_slider")
                slider.value = getattr(pedal, 'e_level', 0.5)
                horizontal.mount(slider)
            if hasattr(pedal, 'bass'):
                horizontal = Horizontal()
                novo_container.mount(horizontal)
                horizontal.mount(Static("Bass:"))
                slider = Slider(id=f"{pedal_id}_bass_slider")
                slider.value = getattr(pedal, 'bass', 0.5)
                horizontal.mount(slider)
            if hasattr(pedal, 'treble'):
                horizontal = Horizontal()
                novo_container.mount(horizontal)
                horizontal.mount(Static("Treble:"))
                slider = Slider(id=f"{pedal_id}_treble_slider")
                slider.value = getattr(pedal, 'treble', 0.5)
                horizontal.mount(slider)
            if hasattr(pedal, 'vibrato'):
                horizontal = Horizontal()
                novo_container.mount(horizontal)
                horizontal.mount(Static("Vibrato:"))
                slider = Slider(id=f"{pedal_id}_vibrato_slider")
                slider.value = getattr(pedal, 'vibrato', 0.5)
                horizontal.mount(slider)
            if hasattr(pedal, 'decay'):
                horizontal = Horizontal()
                novo_container.mount(horizontal)
                horizontal.mount(Static("Decay:"))
                slider = Slider(id=f"{pedal_id}_decay_slider")
                slider.value = getattr(pedal, 'decay', 0.5)
                horizontal.mount(slider)
            if hasattr(pedal, 'rate'):
                horizontal = Horizontal()
                novo_container.mount(horizontal)
                horizontal.mount(Static("Rate:"))
                slider = Slider(id=f"{pedal_id}_rate_slider")
                slider.value = getattr(pedal, 'rate', 0.5)
                horizontal.mount(slider)
            if hasattr(pedal, 'depth'):
                horizontal = Horizontal()
                novo_container.mount(horizontal)
                horizontal.mount(Static("Depth:"))
                slider = Slider(id=f"{pedal_id}_depth_slider")
                slider.value = getattr(pedal, 'depth', 0.5)
                horizontal.mount(slider)
            if hasattr(pedal, 'mix'):
                horizontal = Horizontal()
                novo_container.mount(horizontal)
                horizontal.mount(Static("Mix:"))
                slider = Slider(id=f"{pedal_id}_mix_slider")
                slider.value = getattr(pedal, 'mix', 0.5)
                horizontal.mount(slider)
            if hasattr(pedal, 'effect_level'):
                horizontal = Horizontal()
                novo_container.mount(horizontal)
                horizontal.mount(Static("Effect Level:"))
                slider = Slider(id=f"{pedal_id}_effect_level_slider")
                slider.value = getattr(pedal, 'effect_level', 0.5)
                horizontal.mount(slider)

        for amp in self.app.audio.get_amps():
            amp_id = sanitize_id(amp.get_nome())
            novo_container = Container(id=amp_id)
            container.mount(novo_container)
            novo_container.mount(Static(amp.get_nome(), classes="titulo_amp"))
            checkbox = Checkbox("Ativar", id=f"{amp_id}_checkbox")
            checkbox.value = amp.ativo
            novo_container.mount(checkbox)
            horizontal = Horizontal()
            novo_container.mount(horizontal)
            horizontal.mount(Static("Volume:"))
            slider = Slider(id=f"{amp_id}_volume_slider")
            slider.value = getattr(amp, 'gain', 0.5)
            horizontal.mount(slider)
            horizontal = Horizontal()
            novo_container.mount(horizontal)
            horizontal.mount(Static("Gain:"))
            slider = Slider(id=f"{amp_id}_gain_slider")
            slider.value = getattr(amp, 'gain', 0.5)
            horizontal.mount(slider)
            horizontal = Horizontal()
            novo_container.mount(horizontal)
            horizontal.mount(Static("Bass:"))
            slider = Slider(id=f"{amp_id}_bass_slider")
            slider.value = getattr(amp, 'bass', 0.5)
            horizontal.mount(slider)
            horizontal = Horizontal()
            novo_container.mount(horizontal)
            horizontal.mount(Static("Mid:"))
            slider = Slider(id=f"{amp_id}_mid_slider")
            slider.value = getattr(amp, 'mid', 0.5)
            horizontal.mount(slider)
            horizontal = Horizontal()
            novo_container.mount(horizontal)
            horizontal.mount(Static("Treble:"))
            slider = Slider(id=f"{amp_id}_treble_slider")
            slider.value = getattr(amp, 'treble', 0.5)
            horizontal.mount(slider)
            if hasattr(amp, 'vibrato'):
                horizontal = Horizontal()
                novo_container.mount(horizontal)
                horizontal.mount(Static("Vibrato:"))
                slider = Slider(id=f"{amp_id}_vibrato_slider")
                slider.value = getattr(amp, 'vibrato', 0.5)
                horizontal.mount(slider)
            if hasattr(amp, 'presence'):
                horizontal = Horizontal()
                novo_container.mount(horizontal)
                horizontal.mount(Static("Presence:"))
                slider = Slider(id=f"{amp_id}_presence_slider")
                slider.value = getattr(amp, 'presence', 0.5)
                horizontal.mount(slider)

        self.set_interval(0.1, self._atualizar_progresso_gravacao)

    def compose(self):
        yield Tabs(Tab("Inicio", id="tab_inicio"), Tab("Configurações", id="tab_configuracoes"), Tab("Equipamentos", id="tab_equipamentos"), id="tabs", active="tab_inicio")
        with Horizontal(id="dispositivos"):
            yield Static("Input:", id="input_label")
            yield Static("Output:", id="output_label")

        yield Grid(id="equipamentos")

        with Horizontal(id="volume_control"):
            yield Static("Volume:")
            yield Slider(id="volume_slider")
            yield Checkbox("Ativar Áudio", id="iniciar_checkbox")
            yield Button("Gravar", id="gravar_button", flat=True)
            yield Button("Parar", id="parar_button")
            yield ProgressBar(id="gravar_progress")

    def progress_bar_update(self, valor: float):
        progress_bar = self.query_one("#gravar_progress", ProgressBar)
        if not self.app.audio.gravando:
            progress_bar.update(total=100, progress=0.0)
            return

        progress_bar.update(total=100, progress=valor)

    def _atualizar_progresso_gravacao(self):
        if self.app.audio.gravando:
            valor = (monotonic() * 25) % 100
        else:
            valor = 0.0
        self.progress_bar_update(valor)

    def on_button_pressed(self, event: Button.Pressed):
        match event.button.id:
            case "gravar_button":
                if event.button.label == "Pausar":
                    if self.app.audio.gravando:
                        self.app.audio.pausar_gravacao()
                        event.button.label = "Continuar"
                        self.notify("Gravação pausada.")
                        return
                if event.button.label == "Continuar" and not self.app.audio.gravando:
                    if self.app.audio.iniciar_gravacao():
                        self.query_one("#parar_button",
                                       Button).styles.display = "block"
                        event.button.label = "Pausar"
                        self.notify("Gravação retomada.")
                        return
                if not self.app.audio.gravando:
                    if self.app.audio.iniciar_gravacao():
                        self.query_one("#parar_button",
                                       Button).styles.display = "block"
                        event.button.label = "Pausar"

                    self.notify("Gravação iniciada.")

            case "parar_button":
                if self.app.audio.gravacao_ativa():
                    self.app.audio.parar_gravacao()
                    self.query_one("#gravar_button", Button).label = "Gravar"
                    event.button.styles.display = "none"
                    self.notify("Gravação parada.")

    def on_checkbox_changed(self, evento: Checkbox.Changed):
        match evento._sender.id:

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

            case _:
                id = evento._sender.id
                if id.endswith("_checkbox"):
                    base_id = id[:-9]
                    pedal = next((p for p in self.app.audio.get_pedais(
                    ) if sanitize_id(p.get_nome()) == base_id), None)
                    if pedal:
                        pedal.ativo = evento.value
                        if pedal not in self.app.audio.get_pedais():
                            self.app.audio.add_pedal(pedal)
                    else:
                        amp = next((a for a in self.app.audio.get_amps(
                        ) if sanitize_id(a.get_nome()) == base_id), None)
                        if amp:
                            amp.ativo = evento.value
                            if amp not in self.app.audio.get_amps():
                                self.app.audio.add_amp(amp)

    def on_select_changed(self, evento: Select.Changed):
        match evento.select.id:
            case "input_select":
                idx = evento.select.value
                self.app.audio.set_entrada(idx)
                dicionario = self.app.audio.listar_dispositivos_audio()
                nome_entrada = ""
                for option in self.query_one("#input_select", Select)._options:
                    if option[1] == idx:
                        nome_entrada = option[0]
                        break
                if nome_entrada:
                    self.app.banco.adicionar_dispositivo(
                        nome_entrada, "entrada")
                else:
                    self.app.banco.adicionar_dispositivo("", "entrada")
                self.notify(f"Entrada: [{idx}] {nome_entrada}")
            case "output_select":
                idx = evento.select.value
                self.app.audio.set_saida(idx)
                dicionario = self.app.audio.listar_dispositivos_audio()
                nome_saida = ""
                for option in self.query_one("#output_select", Select)._options:
                    if option[1] == idx:
                        nome_saida = option[0]
                        break
                if nome_saida:
                    self.app.banco.adicionar_dispositivo(nome_saida, "saida")
                else:
                    self.app.banco.adicionar_dispositivo("", "saida")
                self.notify(f"Saída: [{idx}] {nome_saida}")

    def on_slider_changed(self, evento: Slider.Changed):
        match evento._sender.id:

            case "volume_slider":
                self.app.audio.set_volume(evento.value)

            case _:
                id = evento._sender.id
                if id.endswith("_slider"):
                    base_id = id[:-7]
                    pedal = next((p for p in self.app.audio.get_pedais(
                    ) if sanitize_id(p.get_nome()) == base_id), None)
                    if pedal:
                        pedal.set_intensidade(evento.value)
                        if id.endswith("_repeat_slider"):
                            pedal.set_repeat(evento.value)
                        elif id.endswith("_volume_slider"):
                            pedal.set_volume(evento.value)
                        elif id.endswith("_gain_slider"):
                            pedal.set_gain(evento.value)
                        elif id.endswith("_feedback_slider"):
                            pedal.set_feedback(evento.value)
                        elif id.endswith("_tone_slider"):
                            try:
                                pedal.set_tone(evento.value)
                            except AttributeError:
                                pedal.set_tom(evento.value)
                        elif id.endswith("_high_slider"):
                            pedal.set_high(evento.value)
                        elif id.endswith("_low_slider"):
                            pedal.set_low(evento.value)
                        elif id.endswith("_echo_slider"):
                            pedal.set_echo(evento.value)
                        elif id.endswith("_time_slider"):
                            pedal.set_time(evento.value)
                        elif id.endswith("_e_level_slider"):
                            pedal.set_e_level(evento.value)
                        elif id.endswith("_bass_slider"):
                            pedal.set_bass(evento.value)
                        elif id.endswith("_treble_slider"):
                            pedal.set_treble(evento.value)
                        elif id.endswith("_vibrato_slider"):
                            pedal.set_vibrato(evento.value)
                        elif id.endswith("_decay_slider"):
                            pedal.set_decay(evento.value)
                        elif id.endswith("_rate_slider"):
                            pedal.set_rate(evento.value)
                        elif id.endswith("_depth_slider"):
                            pedal.set_depth(evento.value)
                        elif id.endswith("_mix_slider"):
                            pedal.set_mix(evento.value)
                        elif id.endswith("_effect_level_slider"):
                            pedal.set_effect_level(evento.value)
                    else:
                        amp = next((a for a in self.app.audio.get_amps(
                        ) if sanitize_id(a.get_nome()) == base_id), None)
                        if amp:
                            if id.endswith("_volume_slider"):
                                amp.set_volume(evento.value)
                            elif id.endswith("_gain_slider"):
                                amp.set_gain(evento.value)
                            elif id.endswith("_bass_slider"):
                                amp.set_bass(evento.value)
                            elif id.endswith("_mid_slider"):
                                amp.set_mid(evento.value)
                            elif id.endswith("_treble_slider"):
                                amp.set_treble(evento.value)
                            elif id.endswith("_vibrato_slider"):
                                amp.set_vibrato(evento.value)
                            elif id.endswith("_presence_slider"):
                                amp.set_presence(evento.value)


class App(App):
    def on_mount(self):
        self.push_screen(InicioScreen())

    BINDINGS = [
        Binding("ctrl+q", "sair", "Sair"),
    ]

    def salvar_pedais(self):

        for pedal in self.audio.get_pedais():
            try:
                nome = pedal.get_nome()
            except Exception:
                nome = getattr(pedal, "nome", None)
            if not nome:
                continue
            if not self.banco.pedal_nome_existe(nome):
                self.banco.adicionar_pedal(pedal)
            else:
                self.banco.atualizar_pedal(pedal)

        try:
            existing_amps = {a.get_nome() for a in self.banco.listar_amps()}
        except Exception:
            existing_amps = set()
        for amp in self.audio.get_amps():
            try:
                nome = amp.get_nome()
            except Exception:
                nome = getattr(amp, "nome", None)
            if not nome:
                continue
            if nome not in existing_amps:
                self.banco.adicionar_amp(amp)

    def action_sair(self):

        self.salvar_pedais()
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
        self.banco = Init.banco
        self.banco.conectar()
        self.banco.criar_tabelas()
        self.current_screen = "inicio"

    def on_tabs_tab_activated(self, event: Tabs.TabActivated):
        match event.tabs.active:
            case "tab_inicio":
                self.switch_screen("inicio")
            case "tab_configuracoes":
                self.switch_screen("configuracoes")
            case "tab_equipamentos":
                self.switch_screen("equipamentos")

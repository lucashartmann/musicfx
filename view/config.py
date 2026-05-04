import sys
from textual.screen import Screen
from textual.widgets import RichLog, Tabs, Tab
from textual.app import App, ComposeResult


class PrintCapture:
    def __init__(self, log_widget: RichLog):
        self._log = log_widget
        self._original = sys.stdout

    def write(self, text: str):
        if text.strip():
            self._log.write(text)

    def flush(self):
        pass

    def restore(self):
        sys.stdout = self._original


class ConfigScreen(Screen):
    
    CSS_PATH = ["css/base.tcss", "css/config.tcss"]

    def compose(self) -> ComposeResult:
        yield Tabs(
            Tab("Inicio", id="tab_inicio"),
            Tab("Configurações", id="tab_configuracoes"),
            id="tabs"
        )
        yield RichLog(id="log")

    def on_mount(self) -> None:
        log = self.query_one(RichLog)
        self._capture = PrintCapture(log)
        sys.stdout = self._capture 

    def on_screen_resume(self):
        self.query_one(Tabs).active = self.query_one(
            "#tab_configuracoes", Tab).id
        self.app.current_screen = "configuracoes"

    def on_unmount(self) -> None:
        if hasattr(self, "_capture"):
            self._capture.restore() 

    def mostrar_prints(self, texto: str) -> None:
        self.query_one(RichLog).write(texto)


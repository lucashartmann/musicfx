from textual.screen import Screen
from textual.containers import Grid, Container, Vertical, Horizontal
from textual.widgets import Static, Button, Tree, Tabs, Tab
from textual import events
from textual import on

class EquipamentosScreen(Screen):
    
    CSS_PATH = ["css/base.tcss", "css/equipamentos.tcss"]
    
    @on(events.ScreenResume)
    def on_screen_resume(self, event: events.ScreenResume):
        self.query_one(Tabs).active = self.query_one(
            "#tab_equipamentos", Tab).id
    
    def compose(self):
        yield Tabs(Tab("Inicio", id="tab_inicio"), Tab("Configurações", id="tab_configuracoes"), Tab("Equipamentos", id="tab_equipamentos"), id="tabs", active="tab_equipamentos")
        with Horizontal():
            yield Tree(label="Equipamentos", id="side-bar", data={"Pedais": {}, "Amps": {}})
            with Grid():
                yield Container(classes="equipamento")
                yield Container(classes="equipamento")
                yield Container(classes="equipamento")
                yield Container(classes="equipamento")
                
    def on_mount(self):
        self.query_one("#side-bar").mount(Static("Pedais", classes="sidebar-title"))
        
    def on_click(self, event: events.Click):
        if isinstance(event.widget, Static):
            if event.widget.content == "Pedais":
                self.query_one("#side-bar").data = {"Pedais": {"BOSS CE-5 Chorus": {}, "BOSS NS-2 Noise Suppressor": {}}, "Amps": {}}
            elif event.widget.content == "Amps":
                self.query_one("#side-bar").data = {"Pedais": {}, "Amps": {"Marshall DSL40CR": {}, "Fender Blues Junior": {}}}

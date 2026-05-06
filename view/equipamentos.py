from textual.screen import Screen
from textual.containers import Grid, Container, Vertical, Horizontal
from textual.widgets import Static, Button, Tree, Tabs, Tab, Input
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
        yield Input(placeholder="Pesquisar...", id="search-bar")
        with Horizontal():
            tree = Tree(label="Equipamentos", id="side-bar")
            tree.root.expand()
            tree.root.add("Pedais", expand=True)
            tree.root.add("Amps", expand=True)
            yield tree
            yield Grid()
              
                
    def on_mount(self):
        self.query_one("#side-bar").mount(Static("Pedais", classes="sidebar-title"))
        tree = self.query_one("#side-bar", Tree)
        
        pedais = self.app.audio.get_pedais()
        for pedal in pedais:
                    tree.root.children[0].add_leaf(label=pedal.get_nome())
           
        amps = self.app.audio.get_amps()
        for amp in amps:
                    tree.root.children[1].add_leaf(label=amp.get_nome())
        for pedal in self.app.audio.get_pedais():
            self.query_one(Grid).mount(Container(Static(pedal.get_nome(), classes="equipamento-nome")))
        for amp in self.app.audio.get_amps():
            self.query_one(Grid).mount(Container(Static(amp.get_nome(), classes="equipamento-nome")))

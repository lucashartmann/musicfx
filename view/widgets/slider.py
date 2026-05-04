from textual.widget import Widget
from textual.reactive import reactive
from textual.message import Message
from textual.events import MouseDown, MouseMove
from rich.text import Text

class Slider(Widget):

    value = reactive(0.5)

    def render(self):
        width = self.size.width
        pos = int(self.value * (width - 1))

        bar = ["─"] * width
        bar[pos] = "●"

        return Text("".join(bar))

    def on_mouse_down(self, event: MouseDown):
        self.set_value_from_x(event.x)

    def on_mouse_move(self, event: MouseMove):
        if event.button:
            self.set_value_from_x(event.x)

    def set_value_from_x(self, x):
        width = self.size.width
        self.value = min(max(x / width, 0), 1)

    class Changed(Message):
        def __init__(self, sender, value: float):
            self.value = value
            super().__init__()

    def watch_value(self, value: float):
        self.post_message(self.Changed(self, value))
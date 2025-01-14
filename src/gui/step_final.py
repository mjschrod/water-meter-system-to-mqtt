import dataclasses
import json
from typing import Callable

from nicegui import ui

from callbacks import Callbacks
from configuration import Config

from .step_base import BaseStep


class FinalStep(BaseStep):
    def __init__(
        self,
        name: str,
        callbacks: Callbacks,
        set_image_callback: Callable[[str], None],
        save_refs_func: Callable[[], None],
        spinner=None,
    ) -> None:
        super().__init__(
            name,
            set_image_callback=set_image_callback,
            spinner=spinner,
        )
        self.save_refs_func = save_refs_func
        self.callbacks = callbacks
        self.editor: ui.textarea

    def set_config(self, config: Config) -> None:
        self.editor.value = config.save_to_string()

    def _save_config(self) -> None:
        if self._syntax_check() is True:
            self.save_refs_func()
            self.callbacks.save_config_file(self.editor.value)
            self.new_config_saved = True
            ui.notify("Config saved", type="positive")
        self.txt = self.editor.value

    def _show_config(self) -> None:
        try:
            config = Config()
            config.load_from_string(self.editor.value)
            j = json.dumps(dataclasses.asdict(config), indent=4)
            with ui.dialog().classes("w-full w-screen") as dialog:
                with ui.card().classes("bg-gray w-screen"):
                    ui.label("Config in JSON format:")
                    ui.code(j, language="json").classes("w-full")
            dialog.open()
        except Exception as e:
            ui.notify(f"Syntax error: {e}", type="negative")

    def _use_config(self) -> None:
        self.callbacks.use_config()
        self.new_config_saved = False
        ui.notify("Config taken in use", type="positive")

    def _syntax_check(self) -> bool:
        try:
            config = Config()
            config.load_from_string(self.editor.value)
            ui.notify("Syntax is correct", type="positive")
            return True
        except Exception as e:
            ui.notify(f"Syntax error: {e}", type="negative")
            return False

    async def show(self, stepper, first_step=False, last_step=False) -> None:
        with ui.step(self.name):
            with ui.row():
                ui.button(icon="verified", on_click=self._syntax_check).tooltip(
                    "Check syntax"
                )
                self.button_save = ui.button(
                    icon="save", on_click=self._save_config
                ).tooltip("Save config to file")
                self.button_use_config = ui.button(
                    icon="sym_s_reopen_window",
                    on_click=self._use_config,
                ).tooltip("Take config in use")

                ui.button(icon="preview", on_click=self._show_config).tooltip(
                    "Show parsed config"
                )
            ui.separator()
            self.editor = (
                ui.textarea().classes("w-full font-mono").props("autoResize rows=20")
            )

            super().add_navigator(stepper, first_step, last_step)

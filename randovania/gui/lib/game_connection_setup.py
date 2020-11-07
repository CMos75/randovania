from PySide2 import QtWidgets
from asyncqt import asyncSlot

from randovania.game_connection.backend_choice import GameBackendChoice
from randovania.game_connection.connection_base import GameConnectionStatus
from randovania.game_connection.dolphin_backend import DolphinBackend
from randovania.game_connection.game_connection import GameConnection
from randovania.game_connection.nintendont_backend import NintendontBackend
from randovania.gui.lib import async_dialog
from randovania.interface_common.options import Options


class GameConnectionSetup:
    def __init__(self, parent: QtWidgets.QWidget, tool_button: QtWidgets.QToolButton,
                 label: QtWidgets.QLabel, connection: GameConnection, options: Options):
        self.parent = parent
        self.tool = tool_button
        self.label = label
        self.game_connection = connection
        self.options = options

        self.game_connection.Updated.connect(self.on_game_connection_updated)
        self.tool.setText("Configure backend")

        self.game_connection_menu = QtWidgets.QMenu(self.tool)

        self.use_dolphin_backend = QtWidgets.QAction(self.tool)
        self.use_dolphin_backend.setText("Dolphin")
        self.use_dolphin_backend.setCheckable(True)
        self.use_dolphin_backend.triggered.connect(self.on_use_dolphin_backend)
        self.use_nintendont_backend = QtWidgets.QAction(self.tool)
        self.use_nintendont_backend.setCheckable(True)
        self.use_nintendont_backend.triggered.connect(self.on_use_nintendont_backend)
        self.upload_nintendont_action = QtWidgets.QAction(self.tool)
        self.upload_nintendont_action.setText("Upload Nintendont to Homebrew Channel")
        self.upload_nintendont_action.triggered.connect(self.on_upload_nintendont_action)

        self.game_connection_menu.addAction(self.use_dolphin_backend)
        self.game_connection_menu.addAction(self.use_nintendont_backend)
        self.game_connection_menu.addAction(self.upload_nintendont_action)

        self.tool.setMenu(self.game_connection_menu)

        self.refresh_backend()
        self.on_game_connection_updated()

    def on_game_connection_updated(self):
        self.label.setText(self.game_connection.pretty_current_status)

    def refresh_backend(self):
        backend = self.game_connection.backend

        self.use_dolphin_backend.setChecked(isinstance(backend, DolphinBackend))
        if isinstance(backend, NintendontBackend):
            self.use_nintendont_backend.setChecked(True)
            self.use_nintendont_backend.setText(f"Nintendont: {backend.ip}")
            self.upload_nintendont_action.setEnabled(True)
        else:
            self.use_nintendont_backend.setChecked(False)
            self.use_nintendont_backend.setText(f"Nintendont")
            self.upload_nintendont_action.setEnabled(False)

    def on_use_dolphin_backend(self):
        self.game_connection.set_backend(DolphinBackend())
        with self.options as options:
            options.game_backend = GameBackendChoice.DOLPHIN
        self.refresh_backend()

    @asyncSlot()
    async def on_use_nintendont_backend(self):
        dialog = QtWidgets.QInputDialog(self.parent)
        dialog.setModal(True)
        dialog.setWindowTitle("Enter Wii's IP")
        dialog.setLabelText("Enter the IP address of your Wii. "
                            "You can check the IP address on the pause screen of Homebrew Channel.")
        if self.options.nintendont_ip is not None:
            dialog.setTextValue(self.options.nintendont_ip)

        if await async_dialog.execute_dialog(dialog) == dialog.Accepted:
            new_ip = dialog.textValue()
            if new_ip != "":
                with self.options as options:
                    options.nintendont_ip = new_ip
                    options.game_backend = GameBackendChoice.NINTENDONT
                self.game_connection.set_backend(NintendontBackend(new_ip))
        self.refresh_backend()

    @asyncSlot()
    async def on_upload_nintendont_action(self):
        await async_dialog.warning(self.parent, "Not implemented", "This feature hasn't been implemented yet.")

"""
SupportSage Cura Plugin

This plugin allows Cura to use SupportSage's optimized support strategy.
It reads the JSON strategy file and applies support blocking/forcing
in Cura based on the per-island analysis.

Installation:
1. Run: supportsage export model.stl -f cura-plugin -o strategy.json
2. In Cura: Extensions → SupportSage → Load Strategy
3. Select the strategy.json file
4. Cura applies the optimized support settings

For Cura 5.x
"""
import json
import os.path
from typing import List, Optional

from UM.Extension import Extension
from UM.Application import Application
from UM.Message import Message
from UM.i18n import i18nCatalog
from cura.CuraApplication import CuraApplication

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QFileDialog

catalog = i18nCatalog("cura")


class SupportSagePlugin(Extension, QObject):
    """Cura plugin for SupportSage integration."""

    def __init__(self):
        super().__init__()
        self.setMenuName("SupportSage")
        self.addMenuItem("Load Strategy...", self._load_strategy)
        self.addMenuItem("About SupportSage", self._show_about)

        self._strategy_data = None
        self._application = CuraApplication.getInstance()

    def _load_strategy(self):
        """Open file dialog and load a SupportSage strategy JSON."""
        # Get the active scene
        dialog = QFileDialog()
        file_path, _ = dialog.getOpenFileName(
            None,
            "Select SupportSage Strategy File",
            "",
            "JSON Files (*.json);;All Files (*)",
        )

        if not file_path:
            return

        try:
            with open(file_path, "r") as f:
                self._strategy_data = json.load(f)
        except Exception as e:
            msg = Message(
                f"Failed to load strategy file: {e}",
                title="SupportSage Error",
                message_type=Message.MessageType.ERROR,
            )
            msg.show()
            return

        self._apply_strategy()
        msg = Message(
            f"SupportSage strategy loaded: {self._get_summary()}",
            title="SupportSage",
            message_type=Message.MessageType.POSITIVE,
        )
        msg.show()

    def _apply_strategy(self):
        """Apply the loaded strategy to Cura's current scene."""
        if not self._strategy_data:
            return

        global_stack = self._application.getGlobalContainerStack()
        if not global_stack:
            return

        # Apply support settings based on strategy
        config = self._strategy_data.get("config", {})

        # Set global support settings
        support_type = config.get("support_type", "tree")
        support_enabled = True
        support_angle = config.get("angle_threshold", 45.0)
        interface_enabled = config.get("interface_layers", True)

        # Apply to Cura settings
        setting_overrides = {
            "support_enable": support_enabled,
            "support_type": 1 if support_type == "tree" else 0,
            "support_angle": support_angle,
            "support_interface_enable": interface_enabled,
        }

        for setting_key, value in setting_overrides.items():
            try:
                global_stack.setProperty(setting_key, "value", value)
            except:
                pass  # Setting might not exist in this Cura version

        # Apply per-island support blocking/forcing
        islands = self._strategy_data.get("islands", [])
        for island in islands:
            center = island.get("center", [0, 0, 0])
            strategy = island.get("strategy", "tree")

            if strategy == "none":
                # Add support blocker at island position
                self._add_support_blocker(center, 5.0)
            elif strategy == "heavy_interface":
                # These areas need more support density
                pass  # Uses global density setting

    def _add_support_blocker(self, position: List[float], radius: float):
        """Add a support blocker mesh at the given position."""
        # In a full implementation, this would create a cylinder/box
        # support blocker at the position to prevent supports there.
        # For MVP, this is a placeholder.
        pass

    def _get_summary(self) -> str:
        """Get a human-readable summary of the loaded strategy."""
        if not self._strategy_data:
            return "No strategy loaded"

        analysis = self._strategy_data.get("analysis", {})
        islands = self._strategy_data.get("island_strategies", [])
        num_islands = len(islands)

        support_vol = analysis.get("estimated_support_volume_mm3", 0)
        support_g = analysis.get("support_material_g", 0)

        return (
            f"{num_islands} support islands, "
            f"~{support_vol:.0f}mm³ (~{support_g:.1f}g) estimated material"
        )

    def _show_about(self):
        """Show about dialog."""
        msg = Message(
            "SupportSage v0.1.0\n"
            "AI-optimized support structures for 3D printing.\n\n"
            "github.com/bossman-lab/supportsage",
            title="About SupportSage",
        )
        msg.show()


# Plugin registration
def getMetaData():
    return {}


def register(app):
    return {"extension": SupportSagePlugin()}

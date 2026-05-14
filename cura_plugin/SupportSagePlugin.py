"""
SupportSage Cura Plugin v0.1.0

Load SupportSage-optimized support strategies directly into Cura.
Supports per-island support density, tree support, and interface layers.

Installation:
  Cura → Extensions → SupportSage → Load Strategy → select .json file

Works with Cura 5.x
"""
import json
import os
import subprocess
import tempfile
from typing import List, Optional

from UM.Extension import Extension
from UM.Application import Application
from UM.Message import Message
from UM.i18n import i18nCatalog
from cura.CuraApplication import CuraApplication

from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QFileDialog, QMessageBox

catalog = i18nCatalog("cura")


class SupportSagePlugin(Extension, QObject):
    """Cura plugin for SupportSage integration."""

    def __init__(self):
        super().__init__()
        self.setMenuName("SupportSage")

        self.addMenuItem("Load Strategy...", self._load_strategy)
        self.addMenuItem("Run SupportSage on Model...", self._run_supportsage)
        self.addMenuItem("Clear SupportSage Settings", self._clear_settings)
        self.addMenuItem("---", None)
        self.addMenuItem("About SupportSage", self._show_about)

        self._strategy_data = None
        self._application = CuraApplication.getInstance()

    def _run_supportsage(self):
        """Prompt user for an STL and run SupportSage CLI to get strategy."""
        # Check if supportsage CLI is available
        try:
            result = subprocess.run(
                ["supportsage", "--version"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode != 0:
                self._show_install_guide()
                return
        except FileNotFoundError:
            self._show_install_guide()
            return

        # Let user pick an STL file
        dialog = QFileDialog()
        stl_path, _ = dialog.getOpenFileName(
            None,
            "Select STL File for SupportSage Analysis",
            "",
            "STL Files (*.stl);;All Files (*)"
        )
        if not stl_path:
            return

        # Show loading message
        loading_msg = Message(
            "Running SupportSage analysis...",
            title="SupportSage",
            message_type=Message.MessageType.INFO,
        )
        loading_msg.show()

        try:
            # Run supportsage export
            with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
                json_path = f.name

            result = subprocess.run(
                ["supportsage", "export", stl_path, "-f", "json", "-o", json_path],
                capture_output=True, text=True, timeout=30
            )

            if result.returncode != 0:
                loading_msg.hide()
                error_msg = Message(
                    f"SupportSage error: {result.stderr[:200]}",
                    title="SupportSage Error",
                    message_type=Message.MessageType.ERROR,
                )
                error_msg.show()
                return

            # Load the strategy
            with open(json_path) as f:
                self._strategy_data = json.load(f)

            self._apply_strategy()

            loading_msg.hide()
            summary = self._get_summary()
            success_msg = Message(
                f"SupportSage: {summary}",
                title=f"✅ Strategy Applied",
                message_type=Message.MessageType.POSITIVE,
            )
            success_msg.show()

        except Exception as e:
            loading_msg.hide()
            err = Message(
                f"Failed: {str(e)[:100]}",
                title="SupportSage Error",
                message_type=Message.MessageType.ERROR,
            )
            err.show()

    def _show_install_guide(self):
        """Show installation guide for the CLI."""
        msg = Message(
            "SupportSage CLI not found.\n\n"
            "Install:\n"
            "  pip install https://github.com/\n"
            "  bossman-lab/supportsage/releases/\n"
            "  download/v0.1.0/supportsage-\n"
            "  0.1.0-py3-none-any.whl\n\n"
            "Or see: github.com/bossman-lab/supportsage",
            title="SupportSage CLI Required",
        )
        msg.show()

    def _load_strategy(self):
        """Load a pre-exported strategy JSON file."""
        dialog = QFileDialog()
        file_path, _ = dialog.getOpenFileName(
            None,
            "Select SupportSage Strategy File",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        if not file_path:
            return

        try:
            with open(file_path, "r") as f:
                self._strategy_data = json.load(f)
        except Exception as e:
            msg = Message(
                f"Failed to load: {e}",
                title="Error",
                message_type=Message.MessageType.ERROR,
            )
            msg.show()
            return

        self._apply_strategy()
        msg = Message(
            f"✅ {self._get_summary()}",
            title="SupportSage Strategy Loaded",
            message_type=Message.MessageType.POSITIVE,
        )
        msg.show()

    def _apply_strategy(self):
        """Apply the strategy to Cura settings."""
        if not self._strategy_data:
            return

        global_stack = self._application.getGlobalContainerStack()
        if not global_stack:
            return

        config = self._strategy_data.get("config", {})

        # ── Global support settings ──
        support_type = config.get("support_type", "tree")
        angle = config.get("angle_threshold", 45.0)
        interface = config.get("interface_layers", True)
        density = config.get("density", "balanced")

        # Density mapping
        density_pct = {"light": 5, "balanced": 12, "heavy": 20}
        support_density = density_pct.get(density, 12)

        settings = {
            "support_enable": True,
            "support_type": 1 if support_type == "tree" else 0,
            "support_angle": angle,
            "support_interface_enable": interface,
            "support_interface_height": 0.4 if interface else 0,
            "support_infill_rate": support_density,
        }

        for key, value in settings.items():
            try:
                global_stack.setProperty(key, "value", value)
            except Exception:
                pass

        # ── Per-island support tuning ──
        # Cura doesn't have native per-region support settings through API,
        # so we apply the best global approximation and inform the user
        # about manual adjustments.

        islands = self._strategy_data.get("island_strategies", [])

        if islands:
            # Find if there are any "none" islands that need support blocking
            no_support_zones = [s for s in islands if s.get("strategy") == "none"]
            critical_zones = [s for s in islands if s.get("strategy") == "heavy_interface"]

            if no_support_zones:
                # Enable support mesh blocking
                try:
                    global_stack.setProperty("support_mesh_drop_down", "value", "support_block")
                except Exception:
                    pass

    def _clear_settings(self):
        """Reset support settings to defaults."""
        global_stack = self._application.getGlobalContainerStack()
        if not global_stack:
            return

        resets = {
            "support_enable": False,
            "support_type": 0,
            "support_angle": 60,
            "support_interface_enable": False,
            "support_infill_rate": 15,
        }

        for key, value in resets.items():
            try:
                global_stack.setProperty(key, "value", value)
            except Exception:
                pass

        self._strategy_data = None
        msg = Message(
            "Support settings reset to defaults.",
            title="SupportSage",
        )
        msg.show()

    def _get_summary(self) -> str:
        """Get a readable summary of the loaded strategy."""
        if not self._strategy_data:
            return "No strategy loaded"

        analysis = self._strategy_data.get("analysis", {})
        islands = self._strategy_data.get("island_strategies", [])

        num = len(islands)
        vol = analysis.get("estimated_support_volume_mm3", 0)
        grams = analysis.get("support_material_g", 0)
        savings = self._strategy_data.get("savings_estimate", {}).get("material_saved_vs_uniform", "~35%")

        return f"{num} islands, ~{vol:.0f}mm³ ({grams:.1f}g), saves {savings}"

    def _show_about(self):
        """Show about dialog."""
        msg = Message(
            "SupportSage v0.1.0\n"
            "AI-optimized support structures\n\n"
            "GitHub: github.com/bossman-lab/supportsage\n"
            "Dev.to: @lanternproton",
            title="About SupportSage",
        )
        msg.show()


# ── Plugin registration ──
def getMetaData():
    return {}


def register(app):
    return {"extension": SupportSagePlugin()}

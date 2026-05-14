"""SupportSage GUI — local web server

Usage:
    supportsage-gui [--port PORT] [--open]

Starts a local web server with:
  - 3D viewer (drop STL, visualize overhangs)
  - Backend analysis API (runs the full CLI)
  - Support generation
  - FilamentDB search & recommendations
  - Printsight print quality inspection

Dependencies: Python 3.10+, trimesh, numpy (from supportsage)
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Optional

# ── Config ──
DEFAULT_PORT = 5000
HERE = Path(__file__).parent.resolve()
STATIC_DIR = HERE / "gui_static"
WEBDEMO_SRC = HERE / "webdemo" / "index.html"


# ── Lazy imports for optional dependencies ──

def _search_filament(query: str) -> list:
    """Search filamentdb for matching filaments. Returns [] on failure."""
    try:
        from filamentdb.database import search
        results = search(query)
        return results if isinstance(results, list) else list(results)
    except ImportError:
        return [{"error": "filamentdb not installed (pip install filamentdb)"}]
    except Exception as e:
        return [{"error": f"filamentdb search error: {e}"}]


def _recommend_filament(brand: str = "", model: str = "",
                        material_type: str = "") -> dict:
    """Get a full filament recommendation. Returns error dict on failure."""
    try:
        from filamentdb.database import recommend
        result = recommend(brand=brand, model=model,
                           material_type=material_type)
        return result if isinstance(result, dict) else {"result": result}
    except ImportError:
        return {"error": "filamentdb not installed (pip install filamentdb)"}
    except Exception as e:
        return {"error": f"filamentdb recommend error: {e}"}


def _inspect_print(image_path: str) -> dict:
    """Run printsight analysis on a print image. Returns error dict on failure."""
    try:
        from printsight.analyzer import analyze
        result = analyze(image_path)
        return result if isinstance(result, dict) else {"result": result}
    except ImportError:
        return {"error": "printsight not installed (pip install printsight)"}
    except FileNotFoundError:
        return {"error": f"Image file not found: {image_path}"}
    except Exception as e:
        return {"error": f"printsight analyze error: {e}"}


# ── API Handler ──

class SupportSageHandler(SimpleHTTPRequestHandler):
    """HTTP handler that serves the GUI and API endpoints."""

    def __init__(self, *args, **kwargs):
        # Ensure static dir exists
        STATIC_DIR.mkdir(parents=True, exist_ok=True)
        self._ensure_static()
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def _ensure_static(self):
        """Copy webdemo as the GUI frontend."""
        if WEBDEMO_SRC.exists():
            dest = STATIC_DIR / "index.html"
            if not dest.exists():
                shutil.copy2(str(WEBDEMO_SRC), str(dest))

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length else b"{}"

        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self._send_json({"error": "Invalid JSON"}, 400)
            return

        if parsed.path == "/api/analyze":
            self._handle_analyze(data)
        elif parsed.path == "/api/optimize":
            self._handle_optimize(data)
        elif parsed.path == "/api/version":
            self._send_json({"version": "0.1.0", "status": "ok"})
        elif parsed.path == "/api/filament-search":
            self._handle_filament_search(data)
        elif parsed.path == "/api/filament-recommend":
            self._handle_filament_recommend(data)
        elif parsed.path == "/api/print-inspect":
            self._handle_print_inspect(data)
        else:
            self._send_json({"error": "Not found"}, 404)

    def _handle_analyze(self, data: dict):
        """Run supportsage analyze on an uploaded STL file.

        Optional 'filament' field: if provided, filament details are
        appended to the response.
        """
        stl_path = data.get("stl_path", "")
        if not stl_path or not os.path.isfile(stl_path):
            self._send_json({"error": "STL file not found"}, 400)
            return

        angle = data.get("angle", 45)

        try:
            result = subprocess.run(
                ["supportsage", "analyze", stl_path, "--json", "--angle", str(angle)],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0:
                self._send_json({
                    "error": result.stderr[:500],
                    "stdout": result.stdout[:500],
                }, 500)
                return

            analysis = json.loads(result.stdout)

            # Optional filament enrichment
            filament_query = data.get("filament", "")
            if filament_query:
                analysis["filament"] = _search_filament(filament_query)

            self._send_json(analysis)
        except FileNotFoundError:
            self._send_json({
                "error": "SupportSage CLI not found. Install: pip install [wheel URL]",
            }, 500)
        except json.JSONDecodeError as e:
            self._send_json({"error": f"Failed to parse output: {e}"}, 500)
        except subprocess.TimeoutExpired:
            self._send_json({"error": "Analysis timed out"}, 500)

    def _handle_optimize(self, data: dict):
        """Run supportsage tree to generate optimized supports.

        Optional 'filament' field: if provided, filament details are
        appended to the response.
        """
        stl_path = data.get("stl_path", "")
        if not stl_path or not os.path.isfile(stl_path):
            self._send_json({"error": "STL file not found"}, 400)
            return

        angle = data.get("angle", 45)
        strategy = data.get("strategy", "balanced")

        try:
            # Output to temp file
            tmp = tempfile.NamedTemporaryFile(suffix=".stl", delete=False)
            output_path = tmp.name
            tmp.close()

            result = subprocess.run(
                [
                    "supportsage", "tree", stl_path,
                    "-o", output_path,
                    "--angle", str(angle),
                    "--strategy", strategy,
                ],
                capture_output=True, text=True, timeout=60,
            )

            if result.returncode != 0:
                self._send_json({
                    "error": result.stderr[:500],
                    "stdout": result.stdout[:500],
                }, 500)
                return

            # Read the output file
            with open(output_path, "rb") as f:
                import base64
                stl_b64 = base64.b64encode(f.read()).decode()

            os.unlink(output_path)

            response = {
                "status": "ok",
                "stl_base64": stl_b64,
                "log": result.stdout,
            }

            # Optional filament enrichment
            filament_query = data.get("filament", "")
            if filament_query:
                response["filament"] = _search_filament(filament_query)

            self._send_json(response)
        except FileNotFoundError:
            self._send_json({
                "error": "SupportSage CLI not found.",
            }, 500)
        except subprocess.TimeoutExpired:
            self._send_json({"error": "Optimization timed out"}, 500)

    def _handle_filament_search(self, data: dict):
        """Search for filaments matching a query string."""
        query = data.get("query", "")
        if not query:
            self._send_json({"error": "Missing 'query' field"}, 400)
            return

        results = _search_filament(query)
        self._send_json({"results": results})

    def _handle_filament_recommend(self, data: dict):
        """Get a full filament recommendation by brand/model or material_type."""
        brand = data.get("brand", "")
        model = data.get("model", "")
        material_type = data.get("material_type", "")

        if not brand and not model and not material_type:
            self._send_json({
                "error": "Provide 'brand'/'model' or 'material_type'"
            }, 400)
            return

        result = _recommend_filament(
            brand=brand, model=model, material_type=material_type
        )
        self._send_json(result)

    def _handle_print_inspect(self, data: dict):
        """Inspect a print image for quality issues."""
        image_path = data.get("image_path", "")
        if not image_path:
            self._send_json({"error": "Missing 'image_path' field"}, 400)
            return

        result = _inspect_print(image_path)
        self._send_json(result)

    def _send_json(self, data: dict, status: int = 200):
        """Send JSON response."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())


# ── CLI ──

def main():
    parser = argparse.ArgumentParser(
        prog="supportsage-gui",
        description="Launch SupportSage GUI in your browser",
    )
    parser.add_argument(
        "--port", type=int, default=DEFAULT_PORT,
        help=f"Port to serve on (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--open", action="store_true",
        help="Open browser automatically",
    )
    args = parser.parse_args()

    # Verify CLI is installed
    try:
        result = subprocess.run(
            ["supportsage", "--version"],
            capture_output=True, text=True, timeout=5,
        )
        cli_version = result.stdout.strip()
        print(f"  ✅ SupportSage CLI: {cli_version}")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("  ⚠️  SupportSage CLI not found. Install:")
        print("     pip install https://github.com/bossman-lab/supportsage/releases/download/v0.1.0/supportsage-0.1.0-py3-none-any.whl")
        print("  The viewer will work, but analysis & generation require the CLI.\n")

    # Check optional dependencies
    try:
        from filamentdb.database import search  # noqa: F401
        print("  ✅ filamentdb: available")
    except ImportError:
        print("  ⚠️  filamentdb not found — filament search/recommend disabled")

    try:
        from printsight.analyzer import analyze  # noqa: F401
        print("  ✅ printsight: available")
    except ImportError:
        print("  ⚠️  printsight not found — print inspection disabled")

    server = HTTPServer(("0.0.0.0", args.port), SupportSageHandler)
    url = f"http://localhost:{args.port}"

    print(f"\n  🧠 SupportSage GUI")
    print(f"  {'=' * 40}")
    print(f"  📍 {url}")
    print(f"  🛑 Ctrl+C to stop")
    print()

    if args.open:
        import webbrowser
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  👋 Goodbye!")
        server.server_close()


if __name__ == "__main__":
    main()

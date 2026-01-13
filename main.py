# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

# This Python file uses the following encoding: utf-8
"""
Lucent - Main application entry point.

This module initializes the Qt application, registers QML components,
and launches the main window.
"""

import sys
import os
from pathlib import Path

from typing import Optional, cast
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QOpenGLContext, QFont, QIcon
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterType
from PySide6.QtCore import QObject, Property, Signal
from PySide6.QtQuick import QQuickWindow, QSGRendererInterface
from lucent.canvas_renderer import CanvasRenderer
from lucent.canvas_model import CanvasModel
from lucent.document_manager import DocumentManager
from lucent.font_provider import FontProvider
from lucent.app_controller import AppController
from lucent.unit_settings import UnitSettings

# Version placeholder - replaced by GitHub Actions during release builds
__version__ = "__VERSION__"


def _set_default_rhi_backend() -> None:
    # Respect user override
    if os.environ.get("QSG_RHI_BACKEND"):
        return
    # Pick the most capable backend per platform; let Qt fall back if unavailable.
    if sys.platform == "darwin":
        os.environ["QSG_RHI_BACKEND"] = "metal"
    elif sys.platform == "win32":
        os.environ["QSG_RHI_BACKEND"] = "direct3d11"
    else:
        # Linux/BSD: force OpenGL for grid shader compatibility
        os.environ["QSG_RHI_BACKEND"] = "vulkan"


if __name__ == "__main__":
    _set_default_rhi_backend()

    # Use threaded render loop for proper VSync at display refresh rate
    os.environ.setdefault("QSG_RENDER_LOOP", "threaded")

    # Use QApplication (not QGuiApplication) to support Qt.labs.platform native dialogs
    app = QApplication(sys.argv)

    # Set application icon
    icon_path = Path(__file__).resolve().parent / "assets" / "appIcon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # Use fusion style on Windows to match Linux
    if sys.platform == "win32":
        from PySide6.QtQuickControls2 import QQuickStyle

        QQuickStyle.setStyle("Fusion")
    app_font = QFont()
    app_font.setFamilies(
        ["Cantarell", "Segoe UI", "Tahoma", "Ubuntu", "Roboto", "sans-serif"]
    )
    app.setFont(app_font)

    class AppInfo(QObject):
        """Exposes app version and renderer info to QML for About dialog."""

        infoChanged = Signal()

        def __init__(self, version: str) -> None:
            super().__init__()
            self._app_version = version
            self._renderer_backend = "unknown"
            self._gl_vendor = "unknown"
            self._renderer_type = "unknown"

        def setRendererInfo(
            self, backend: str, vendor: str, renderer_type: str
        ) -> None:
            """Set all renderer info at once and notify QML."""
            self._renderer_backend = backend
            self._gl_vendor = vendor
            self._renderer_type = renderer_type
            self.infoChanged.emit()

        @Property(str, constant=True)
        def appVersion(self) -> str:
            return self._app_version

        @Property(str, notify=infoChanged)
        def rendererBackend(self) -> str:
            return self._renderer_backend

        @Property(str, notify=infoChanged)
        def glVendor(self) -> str:
            return self._gl_vendor

        @Property(str, notify=infoChanged)
        def rendererType(self) -> str:
            return self._renderer_type

    qmlRegisterType(
        cast(type, CanvasRenderer), "CanvasRendering", 1, 0, "CanvasRenderer"
    )  # type: ignore[call-overload]

    engine = QQmlApplicationEngine()

    # Create and register canvas model as global singleton
    canvas_model = CanvasModel()
    engine.rootContext().setContextProperty("canvasModel", canvas_model)

    # Unit and DPI settings exposed to QML
    unit_settings = UnitSettings()
    engine.rootContext().setContextProperty("unitSettings", unit_settings)

    # Create and register document manager for file operations
    document_manager = DocumentManager(canvas_model, unit_settings)
    engine.rootContext().setContextProperty("documentManager", document_manager)

    # Create and register font provider for dynamic font lists
    font_provider = FontProvider()
    engine.rootContext().setContextProperty("fontProvider", font_provider)

    app_info = AppInfo(__version__)
    engine.rootContext().setContextProperty("appInfo", app_info)

    # App controller for cross-cutting UI actions
    app_controller = AppController()
    engine.rootContext().setContextProperty("appController", app_controller)

    # Expose renderer backend info helper
    def _renderer_backend(api: QSGRendererInterface.GraphicsApi) -> str:
        name = getattr(api, "name", None)
        if isinstance(name, str):
            n = name.lower()
            if n == "unknown":
                return "unknown"
            if n == "software":
                return "software"
            if n == "opengl":
                return "opengl"
            if n == "direct3d11":
                return "direct3d11"
            if n == "vulkan":
                return "vulkan"
            if n == "metal":
                return "metal"
            if n == "null":
                return "null"

        # Fallback by numeric value
        value_obj = getattr(api, "value", None)
        value = value_obj if isinstance(value_obj, int) else -1
        mapping_int = {
            0: "unknown",
            1: "software",
            2: "opengl",
            3: "direct3d11",
            4: "vulkan",
            5: "metal",
            6: "null",
        }
        return mapping_int.get(value, "unknown")

    qml_file = Path(__file__).resolve().parent / "App.qml"
    engine.load(qml_file)
    if not engine.rootObjects():
        sys.exit(-1)

    # Collect renderer info now that a window exists
    backend = "unknown"
    vendor = "unknown"
    resolved_type = "unknown"

    try:
        window = engine.rootObjects()[0]
        ri = window.rendererInterface()  # type: ignore[attr-defined]
        api = ri.graphicsApi() if ri is not None else QQuickWindow.graphicsApi()
        backend = _renderer_backend(api)

        if backend in ("software", "unknown", "null"):
            resolved_type = "software"
            vendor = "n/a"
        elif backend != "opengl":
            resolved_type = "hardware"
            vendor = f"n/a ({backend})"
        else:
            # Try to collect GL vendor/renderer and classify hardware vs software
            ctx_candidates = []
            if ri is not None:
                ctx_candidates.append(
                    ri.getResource(window, QSGRendererInterface.OpenGLContextResource)  # type: ignore[attr-defined]
                )
            ctx_candidates.append(QOpenGLContext.currentContext())
            ctx_candidates.append(QOpenGLContext.globalShareContext())

            for ctx in ctx_candidates:
                if not isinstance(ctx, QOpenGLContext):
                    continue
                funcs = ctx.functions()
                if not funcs:
                    continue
                try:
                    vendor_bytes = cast(
                        Optional[bytes], funcs.glGetString(0x1F00)
                    )  # GL_VENDOR
                    renderer_bytes = cast(
                        Optional[bytes], funcs.glGetString(0x1F01)
                    )  # GL_RENDERER
                    vendor = (
                        vendor_bytes.decode(errors="ignore")
                        if vendor_bytes
                        else "unknown"
                    )
                    renderer_str = (
                        renderer_bytes.decode(errors="ignore") if renderer_bytes else ""
                    )
                    rend_lower = (renderer_str or vendor).lower()
                    if (
                        "llvmpipe" in rend_lower
                        or "softpipe" in rend_lower
                        or "software" in rend_lower
                    ):
                        resolved_type = "software"
                    else:
                        resolved_type = "hardware"
                    break
                except Exception:
                    continue

            # Default to hardware for GL if we couldn't determine from strings
            if resolved_type == "unknown":
                resolved_type = "hardware"
                if vendor == "unknown":
                    vendor = "unknown (OpenGL)"
    except Exception:
        pass

    app_info.setRendererInfo(backend, vendor, resolved_type)

    sys.exit(app.exec())

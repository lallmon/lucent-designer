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
from PySide6.QtGui import QOpenGLContext, QFont
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterType
from PySide6.QtCore import Qt, QObject, Property, Signal
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
    # Enable VSync and optimize rendering
    os.environ["QSG_RENDER_LOOP"] = "basic"  # Use basic render loop for better sync
    _set_default_rhi_backend()
    # Enable desktop OpenGL for better performance
    QApplication.setAttribute(Qt.AA_UseDesktopOpenGL)  # type: ignore[attr-defined]

    # Use QApplication (not QGuiApplication) to support Qt.labs.platform native dialogs
    app = QApplication(sys.argv)

    # Use fusion style on Windows to match Linux
    if sys.platform == "win32":
        from PySide6.QtQuickControls2 import QQuickStyle

        QQuickStyle.setStyle("Fusion")

    # Set global font with fallbacks to stay close to platform defaults
    app_font = QFont()
    app_font.setFamilies(
        ["Cantarell", "Segoe UI", "Tahoma", "Ubuntu", "Roboto", "sans-serif"]
    )
    app.setFont(app_font)

    class AppInfo(QObject):
        rendererBackendChanged = Signal()
        appVersionChanged = Signal()
        glVendorChanged = Signal()
        rendererTypeChanged = Signal()

        def __init__(self, version: str) -> None:
            super().__init__()
            self._app_version = version
            self._renderer_backend = "unknown"
            self._gl_vendor = "unknown"
            self._renderer_type = "unknown"

        def get_app_version(self) -> str:
            return self._app_version

        def set_app_version(self, value: str) -> None:
            if self._app_version == value:
                return
            self._app_version = value
            self.appVersionChanged.emit()

        def get_renderer_backend(self) -> str:
            return self._renderer_backend

        def set_renderer_backend(self, value: str) -> None:
            if self._renderer_backend == value:
                return
            self._renderer_backend = value
            self.rendererBackendChanged.emit()

        def get_gl_vendor(self) -> str:
            return self._gl_vendor

        def set_gl_vendor(self, value: str) -> None:
            if self._gl_vendor == value:
                return
            self._gl_vendor = value
            self.glVendorChanged.emit()

        def get_renderer_type(self) -> str:
            return self._renderer_type

        def set_renderer_type(self, value: str) -> None:
            if self._renderer_type == value:
                return
            self._renderer_type = value
            self.rendererTypeChanged.emit()

        appVersion = Property(
            str, get_app_version, set_app_version, notify=appVersionChanged
        )  # type: ignore[assignment]
        rendererBackend = Property(
            str,
            get_renderer_backend,
            set_renderer_backend,
            notify=rendererBackendChanged,
        )  # type: ignore[assignment]
        glVendor = Property(str, get_gl_vendor, set_gl_vendor, notify=glVendorChanged)  # type: ignore[assignment]
        rendererType = Property(
            str, get_renderer_type, set_renderer_type, notify=rendererTypeChanged
        )  # type: ignore[assignment]

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

    # Initial guess
    app_info.set_renderer_backend(_renderer_backend(QQuickWindow.graphicsApi()))
    qml_file = Path(__file__).resolve().parent / "App.qml"
    engine.load(qml_file)
    if not engine.rootObjects():
        sys.exit(-1)

    # Update renderer info now that a window exists
    try:
        window = engine.rootObjects()[0]
        ri = window.rendererInterface()  # type: ignore[attr-defined]
        api = ri.graphicsApi() if ri is not None else QQuickWindow.graphicsApi()
        backend = _renderer_backend(api)
        app_info.set_renderer_backend(backend)

        resolved_type: Optional[str] = None

        # For non-OpenGL backends, GL vendor is meaningless;
        # assume hardware unless software/null.
        if backend in ("software", "unknown", "null"):
            resolved_type = "software"
            app_info.set_gl_vendor("n/a")
        elif backend != "opengl":
            resolved_type = "hardware"
            app_info.set_gl_vendor(f"n/a ({backend})")
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
                    app_info.set_gl_vendor(vendor or "unknown")
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

            # If we couldn't resolve type from GL strings, default to hardware for GL
            if resolved_type is None:
                resolved_type = "hardware"
                if app_info.get_gl_vendor() == "unknown":
                    app_info.set_gl_vendor("unknown (OpenGL)")

        app_info.set_renderer_type(resolved_type or "unknown")
    except Exception:
        # Leave the initial value if introspection fails
        pass

    sys.exit(app.exec())

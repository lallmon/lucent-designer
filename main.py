# This Python file uses the following encoding: utf-8
"""
Lucent - Main application entry point.

This module initializes the Qt application, registers QML components,
and launches the main window.
"""
import sys
import os
from pathlib import Path

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterType
from PySide6.QtCore import Qt
from lucent.canvas_renderer import CanvasRenderer
from lucent.canvas_model import CanvasModel

# Version placeholder - replaced by GitHub Actions during release builds
__version__ = "__VERSION__"


if __name__ == "__main__":
    # Enable VSync and optimize rendering
    os.environ["QSG_RENDER_LOOP"] = "basic"  # Use basic render loop for better sync

    # Enable desktop OpenGL for better performance
    QGuiApplication.setAttribute(Qt.AA_UseDesktopOpenGL)

    app = QGuiApplication(sys.argv)

    qmlRegisterType(CanvasRenderer, "CanvasRendering", 1, 0, "CanvasRenderer")

    engine = QQmlApplicationEngine()

    # Create and register canvas model as global singleton
    canvas_model = CanvasModel()
    engine.rootContext().setContextProperty("canvasModel", canvas_model)

    # Expose application version to QML
    engine.rootContext().setContextProperty("appVersion", __version__)
    qml_file = Path(__file__).resolve().parent / "App.qml"
    engine.load(qml_file)
    if not engine.rootObjects():
        sys.exit(-1)
    sys.exit(app.exec())

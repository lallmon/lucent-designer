# This Python file uses the following encoding: utf-8
"""
DesignVibe - Main application entry point.

This module initializes the Qt application, registers QML components,
and launches the main window.
"""
import sys
import os
from pathlib import Path
from typing import List

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterType
from PySide6.QtCore import Qt
from canvas_renderer import CanvasRenderer
from canvas_model import CanvasModel


if __name__ == "__main__":
    # Enable VSync and optimize rendering
    os.environ['QSG_RENDER_LOOP'] = 'basic'  # Use basic render loop for better sync
    
    # Enable desktop OpenGL for better performance
    QGuiApplication.setAttribute(Qt.AA_UseDesktopOpenGL)
    
    app = QGuiApplication(sys.argv)
    
    qmlRegisterType(CanvasRenderer, "DesignVibe", 1, 0, "CanvasRenderer")
    
    engine = QQmlApplicationEngine()
    
    # Create and register canvas model as global singleton
    canvas_model = CanvasModel()
    engine.rootContext().setContextProperty("canvasModel", canvas_model)
    qml_file = Path(__file__).resolve().parent / "main.qml"
    engine.load(qml_file)
    if not engine.rootObjects():
        sys.exit(-1)
    sys.exit(app.exec())

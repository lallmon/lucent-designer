"""Pytest configuration and shared fixtures for Lucent tests."""

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlApplicationEngine
from lucent.canvas_model import CanvasModel
from lucent.canvas_renderer import CanvasRenderer


@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication instance for the test session.

    Qt requires a QApplication instance to be created before any Qt objects.
    This fixture creates one that lasts for the entire test session.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # Note: Don't call app.quit() here as it can cause issues with pytest-qt


@pytest.fixture
def canvas_model(qapp):
    """Create a fresh CanvasModel instance for each test."""
    return CanvasModel()


@pytest.fixture
def canvas_renderer(qapp):
    """Create a fresh CanvasRenderer instance for each test."""
    return CanvasRenderer()


@pytest.fixture
def qml_engine(qapp):
    """Create a QQmlApplicationEngine instance for integration tests."""
    engine = QQmlApplicationEngine()
    yield engine
    engine.deleteLater()

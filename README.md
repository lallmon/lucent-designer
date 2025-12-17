# DesignVibe

A digital design application built with PySide6 and Qt Quick.

## Features

### Rendering Canvas
- **Infinite canvas** (36,000 x 36,000 pixels) with pan and zoom capabilities
- **Grid system** with minor and major gridlines for visual reference
- **Zoom controls**: Mouse wheel, keyboard shortcuts (Ctrl+/Ctrl-/Ctrl+0), and menu options
- **Pan navigation**: Click and drag with left mouse button
- **Crisp rendering** with smooth transformations
- Starts with a zoomed-out view for better overview

### User Interface
- Menu bar with File and View menus
- Status bar with real-time zoom level indicator


## Controls

- **Pan**: Click and drag with left mouse button
- **Zoom**: Mouse wheel or Ctrl+Plus/Ctrl+Minus
- **Reset view**: Ctrl+0
- **Quit**: Ctrl+Q

## Project Structure

- `main.py` - Application entry point
- `main.qml` - Main application window with menu bar
- `Components/` - QML components directory
  - `InfiniteCanvas.qml` - Infinite canvas component with pan/zoom
  - `StatusBar.qml` - Status bar component with zoom level display
- `pyproject.toml` - Project configuration
- `requirements.txt` - Python dependencies


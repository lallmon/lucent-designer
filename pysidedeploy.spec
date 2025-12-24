[app]
title = DesignVibe
version = __VERSION__
exec_directory = .
icon = assets/icon.png
input_file = main.py
project_dir = .
project_file = pyproject.toml

[python]
version = 3.10
packages = PySide6
python_path = /home/lka/Git/DesignVibe/.venv/bin/python

[qt]
qml_files = App.qml,components/
plugins = qml
excluded_qml_plugins = QtCharts,QtSensors,QtWebEngine
modules = Core,DBus,Gui,Network,OpenGL,Qml,QmlMeta,QmlModels,QmlWorkerScript,Quick,QuickControls2,QuickTemplates2

[linux]
appimage = true

[macos]
bundle_identifier = org.designvibe.DesignVibe

[windows]
console = false


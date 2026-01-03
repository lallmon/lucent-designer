[app]
title = Lucent
version = __VERSION__
exec_directory = .
icon = assets/appIcon.png
input_file = main.py
project_dir = .
project_file = pyproject.toml

[python]
version = 3.10
packages = PySide6,lucent
python_path = /home/lka/Git/lucent/.venv/bin/python

[qt]
qml_files = App.qml,components/
plugins = qml
excluded_qml_plugins = QtCharts,QtSensors,QtWebEngine
modules = Core,DBus,Gui,Network,Qml

[nuitka]
extra_args = --jobs=6 --assume-yes-for-downloads --include-package=lucent --include-data-files=App.qml=App.qml --include-data-dir=components=components --include-data-dir=assets=assets

[linux]
appimage = true

[macos]
bundle_identifier = org.lucent.Lucent

[windows]
console = false


@echo off
python -m pip install -r requirements.txt
python -m pyinstaller --onefile src\app.py

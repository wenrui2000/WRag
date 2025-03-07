@echo off
cd backend
set PYTHONPATH=%PYTHONPATH%;%CD%\src
python -m pytest tests/common -v --cov=src.common
cd .. 
@echo off
echo Running tests with coverage...
pytest --cov=src --cov-report=html --cov-report=term-missing
echo.
echo HTML coverage report generated in htmlcov/index.html
pause 
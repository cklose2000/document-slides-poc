@echo off
echo Starting Document to Slides POC...
echo.
echo Opening browser to: http://localhost:5000/static/presentation.html
echo.
start http://localhost:5000/static/presentation.html
wsl cd /mnt/c/Users/cklos/document-slides-poc && python3 start_simple.py
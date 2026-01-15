@echo off
REM Install all required packages for OPENCHAIN IR v3.0
echo Installing advanced features packages...

cd /d c:\Users\kollu\Documents\PROJECTS\OPENCHAIN-IR

REM Activate venv
call venv\Scripts\activate.bat

REM Install new packages
echo Installing sqlalchemy, psycopg2, scikit-learn, xgboost...
pip install -q sqlalchemy psycopg2-binary scikit-learn numpy xgboost 2>&1

echo.
echo ✅ All packages installed successfully!
echo.
echo Ready to test features...
pause

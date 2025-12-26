@echo off
echo Starting ZK Biometric System Servers...
echo.

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate
) else (
    echo Virtual environment not found. Using system Python.
)

echo.
echo Starting FastAPI Device API Server on port 5000...
start "ZK Device API" cmd /k "python zk_device_api.py"

echo Waiting for API server to start...
timeout /t 3 /nobreak >nul

echo.
echo Testing API connection...
python -c "import requests; response = requests.post('http://localhost:5004/test-connection', json={'ip_address': '172.16.10.39', 'port': 4370}); print('API Test Result:', response.text)"

echo.
echo Starting Django Development Server on port 8000...
echo.

REM Run Django server
python manage.py runserver 0.0.0.0:8000

echo.
echo Both servers should now be running:
echo - FastAPI Device API: http://localhost:5004
echo - Django Application: http://localhost:8000
echo.
echo Press any key to exit...
pause >nul
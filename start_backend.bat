@echo off
echo Starting Backend Server...
echo.

REM Activate virtual environment
call ..\venv\Scripts\activate

REM Start the FastAPI server
echo Backend API will be available at: http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000


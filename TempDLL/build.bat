@echo off
echo Building ZKBiometricDLL...

cd /d "%~dp0"

echo Restoring NuGet packages...
dotnet restore

echo Building DLL...
dotnet build --configuration Release

echo Copying DLL to output folder...
if not exist "output" mkdir output
copy "bin\Release\net8.0\ZKBiometricDLL.dll" output\
copy "bin\Release\net8.0\*.dll" output\ 2>nul

echo Build completed! DLL is in the 'output' folder.
echo.
echo To use from Python, install Python.NET:
echo pip install pythonnet
echo.
echo See python_example.py for usage examples.
pause
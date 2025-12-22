@echo off
echo Building ZKBiometricDLL...

cd /d "%~dp0"

echo Checking .NET version...
dotnet --version

echo Restoring NuGet packages...
dotnet restore

echo Building DLL...
dotnet build --configuration Release

echo Copying DLL to output folder...
if not exist "output" mkdir output
if exist "bin\Release\net8.0\win-x64\ZKBiometricDLL.dll" (
    copy "bin\Release\net8.0\win-x64\ZKBiometricDLL.dll" output\
    copy "bin\Release\net8.0\win-x64\*.dll" output\ 2>nul
) else (
    if exist "bin\Release\net8.0\ZKBiometricDLL.dll" (
        copy "bin\Release\net8.0\ZKBiometricDLL.dll" output\
        copy "bin\Release\net8.0\*.dll" output\ 2>nul
    ) else (
        echo ERROR: DLL was not built successfully!
        echo Check the build errors above.
        pause
        exit 1
    )
)

echo Build completed! DLL is in the 'output' folder.
echo.
echo To use from Python, install Python.NET:
echo pip install pythonnet
echo.
echo See python_example.py for usage examples.
pause
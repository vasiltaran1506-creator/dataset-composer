@echo off
echo ========================================
echo Сборка Dataset Composer (.exe)
echo ========================================
echo.

REM Проверяем, установлен ли PyInstaller
python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo [!] PyInstaller не установлен. Устанавливаю...
    pip install pyinstaller
    echo.
)

echo [1/3] Запуск сборки...
python -m PyInstaller ^
    --noconfirm ^
    --onedir ^
    --windowed ^
    --name="Dataset Composer" ^
    --icon=NONE ^
    --add-data "%cd%/src/settings_manager.py;." ^
    --add-data "%cd%/src/config_loader.py;." ^
    --add-data "%cd%/src/prompt_library.py;." ^
    --add-data "%cd%/src/scene_builder.py;." ^
    --add-data "%cd%/src/exporter.py;." ^
    --add-data "%cd%/src/coverage_tracker.py;." ^
    --add-data "%cd%/prompt-library;prompt-library" ^
    --add-data "%cd%/scene-rules;scene-rules" ^
    --add-data "%cd%/character-profiles;character-profiles" ^
    --hidden-import=tomli ^
    --hidden-import=tomli_w ^
    --hidden-import=yaml ^
    --hidden-import=customtkinter ^
    src/ui/main_window.py

if errorlevel 1 (
    echo.
    echo [!] Сборка завершилась с ошибкой!
    pause
    exit /b 1
)

echo.
echo [2/3] Копирую settings.json (если нет)...
if not exist "dist\Dataset Composer\settings.json" (
    if exist "settings.json" (
        copy "settings.json" "dist\Dataset Composer\settings.json"
    )
)

echo.
echo [3/3] Готово!
echo.
echo ========================================
echo Исполняемый файл находится в:
echo %cd%\dist\Dataset Composer\Dataset Composer.exe
echo ========================================
echo.
pause
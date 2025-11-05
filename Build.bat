@echo off
setlocal enabledelayedexpansion

:: ===================================================================
::            SysTools - 自动化打包与分发脚本 (V8 - 排除 __pycache__)
:: ===================================================================

echo.
echo [INFO] 设置环境变量...
set "PROJECT_ROOT=%~dp0"
set "PYTHON_EXE=python"
set "COLLECT_SCRIPT=%PROJECT_ROOT%collect_imports.py"
set "HIDDEN_IMPORTS_FILE=%PROJECT_ROOT%_hidden_imports.py"
set "PYINSTALLER_DIST=%PROJECT_ROOT%dist"
set "PYINSTALLER_BUILD=%PROJECT_ROOT%build"
set "FINAL_PACKAGE_DIR=%PROJECT_ROOT%SysTools_FinalPackage"
set "VERSION_FILE=%PROJECT_ROOT%version_info.txt"
set "EXCLUDE_FILE=%PROJECT_ROOT%build_exclude.txt"

echo.
echo [STEP 1/6] 清理旧的输出文件...
if exist "%FINAL_PACKAGE_DIR%" (
    echo  - 删除旧的发布包: %FINAL_PACKAGE_DIR%
    rmdir /s /q "%FINAL_PACKAGE_DIR%"
)
if exist "%PYINSTALLER_DIST%" (
    echo  - 删除临时的 dist 文件夹...
    rmdir /s /q "%PYINSTALLER_DIST%"
)
if exist "%PYINSTALLER_BUILD%" (
    echo  - 删除临时的 build 文件夹...
    rmdir /s /q "%PYINSTALLER_BUILD%"
)
echo  - 删除临时的 spec 文件...
del /f /q "%PROJECT_ROOT%SysTools.spec" 2>nul
echo  - 删除旧的依赖文件...
del /f /q "%HIDDEN_IMPORTS_FILE%" 2>nul
echo  - 清理完成。

echo.
echo [STEP 2/6] 自动收集插件依赖 (非递归)...
if not exist "%COLLECT_SCRIPT%" (
    echo.
    echo [ERROR] 依赖收集脚本 %COLLECT_SCRIPT% 不存在！
    pause
    exit /b 1
)
%PYTHON_EXE% "%COLLECT_SCRIPT%"
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] 依赖收集失败！请检查上面的错误信息。
    pause
    exit /b %errorlevel%
)
echo  - 依赖收集完成！

echo.
echo [STEP 3/6] 开始使用 PyInstaller 打包主程序...
echo  - 正在嵌入版本信息从 %VERSION_FILE%...
pyinstaller --noconfirm --onefile --windowed --name SysTools --uac-admin --icon "%PROJECT_ROOT%SysTools.ico" --version-file "%VERSION_FILE%" "%PROJECT_ROOT%main.py"

:: 检查打包是否成功
if not exist "%PYINSTALLER_DIST%\SysTools.exe" (
    echo.
    echo [ERROR] PyInstaller 打包失败！请检查上面的错误信息。
    pause
    exit /b 1
)
echo  - 主程序打包成功！

echo.
echo [STEP 4/6] 创建最终的发布文件夹...
mkdir "%FINAL_PACKAGE_DIR%"
echo  - 已创建目录: %FINAL_PACKAGE_DIR%

echo.
echo [STEP 5/6] 组装发布包，复制并整理所有文件...
echo  - 移动主程序 SysTools.exe...
move "%PYINSTALLER_DIST%\SysTools.exe" "%FINAL_PACKAGE_DIR%\"

rem ===================================================================
rem  【核心修改】为 xcopy 命令添加 /EXCLUDE 参数
rem ===================================================================
if not exist "%EXCLUDE_FILE%" (
    echo.
    echo [WARNING] 排除文件 %EXCLUDE_FILE% 不存在，将复制所有文件。
    set "EXCLUDE_PARAM="
) else (
    set "EXCLUDE_PARAM=/EXCLUDE:%EXCLUDE_FILE%"
)

echo  - 复制 plugins 文件夹 (排除 __pycache__)...
xcopy "%PROJECT_ROOT%plugins" "%FINAL_PACKAGE_DIR%\plugins\" /s /e /i /y %EXCLUDE_PARAM% > nul

echo  - 复制 plugins_test 文件夹 (排除 __pycache__)...
xcopy "%PROJECT_ROOT%plugins_test" "%FINAL_PACKAGE_DIR%\plugins_test\" /s /e /i /y %EXCLUDE_PARAM% > nul
rem ===================================================================

echo  - 复制 .ini 配置文件...
xcopy "%PROJECT_ROOT%plugins\tools\*.ini" "%FINAL_PACKAGE_DIR%\" /y > nul

echo  - 复制 templates 图像模板...
mkdir "%FINAL_PACKAGE_DIR%\templates"
xcopy "%PROJECT_ROOT%plugins\tools\templates\*.bmp" "%FINAL_PACKAGE_DIR%\templates\" /y > nul

echo  - 复制图标文件...
xcopy "%PROJECT_ROOT%SysTools.ico" "%FINAL_PACKAGE_DIR%\" /y > nul

echo  - 清理发布包内已移动的冗余文件...
del /q "%FINAL_PACKAGE_DIR%\plugins\tools\*.ini" > nul 2>&1
rmdir /s /q "%FINAL_PACKAGE_DIR%\plugins\tools\templates" > nul 2>&1
echo  - 文件组装与整理完成！

echo.
echo [STEP 6/6] 清理临时的打包文件...
rmdir /s /q "%PYINSTALLER_BUILD%"
rmdir /s /q "%PYINSTALLER_DIST%"
del /f /q "%PROJECT_ROOT%SysTools.spec" 2>nul
del /f /q "%HIDDEN_IMPORTS_FILE%" 2>nul
echo  - 清理完成。

echo.
echo ===================================================================
echo  打包成功！
echo.
echo  您最终的、可分发的应用程序位于以下文件夹中:
echo  %FINAL_PACKAGE_DIR%
echo.
echo ===================================================================
echo.
pause
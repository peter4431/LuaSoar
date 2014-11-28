@echo off

set DIR=%~dp0

echo %QUICK_V3_ROOT%

::这个文件放在工程目录下面和src同一级目录
::如果还是不能启动，修改下面=右边的值为player的绝对路径
set BIN=%QUICK_COCOS2DX_ROOT%\player\win\player.exe

set BIN=%QUICK_V3_ROOT%\quick\player\proj.win32\bin\player3.exe
if not exist %BIN% set BIN=%QUICK_V3_ROOT%quick\player\proj.win32\Release\player3.exe
if not exist %BIN% set BIN=%QUICK_V3_ROOT%quick\player\proj.win32\Debug\player3.exe

set ARG= -workdir %DIR%
set SIZE=-portrait

%BIN% %ARG% %SIZE%

pause


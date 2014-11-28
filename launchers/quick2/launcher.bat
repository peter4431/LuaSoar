@echo off
::这个文件放在工程目录下面和script同一级目录
::如果还是不能启动，修改下面=右边的值为player的绝对路径
set BIN=%QUICK_COCOS2DX_ROOT%\player\win\player.exe
%BIN% -workdir %~dp0

pause
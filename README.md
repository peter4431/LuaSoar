# LuaSoar（Lua说）

sublime插件，用来调试quick-cocos2dx的lua脚本。

![LuaSoar looks like][LuaSoarlooklike]

## 环境:
* sublime 版本：sublime text 3
* 测试环境：windows and Mac os

## 安装：

###1 下载安装
###2 通过package control安装

## 使用：
![luaSoar use][LuaSoaruse]

* <kbd>f2</kbd> 添加断点
* <kbd>f5</kbd> step into
* <kbd>f6</kbd> step over
* <kbd>f7</kbd> step out
* <kbd>f8</kbd> run
* <kbd>shift</kbd>+<kbd>f2</kbd> 启动播放器调试
* <kbd>ctrl</kbd>+<kbd>shift</kbd>+<kbd>f2</kbd> 启动真机调试，等待android客户端连接

## 注意事项

* 只接受一个调试客户端的连接
* 如果发现连接不上，请按<kbd>f8</kbd>先
## 自定义

修改快捷键请编辑插件目录下的文件:

	Default (Windows).sublime-keymap/Default (OSX).sublime-keymap

修改【keys】字段

[LuaSoarlooklike]:                https://raw.githubusercontent.com/peter4431/LuaSoar/master/screenshots/light.png
[LuaSoaruse]:					  https://raw.githubusercontent.com/peter4431/LuaSoar/master/screenshots/use.png
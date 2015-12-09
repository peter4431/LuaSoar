# LuaSoar（Lua说）

sublime插件，用来调试quick-cocos2dx的lua脚本。支持Android真机调试

启动方式修改：

因为quick版本太多，启动方式太多，所以把启动单独成一个脚本，复制到项目路径下就可以，暂时有quick2和quick3两个版本。

实现原理请查看 [15 行代码 Lua 调试原理][15line] 和 [自定义sublime插件][sublimeplugin]
<font color="red">调试原理：</font>

* <font color="red">lua本身有一个库叫做debug，可以获得当前运行的代码信息，如上下文，堆栈，执行表达式。</font>
* <font color="red">这个调试插件有以下两个主要的文件，他们之间使用socket通信。</font>
* <font color="red">debugger.lua，功能是设置断点，获取lua本身的运行信息，作为socket的客户端</font>
* <font color="red">luaSoar.py，作为socket服务端，用来获得lua的运行信息，使用sublime接口显示出来</font>


## 如果不能设置断点，请按照以下步骤试试：
- 检查快捷键有没有被占用，如果占用换一个试试
- 修改插件以后，需要重启sublime
- 再按添加断点的快捷键，会出现断点的小圆点。

##如果出现了断点的小圆点，不能启动模拟器，请手动启动模拟器试试。


![LuaSoar looks like][LuaSoarlooklike]

## 环境:
* sublime 版本：sublime text 3
* 测试环境：windows and Mac os
* 测试使用quick-cocos2d-x-3.2rc1

## 安装：

###方法一 通过package control安装
参考[这里](http://code-tech.diandian.com/post/2012-11-10/40041273125)

###方法二 下载安装
* 下载LuaSoar
* 点击sublime text3 浏览插件包；![luaSoarinstall1][luaSoarinstall1]
* 放置插件到这个目录即可。![luaSoarinstall2][luaSoarinstall2]

## 使用：
![luaSoar use][LuaSoaruse]

图中的main.lua是这样的
<pre>
--192.168.0.5 ip地址，如果不需要真机调试，可以写127.0.0.1
--10240 调试用的端口号，和debugger.lua文件中用的一样就可以
--"luasoar"一个字符串
--nil（不用理他）
--"win"关系到路径的处理，mac上使用"unix",windows使用"win"
--"E:/projects/android/mytest" 项目绝对路径。
require("debugger")("192.168.0.5",10240,"luasoar",nil,"win","E:/projects/android/mytest")

function __G__TRACKBACK__(errorMessage)
    print("----------------------------------------")
    print("LUA ERROR: " .. tostring(errorMessage) .. "\n")
    print(debug.traceback("", 2))
    print("----------------------------------------")
end
require("app.MyApp").new():run()
</pre>

总结一下步骤：

* 复制debugger.lua到src目录，quick2.x.x是script目录
* 在main.lua中添加调试入口，见上文的文件。
* 复制对应的launcher.bat到工程目录，和src目录同级，windows下双击应该能够打开模拟器。（可以不做，不做需要手动启动模拟器）

快捷键：

* <kbd>f2</kbd> 添加断点
* <kbd>f5</kbd> step into
* <kbd>f6</kbd> step over
* <kbd>f7</kbd> step out
* <kbd>f8</kbd> run
* <kbd>shift</kbd>+<kbd>f2</kbd> 启动播放器调试
* <kbd>ctrl</kbd>+<kbd>shift</kbd>+<kbd>f2</kbd> 启动真机调试，等待android客户端连接

* 光标移动到一行按 <kbd>f2</kbd> 可添加断点
* 定位到 Lua Expression 标签，输入要执行的代码，按enter即可查询表达式(注意，如果代码提示不正确，按<kbd>esc</kbd>)



## 注意事项

* 只接受一个调试客户端的连接
* 如果发现连接不上，请按<kbd>f8</kbd>先
* 调试时，断点只支持未编译过的lua，如果使用luac或者luajit编译过，不能断点。

## 自定义

修改快捷键请编辑插件目录下的文件:

	Default (Windows).sublime-keymap/Default (OSX).sublime-keymap

修改【keys】字段

## 最后
欢迎拍砖

[15line]: https://github.com/peter4431/doc/blob/master/15_line_lua_debug.md
[sublimeplugin]: https://github.com/peter4431/doc/blob/master/sublime_plugin.md
[LuaSoarlooklike]:      https://raw.githubusercontent.com/peter4431/LuaSoar/master/screenshots/light.png
[LuaSoaruse]:			https://raw.githubusercontent.com/peter4431/LuaSoar/master/screenshots/use.png
[luaSoarinstall1]:		https://raw.githubusercontent.com/peter4431/LuaSoar/master/screenshots/install1.png
[luaSoarinstall2]:		https://raw.githubusercontent.com/peter4431/LuaSoar/master/screenshots/install2.png

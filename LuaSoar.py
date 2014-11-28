#coding:utf-8

import platform
import socket
from threading import Thread
from xml.dom.minidom import parseString
import sublime, sublime_plugin
import os
import base64
import subprocess
import time
import re
import time


class Contextview(object):
    '''
    结构化文本的显示，控制缩进等。
    '''
    #{fullname:{value,numchildren,childlist,fullname,name,type,lv}}
    datadict = None
    fullnamedict = None #fullname:{}
    linefullname = None #line:fullname
    lineno = 0
    ordernames = None
    gap = "    "

    def __init__(self):
        self.datadict = {}
        self.fullnamedict = {}
        self.linefullname = {}
        self.ordernames = []

    def clear(self):
        self.datadict.clear()
        self.fullnamedict.clear()
        self.linefullname.clear()
        self.ordernames.clear()
        self.lineno=0

    def parsecontext(self,mstr):
        if type(mstr) == str:
            doc = parseString(mstr)
        else:
            doc = mstr
        try:
            if doc.firstChild.firstChild.localName == "error":
                return
        except:
            return

        self.clear()

        firstchild = doc.firstChild
        childnodes = firstchild.childNodes

        for node in childnodes:
            if node.nodeName == "property":
                mdata = self.parseone(node)
                mdata["lv"] = 0
                print("增加上下文:"+mdata["fullname"])
                self.addvalue(mdata)

    #解析表达式
    def parseeval(self,name,mstr):
        if type(mstr) == str:
            doc = parseString(mstr)
        else:
            doc = mstr

        element = doc.firstChild.firstChild
        if element.firstChild.localName == "error":
            res = {}
            res["fullname"] = name #表达式的fullname
            res["value"] = "error"
            res["name"] = name
            res["type"] = "error"
            res["numchildren"] = "0"
            res["childlist"] = {}
            res["lv"] = 0
        else:
            fullname = self.getattribute(element,"fullname")
            res = {}
            res["fullname"] = name #表达式的fullname
            valuebyte = base64.decodebytes(element.firstChild.data.encode())
            res["value"] = self.pdecode(valuebyte)
            
            res["name"] = name
            res["type"] = element.getAttribute("type")
            res["numchildren"] = res.get("numchildren") or element.getAttribute("numchildren") or 0
            res["childlist"] = res.get("childlist") or {}
            res["lv"] = 0

        for node in element.childNodes:
            if node.localName == "property":
                mdata = self.parseone(node)
                mdata["lv"] = res["lv"]+1
                fullname = mdata["fullname"]
                res["childlist"][fullname] = mdata
                self.fullnamedict[fullname] = mdata
        print("增加表达式:"+res["fullname"])
        self.addvalue(res)

    def pdecode(self,mword):
        try:
            result = mword.decode()
        except Exception as e:
            result = str(mword)

        return result


    #一个property
    def parseone(self,element):
        fullname = self.getattribute(element,"fullname")
        res = self.fullnamedict.get(fullname) or {}
        res["fullname"] = fullname
        res["value"] = self.pdecode(base64.decodebytes(element.firstChild.data.encode()))
        res["name"] = res.get("name") or element.getAttribute("name")
        res["type"] = element.getAttribute("type")
        res["numchildren"] = res.get("numchildren") or element.getAttribute("numchildren") or 0
        res["childlist"] = res.get("childlist") or {}

        return res

    def getattribute(self,element,name):
        return self.pdecode(base64.decodebytes(element.getAttribute(name).encode()))

    #用来显示空table
    def getempty(self,level):
        res = {}
        res["lv"] = level
        res["fullname"] = "["*level
        res["value"] = "empty"
        res["name"] = "empty"
        res["type"] = "empty"
        res["numchildren"] = 0
        res["childlist"] = {}
        return res

    def parseproperty(self,mstr):
        if type(mstr) == str:
            doc = parseString(mstr)
        else:
            doc = mstr
        if doc.firstChild.firstChild.localName == "error":
            return
        firstchild = doc.firstChild.firstChild
        currentnode = self.parseone(firstchild)
        mdict = self.fullnamedict[currentnode["fullname"]]
        fullname = mdict["fullname"]
        if not mdict["numchildren"]:
            if mdict["type"] == "table":
                mdict["childlist"][0] = self.getempty(mdict["lv"]+1)
            else:
                mdict["childlist"] = {}
            return
        childnodes = firstchild.childNodes
        for node in childnodes:
            if node.nodeName == "property":
                mdata = self.parseone(node)
                mdata["lv"] = mdict["lv"]+1
                fullname = mdata["fullname"]
                mdict["childlist"][fullname] = mdata
                self.fullnamedict[fullname] = mdata

    #点击的行来获得fullname
    def getfullnamebyline(self,line):
        if line > len(self.linefullname.keys())-1:
            return
        line = min(line,len(self.linefullname.keys())-1)
        line = max(line,0)
        return self.linefullname[line]

    def addvalue(self,valueobj):
        fullname = valueobj["fullname"]
        self.datadict[fullname] = valueobj
        if not self.datadict[fullname].get("childlist"):
            self.datadict[fullname]["childlist"] = {}

        self.fullnamedict[fullname] = valueobj

    def getstring(self,keys=None):
        self.lineno = 0
        return self.getdictstr(self.datadict,keys)

    #获得最终输出
    def getdictstr(self,mdict,keys=None):
        result = ""
        mkeys = list(mdict.keys())
        mkeys.sort()
        mlist = keys or mkeys
        #sort datalist
        for fullname in mlist:
            prop = mdict[fullname]
            if prop["type"] == "empty":
                result += self.gap * prop["lv"] + "{}\n"
            else:
                result += self.gap * prop["lv"] + "{0}={1}\n".format(prop["name"],prop["value"])
            self.linefullname[self.lineno] = prop["fullname"]
            self.lineno += 1
            if prop.get("childlist") and len(prop["childlist"].values()) > 0:
                result += self.getdictstr(prop["childlist"])
        return result


class MngContext(Contextview):
    '''
    上下文管理器
    '''

    def __init__(self):
        super(MngContext,self).__init__()

class MngExp(Contextview):
    '''
    表达式管理器
    '''
    expressions = []
    #等待结果的表达式
    waitingexps = []

    def __init__(self):
        super(MngExp,self).__init__()

    def getallexp(self):
        view = mng_view.find_debug_view("expression")
        if not view:
            print("没有表达式view")
            return
        allstr = view.substr(sublime.Region(0,view.size()))
        print("获得表达式字符串")
        lines = allstr.split("\n")

        self.expressions.clear()
        for line in lines:
            if line.startswith(" "):
                continue
            line = re.sub("^\s*|\s*$","",line)
            index = line.find("=")
            if index == -1:
                index = len(line)
            exp = line[0:index]
            if exp:
                self.expressions.append(exp)

        print("解析得到所有表达式:"+str(self.expressions))

    def refresheval(self):
        if protocol.status != "break":
            return
        self.clear()
        self.getallexp()

        print("所有exp:")
        print(self.expressions)

        for exp in self.expressions:
            self.requesteval(exp)

    def requesteval(self,eval):
        self.waitingexps.append(eval)
        protocol.eval(eval)

    def on_eval(self,res):
        if len(self.waitingexps) != 0:
            self.parseeval(self.waitingexps[0],res)
            del self.waitingexps[0]
        
        if len(self.waitingexps) == 0:
            mng_view.add_debug_info("expression",self.getstring())

    def getstring(self):
        return super(MngExp,self).getstring(self.expressions)

class DebugServer(object):
    def __init__(self,datahandler,closecallback=None):
        self.datahandler = datahandler
        self.closecallback = closecallback
        self.conn = None
        self.ver = platform.python_version_tuple()
        self.clear()
        self.default_transaction_id = 100

    def clear(self):
        self.listening = False
        self.connected = False
        self.buffer = ""

    def readpacket(self):
        if not self.connected:
            return

        res = bytearray()
        while True:
            try:
                byte = self.conn.recv(1)
            except Exception as e:
                if str(e) == "timed out":
                    return
                else:
                    print(e)
                    print("客户端断开")
                    self.conn.close()
                    self.connected = False
                    if self.closecallback:
                        self.closecallback()
                return

            if len(byte) and byte[0] == 0:
                break
            else:
                if len(byte):
                    res.append(byte[0])
        return res

    def senddata(self,command,transactionid=None,data=None):
        print("send:"+command+" data:"+str(data))
        if not self.conn:
            print("wainting for connect!")
            return
        try:
            cmd = command+" -i {0}".format(transactionid or self.default_transaction_id)
            if data != None:
                cmd += " --" + base64.encodebytes(data.encode()).decode().replace("\n","")

            cmd = cmd+"\x00"
            print("senddata:"+cmd)
            self.conn.sendall(cmd.encode())
        except Exception as e:
            print(str(e))
            self.conn.close()
            self.connected = False
            if self.closecallback:
                self.closecallback()
            return

    def read(self):
        mlen = self.readpacket()
        if not mlen:
            return
        response = self.readpacket()
        if not response:
            return None

        if response:
            docstr = response.decode()
            return docstr

    def start(self):
        self.sock = socket.socket()
        try:
            self.sock.bind(("", 10240))
            self.sock.listen(5)
            self.sock.settimeout(1)
            self.listening = True
        except Exception as e:
            sublime.error_message("检查端口是否被占用:"+str(e))

        while self.listening: 
            try:
                self.conn, addr = self.sock.accept()
                if self.conn:
                    self.connected = True
                    self.conn.settimeout(1)
                    print("client connected!")
            except Exception as e:
                pass  

            while self.connected:
                mstr = self.read()
                if mstr:
                    if self.datahandler:
                        self.datahandler(mstr)

            if not protocol or not protocol.server:
                self.close()

    def close(self):
        print("关闭连接")
        self.conn.close()
        self.sock.close()
        self.clear()

class ServerThread(Thread):
    def __init__(self,datahandler=None,closecallback=None):
        super(ServerThread, self).__init__()
        self.server = DebugServer(datahandler,closecallback)

    def run(self):
        self.server.start()

    def stop(self):
        self.server.close()

    def sendcmd(self, cmd):
        self.server.senddata(cmd)

class MngView(object):
    breakpoint_key = "luadbg_breakpoint"
    currentline_key = "luadbg_currentline"
    table_key = "luadbg_table"
    currentline_view = None

    debug_layout = {
        "cols": [0.0, 0.5, 1.0],
        "rows": [0.0, 0.7, 1.0],
        "cells": [[0, 0, 2, 1], [0, 1, 1, 2], [1, 1, 2, 2]]
        }

    original_layout = None

    debug_names = {
        "context":("Lua Context",1,True),
        "expression":("Lua expression",2,False),
        "breakpoint":("Lua breakpoint",2,True)
        }

    def save_all_file(self):
        # window = sublime.active_window()
        # views = window.views()
        # for view in views:
        #     if view.file_name():
        #         view.save
        sublime.run_command("save_all")

    def backup_layout(self):
        window = sublime.active_window()
        self.original_layout = window.get_layout()
        print("original_layout:"+str(self.original_layout))

    def set_debug(self,mbool):
        print("set_debug:"+str(mbool))
        window = sublime.active_window()
        if mbool:
            self.backup_layout()
            print("set_layout:"+str(self.debug_layout))
            window.set_layout(self.debug_layout)
        else:
            print("set_layout:"+str(self.original_layout))
            window.set_layout(self.original_layout)

    #清除所有调试信息
    def clear_debug(self):
        self.add_debug_info("context","")
        # self.add_debug_info("expression","")
        self.clear_current_line()

    #@param file_name sublime得到的打开的文件地址
    #@return 用来设置断点的uri
    def get_abs_uri(self,file_name):
        if not file_name:
            return ""
        result = ""
        file_name = file_name.replace("\\","/")
        if sublime.platform() == "windows":
            result = "file:///"+file_name.lower()
        else:
            result = "file://"+file_name
        return result

    #@parem file_name 从堆栈得到的文件信息
    #@return 本地用来打开的文件地址
    def get_file_name(self,file_name):
        if sublime.platform() == "windows":
            if file_name.startswith("file:///"):
                temp = file_name[len("file:///"):]
            return temp
        else:
            if file_name.startswith("file:///"):
                temp = file_name[len("file://"):]
            return temp

    def show_breakpoint(self,view,breakpoints):
        self.clear_breakpoint(view)
        file_name = view.file_name()

        if not file_name:
            return

        uri = self.get_abs_uri(file_name)
        fdict = breakpoints.get(uri)

        if fdict:
            for k,v in fdict.items():
                pass
                # print("显示断点:{0}:{1}".format(uri,k))

            regions = [self.get_line_region(view,line_no-1) for line_no in fdict.keys()]
            view.add_regions(self.breakpoint_key,regions,"code","circle",sublime.HIDDEN)

    def clear_breakpoint(self,view):
        view.erase_regions(self.breakpoint_key)

    def show_current_line(self,view,line_no):
        self.currentline_view = view
        view.add_regions(self.currentline_key,[self.get_line_region(view,line_no)],"code","bookmark",sublime.DRAW_NO_OUTLINE)

    def show_current_file_line(self,file,line,isHightlight=False):
        file = self.get_file_name(file)
        print("find file:"+file)
        line = int(line)
        window = sublime.active_window()
        findview = window.find_open_file(file)
        #TODO::for test
        self.searchfile(file)
        isNew = False
        if not findview:
            if not os.path.exists(file):
                file = self.searchfile(file)
            if file and os.path.exists(file):
                findview = window.open_file(file)
                isNew = True
            else:
                print("file not exists:"+str(file))
                protocol.step_out()
                return None,None

        def focusfile():
            window.focus_view(findview)
            region = self.get_line_region(findview,line)
            print("region:"+str(region))
            findview.show_at_center(region)
            if isHightlight:
                self.show_current_line(findview,line)

        if isNew:
            sublime.set_timeout(focusfile,100)
        else:
            focusfile()

    def searchfile(self,file):
        #subpath = file[file.rfind("/src/")+len("/src/"):]
        subpath = getsubdir(file)
        print("subpath:"+subpath)
        temppath = None
        global searchpaths
        for path in searchpaths:
            path = re.sub("\\*","/",path)
            path = re.sub("/$","",path)+"/"
            temppath=path+subpath
            if os.path.exists(temppath):
                return temppath

    def clear_current_line(self):
        if self.currentline_view:
            self.currentline_view.erase_regions(self.currentline_key)

    def get_line_region(self,view,line_no):
        text_point = view.text_point(line_no,0)
        return view.line(text_point)

    def focus_debug(self, name):
        fullname,group,readonly = self.debug_names[name]
        view = None
        for v in window.views():
            if v.name() == fullname:
                view = v
                break
        if view:
            window = sublime.active_window()
            window.set_view_index(view, group, 0)

    def find_debug_view(self,name):
        view = None
        fullname,group,readonly = self.debug_names[name]
        window = sublime.active_window()

        for v in window.views():
            if v.name() == fullname:
                view = v
                return view

    def add_debug_info(self, name, data, focus=True):
        view = None
        fullname,group,readonly = self.debug_names[name]
        window = sublime.active_window()

        if window.num_groups() != 3:
            self.set_debug(True)

        for v in window.views():
            if v.name() == fullname:
                view = v
                break

        if not view:
            self.set_debug(True)
            view = window.new_file()
            view.set_scratch(True)
            view.set_read_only(readonly)
            view.set_name(fullname)
            view.settings().set('word_wrap', False)
            
        window.set_view_index(view, group, 0)
            
        originaldata = view.substr(sublime.Region(0,view.size()))
        
        if True:#originaldata != data:
            view.set_read_only(False)
            view.run_command("luadbg_view_replace",{"mstr":data})
            view.set_read_only(readonly)
            view.run_command("set_file_type",{'syntax': 'Packages/Lua/Lua.tmLanguage'})
            view.add_regions(self.table_key,view.find_all(r"table: 0x.*$"),"code","bookmark",sublime.HIDDEN)
        else:
            pass

        if focus:
            window.set_view_index(view, group, 0)


#断点管理
class MngBreakPoint(object):
    #行号从1开始，显示和调试器都是从1开始,sublime从0开始
    breakpoints = None
    linedict = {}
    line_no = 0

    def __init__(self,addhandler=None,removehandler=None):
        self.breakpoints = {}
        self.addhandler = addhandler
        self.removehandler = removehandler

    def switch(self,file_name,line_no):
        line_no = int(line_no)
        print("switchbreakpoint:{file_name}:{line_no}".format(**locals()))
        if not self.breakpoints.get(file_name):
            self.breakpoints[file_name] = {}

        fdict = self.breakpoints.get(file_name)
        if fdict.get(line_no) != None:
            if self.removehandler:
                self.removehandler(file_name,line_no)
            if fdict.get(line_no):
                del fdict[line_no]
        else:
            fdict[line_no] = {} #存放id，条件等
            if self.addhandler:
                self.addhandler(file_name,line_no)
    
    def getstring(self):
        result = ""
        self.linedict.clear()
        self.line_no = 0
        for file,value in self.breakpoints.items():
            for lineno in value.keys():
                subpath = getsubdir(file)
                result += "{0:>4}:{1}\n".format(lineno,subpath)
                self.linedict[self.line_no] = (file,lineno)
                self.line_no += 1

        return result

    #输出字符串的某一行是哪个文件哪一行
    def getfileinfo(self,line):
        line = int(line)
        print(self.linedict)
        if self.linedict.get(line):
            return self.linedict[line]

    def setinfo(self,id,filename,lineno):
        lineno = int(lineno)
        filedict = self.breakpoints.get(filename)
        if filedict != None:
            linedict = filedict.get(lineno)
            if linedict != None:
                linedict["id"] = int(id)

    def getid(self,filename,lineno):
        lineno = int(lineno)
        print(self.breakpoints)
        filedict = self.breakpoints.get(filename)
        if filedict:
            linedict = filedict.get(lineno)
            if linedict:
                return linedict.get("id")

    def setall(self):
        if not protocol:
            return

        for k,v in self.breakpoints.items():
            for kk,vv in v.items():
                protocol.breakpoint_set(k,kk)


class Protocol(object):
    doc = None
    transaction_id = 0
    status = None
    command = None
    server = None
    isdebugging = False
    lastfileinfo = None

    # commands = {"breakpoint_set","breakpoint_remove",step_into","step_over","step_out","run","context_get","property_get","stack_get","stack_depth","eval"}

    def __init__(self,server):
        self.server = server
        self.context_id = 11
        self.eval_id = 12
        self.status = "break"

    def reset(self):
        self.isdebugging = False

    def setdebugstatus(self,mstr):
        mstr = mstr or ""
        sublime.active_window().active_view().set_status("status","调试状态:"+mstr)

    def datahandler(self,data):
        print(data)
        self.doc = parseString(data)
        if self.doc.firstChild.localName == "init":
            self.on_init()
        elif self.doc.firstChild.localName == "output":
            print(self.doc.firstChild.getAttribute("mstr"))
        else:
            self.transaction_id = int(self.doc.firstChild.getAttribute("transaction_id"))
            self.command = self.doc.firstChild.getAttribute("command")

            self.setdebugstatus(self.status)

            if self.command == "step_into" or \
                self.command == "step_over" or \
                self.command == "step_out" or \
                self.command == "run":
                    self.status = self.doc.firstChild.getAttribute("status")
                    self.on_continue()
            elif self.command == "property_get":
                if self.transaction_id == self.context_id:
                    self.on_property_context()
                elif self.transaction_id == self.eval_id:
                    self.on_property_eval()
            else:
                funcname = "on_"+self.command
                if hasattr(self,funcname):
                    getattr(self,funcname)()

    def breakpoint_set(self,file,line):
        self.server.senddata("breakpoint_set -t line -f {file} -n {line}".format(**locals()))

    def breakpoint_remove(self,id):
        self.server.senddata("breakpoint_remove -d {id}".format(**locals()))

    def step_into(self):
        self.status = "running"
        self.setdebugstatus(self.status)
        mng_view.clear_debug()
        self.server.senddata("step_into")

    def step_over(self):
        self.status = "running"
        self.setdebugstatus(self.status)
        mng_view.clear_debug()
        self.server.senddata("step_over")

    def step_out(self):
        self.status = "running"
        self.setdebugstatus(self.status)
        mng_view.clear_debug()
        self.server.senddata("step_out")

    def run(self):
        self.status = "running"
        self.setdebugstatus(self.status)
        mng_view.clear_debug()
        self.server.senddata("run")

    def context_get(self):
        self.server.senddata("context_get -d 0")

    def property_get_context(self,fullname):
        if self.status == "break":
            self.server.senddata("property_get -n {fullname}".format(**locals()),self.context_id)

    def property_get_eval(self,fullname):
        if self.status == "break":
            self.server.senddata("property_get -n {fullname}".format(**locals()),self.eval_id)

    def stack_get(self,level=0):
        if self.status == "break":
            self.server.senddata("stack_get -d {level}".format(**locals()))

    def eval(self,data):
        self.server.senddata("eval",None,data)

    def on_init(self):
        mng_breakpoints.setall()
        mng_view.add_debug_info("expression","")
        mng_view.add_debug_info("context","")

        #连上调试客户端时会自动断在程序入口，执行step_over来和平时表现一样(无断点则通过，有断点进断点)
        self.step_over()
        self.isdebugging = True

    def on_breakpoint_set(self):
        filename = self.doc.firstChild.getAttribute("filename")
        lineno = self.doc.firstChild.getAttribute("line")
        id = self.doc.firstChild.getAttribute("id")
        print(mng_breakpoints.breakpoints)
        mng_breakpoints.setinfo(id,filename,lineno)

    def on_continue(self):
        self.stack_get()
        self.context_get()
        mng_exp.refresheval()

    def on_property_context(self):
        print("get context property")
        mng_context.parseproperty(self.doc)

        view = mng_view.find_debug_view("context")
        if not view:
            return
        layout = view.viewport_position()
        mng_view.add_debug_info("context",mng_context.getstring())
        view.set_viewport_position(layout,False)

    def on_property_eval(self):
        print("get eval property")
        mng_exp.parseproperty(self.doc)

        view = mng_view.find_debug_view("expression")
        if not view:
            return
        layout = view.viewport_position()
        mng_view.add_debug_info("expression",mng_exp.getstring())
        view.set_viewport_position(layout,False)

    def on_context_get(self):
        mng_context.parsecontext(self.doc)
        mng_view.add_debug_info("context",mng_context.getstring())

    def on_stack_get(self):
        file_name = self.doc.firstChild.firstChild.getAttribute("filename")
        line_no = int(self.doc.firstChild.firstChild.getAttribute("lineno"))
        
        
        if self.lastfileinfo and self.lastfileinfo[0] == file_name and \
            self.lastfileinfo[1] == line_no:
            self.step_over()
            return False
        else:
            self.lastfileinfo = (file_name,line_no)
            mng_view.show_current_file_line(file_name,line_no-1,True)
            return True

    def on_eval(self):
        mng_exp.on_eval(self.doc)

def addbreakpoint(file,line):
    if protocol:
        protocol.breakpoint_set(file,line)

def removebreakpoint(file_name,line):
    if protocol:
        id = mng_breakpoints.getid(file_name,line)
        if id != None:
            protocol.breakpoint_remove(id)

#断点管理
mng_breakpoints = MngBreakPoint(addbreakpoint,removebreakpoint)
#视图管理
mng_view = MngView()
#上下文管理器
mng_context = MngContext()
#表达式管理器
mng_exp = MngExp()
#消息处理
protocol = None
#上次点选的时间，控制上下文和表达式触发点选的时间 
last_select_time = 0

searchpaths = []



def init():
    mng_view.backup_layout()
    global searchpaths
    settings = sublime.load_settings("luadbg.sublime-settings")
    searchpaths = settings.get("searchpaths") or []
    print("search path:"+str(searchpaths))

    mng_view.clear_debug()
    mng_view.add_debug_info("breakpoint","")

def plugin_loaded():
    sublime.set_timeout(init, 200)

def parsepath(mpath):
    mpath = mpath.replace("\\","/")
    indexsrc = mpath.rfind("/src/")
    indexscripts = mpath.rfind("/scripts/")

    print(indexsrc,indexscripts)

    if indexsrc == -1 and indexscripts ==-1:
        return os.path.dirname(result),os.path.basename(result)
    else:
        if indexsrc > indexscripts:
            return mpath[0:indexsrc],mpath[indexsrc+len("/src/"):],"/src/"
        else:
            print(mpath[0:indexscripts])
            print(mpath[indexscripts+len("/scripts/"):])
            return mpath[0:indexscripts],mpath[indexscripts+len("/scripts/"):],"/scripts/"

def getsubdir(mpath):
    _,sub,_ = parsepath(mpath)
    return sub

def getworkdir(mpath):
    workdir,_,_ = parsepath(mpath)
    return workdir

process = None
class LuadbgStartCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        file_name = self.view.file_name()
        if not file_name or not file_name.endswith(".lua"):
            sublime.error_message("choose .lua file and then start!")
            return

        mng_view.save_all_file()

        workdir = getworkdir(file_name)

        def datahandler(data):
            protocol.datahandler(data)

        #因为调试客户端关闭，终止调试
        def closecallback():
            mng_view.clear_current_line()
            mng_view.clear_debug()
        
        global protocol
        if not protocol:
            serverThread = ServerThread(datahandler,closecallback)
            serverThread.setDaemon(True)
            serverThread.start()
            server = serverThread.server
            protocol = Protocol(server)
            print("创建serverThread")
        else:
            print("不需要创建serverThread")

        print("Luadbg:startdbg")

        global process
        args = []
        if process:
            try:
                process.terminate()
            except Exception:
                pass
        if sublime.platform()=="osx":
            args = [workdir+"/launcher.sh"]
            print(args)
            process=subprocess.Popen(args)
        elif sublime.platform()=="windows":
            args = [workdir+"/launcher.bat"]
            print(args)
            process=subprocess.Popen(args)

class LuadbgStartAndroidCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        file_name = self.view.file_name()
        if not file_name or not file_name.endswith(".lua"):
            sublime.error_message("choose .lua file and then start!")
            return

        mng_view.save_all_file()

        if sublime.platform() == "windows":
            index = file_name.rfind("\\src\\")
        else:
            index = file_name.rfind("/src/")
        
        workdir = file_name[0:index]

        def datahandler(data):
            protocol.datahandler(data)

        #因为调试客户端关闭，终止调试
        def closecallback():
            mng_view.clear_current_line()
            mng_view.clear_debug()
        
        global protocol
        if not protocol:
            serverThread = ServerThread(datahandler,closecallback)
            serverThread.setDaemon(True)
            serverThread.start()
            server = serverThread.server
            protocol = Protocol(server)
            print("创建serverThread")
        else:
            print("不需要创建serverThread")

        print("Luadbg:startdbg")

        #TODO compile lua scripts and push to android

class LuadbgBreakpointCommand(sublime_plugin.TextCommand):
    '''
    Toggle a breakpoint
    '''
    def run(self, edit):
        file_name = mng_view.get_abs_uri(self.view.file_name())
        if not file_name.endswith(".lua"):
            return
        sel = self.view.sel()
        line_no = self.view.rowcol(sel[0].a)[0]
        mng_breakpoints.switch(file_name,line_no+1)
        mng_view.show_breakpoint(self.view,mng_breakpoints.breakpoints)
        mng_view.add_debug_info("breakpoint",mng_breakpoints.getstring())

class LuadbgContinueCommand(sublime_plugin.TextCommand):
    def run(self, edit, state):
        if hasattr(protocol,state):
            getattr(protocol,state)()

class LuadbgViewReplaceCommand(sublime_plugin.TextCommand):
    def run(self, edit, mstr):
        self.view.replace(edit,sublime.Region(0,self.view.size()),mstr)

class LuadbgFocusFileCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        print(self.view.name())
        if self.view.name() == "Lua breakpoint":
            sel = self.view.sel()[0]
            line_no = self.view.rowcol(sel.a)[0]
            if line_no < 0:
                return

            mfileline = mng_breakpoints.getfileinfo(line_no)
            
            if mfileline:
                mng_view.show_current_file_line(*mfileline)

    def is_visible(self):
        return self.view.name() == "Lua breakpoint"

class LuadbgAddSearchPathCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        def ondone(mstr):
            settings = sublime.load_settings("luadbg.sublime-settings")
            global searchpaths
            if searchpaths.count(mstr) == 0:
                searchpaths.append(mstr)
            settings.set("searchpaths",searchpaths)
            sublime.save_settings("luadbg.sublime-settings")
            
        def onchange(mstr):
            pass
        def oncancel():
            pass

        sublime.active_window().show_input_panel("add search path:","",ondone,onchange,oncancel)



class EventListener(sublime_plugin.EventListener):
    mfile = None
    def output(self,mstr,*mlist):
        pass

    def on_new(self, view):
        self.output("on_new")

    def on_new_async(self,view):
        self.output("on_new_async")

    def on_clone(self,view):
        self.output("on_clone")

    def on_clone_async(self,view):
        self.output("on_clone_async")

    def on_load(self,view):
        self.output("on_load")

    def on_load_async(self,view):
        self.output("on_load_async")

    def on_pre_close(self,view):
        self.output("on_pre_close")

    def on_close(self,view):
        self.output("on_close")

    def on_pre_save(self,view):
        self.output("on_pre_save")

    def on_pre_save_async(self,view):
        self.output("on_pre_save_async")

    def on_post_save(self,view):
        self.output("on_post_save")

    def on_post_save_async(self,view):
        self.output("on_post_save_async")

    def on_modified(self, view):
        self.output("on_modified")

    def on_modified_async(self,view):
        self.output("on_modified_async")

    def on_selection_modified(self,view):
        self.output("on_selection_modified")

        global last_select_time
        if view.name() == "Lua Context":
            if not protocol or not protocol.server:
                print("not server")
                return

            if time.time()-(last_select_time or 0) <= 0.1:
                print("time too close")
                return

            last_select_time = time.time()

            sel = view.sel()[0]
            line_no = view.rowcol(sel.a)[0]
            if line_no < 0:
                return
            fullname = mng_context.getfullnamebyline(line_no)
            print(fullname)
            if not fullname or re.match(r"\[+",fullname):
                return
            
            mdict = mng_context.fullnamedict[fullname]

            if mdict["value"].find("table") != -1 or mdict["value"].find("userdata") != -1:
                protocol.property_get_context(base64.encodebytes(fullname.encode()).decode())
            
        elif view.name() == "Lua expression":
            if not protocol or not protocol.server:
                return

            if time.time()-(last_select_time or 0) <= 0.1:
                return

            last_select_time = time.time()

            sel = view.sel()[0]
            line_no = view.rowcol(sel.a)[0]
            if line_no < 0:
                return
            fullname = mng_exp.getfullnamebyline(line_no)
            print(fullname)
            if not fullname:
                return
            
            mdict = mng_exp.fullnamedict[fullname]
            if mdict["lv"] > 0:
                if mdict["value"].find("table") != -1 or mdict["value"].find("userdata") != -1:
                    protocol.property_get_eval(base64.encodebytes(fullname.encode()).decode())
            

    def on_selection_modified_async(self,view):
        self.output("on_selection_modified_async")

    def on_activated(self, view):
        file_name = view.file_name()
        self.output("on_activated:"+(file_name or view.name()))

    def on_activated_async(self,view):
        mng_view.show_breakpoint(view,mng_breakpoints.breakpoints)

    def on_deactivated(self,view):
        self.output("on_deactivated")

    def on_deactivated_async(self,view):
        self.output("on_deactivated_async")

    def on_text_command(self, view, command_name, args):
        if command_name == "insert" and view.name() == "Lua expression":
            mng_exp.refresheval()

        self.output("on_text_command:"+command_name,args)

    def on_window_command(self,window,command_name,args):
        self.output("on_window_command:"+command_name,args)

    def post_text_command(self,view,command_name,args):
        print("post_text_command")
        if command_name == "insert" and view.name() == "Lua expression":
            pass
            view.run_command("luadbg_show_expression",{"pos":0,"mstr":"\n"})
        self.output("post_text_command:"+command_name,args)

    def post_window_command(self,window,command_name,args):
        self.output("post_window_command:"+command_name,args)

    def on_query_context(self,view, key, operator, operand, match_all):
        self.output("on_query_context",key,operator,operand,match_all)


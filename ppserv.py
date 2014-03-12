#!/usr/bin/env python
# coding:utf-8

"""Subclass of Ui, which is generated by wxFormBuilder."""

import wx
import ui
import task_bar_icon
from cache import *
from conf import *
from common import *
from module.module_factory import *
from plugin_manager import DirectoryPluginManager
import state_label
import message_handler
import logging
import logging.config


# Implementing Ui
class PPServ(ui.Ui):
    def __init__(self, parent):
        ui.Ui.__init__( self, parent )

        self.SetIcon(wx.Icon('icon.ico', wx.BITMAP_TYPE_ICO))
        self.tray_icon = task_bar_icon.TaskBarIcon(self)
        self.Bind(wx.EVT_CLOSE, self.OnHide)
        self.Bind(wx.EVT_ICONIZE, self.OnIconfiy)

        self.SetBackgroundColour('white')
        self.Show()

        self.data = Cache().get()
        self.lbl = {}
        self.btn_size = (110, 25)
        self.mod_list = {}

        for mod in ModuleFactory.get_module_list():
            self.mod_list[mod.module_name] = mod

        self._dynamic_ui()

        self._set_log()

        wx.CallAfter(self._update_state)

    #窗口控制事件
    def OnHide(self, event):
        """隐藏"""
        self.Hide()

    def OnIconfiy(self, event):
        """点击关闭时只退出监控界面"""
        self.Hide()
        event.Skip()

    def OnClose(self, event):
        """退出"""
        self.tray_icon.Destroy()
        self.Destroy()

    def About(self, event):
        about_str = '%s %s\n\n%s\n %s: %s' % \
        (
            APPNAME,
            VERSION,
            ''.join([mod.module_name + '\n' for mod in ModuleFactory.get_module_list()]),
            Lang().get('author'),
            AUTHOR
        )
        wx.MessageBox(about_str, Lang().get('about_title'))

    # Handlers for Ui events.
    def toggle_service_click(self, event):
        for module_name, state in Cache().get("autorun").items():
            if state:
                mod = self.mod_list[module_name]
                if event.GetEventObject().GetName() == "start":
                    wx.CallAfter(mod.start_service)
                else:
                    wx.CallAfter(mod.stop_service)
    
    def edit_host_click(self, event):
        open_hosts(event)
    
    def auto_run_click(self, event):
        set_autorun(event)
    
    def advt_setting_click(self, event):
        self.basic_panel.Hide()
        self.advt_panel.Show()
        self.advt_sizer.Fit( self.advt_panel )
    
    def basic_setting_click(self, event):
        self.basic_panel.Show()
        self.advt_panel.Hide()
    
    def open_cmd_click(self, event):
        tab_name = self.advt_notebook.GetPageText(self.advt_notebook.GetSelection())
        open_cmd(self.mod_list[tab_name].path)
    
    def _dynamic_ui(self):
        """动态设置Ui"""
        self._add_module_list()
        self._add_advt_page()

        btn_data = (
            ('start_all_service', self.start_all_service),
            ('stop_all_service', self.stop_all_service),
            ('edit_hosts', self.edit_host),
            ('addto_startup', self.auto_run),
            ('advt_setting', self.advt_setting),
            ('basic_setting', self.basic_setting),
            ('open_cmd', self.open_cmd)
        )

        for label, btn in btn_data:
            btn.SetLabel(Lang().get(label))

        plugin_manager = DirectoryPluginManager()
        plugin_manager.load_plugins()
        plugins = plugin_manager.get_plugins()

        for plugin in plugins:
            if plugin.enable:
                plugin.start(self.advt_notebook)

    def _add_module_list(self):
        for module_name in BaseModule.list_service_module():
            run = wx.CheckBox(self.basic_panel, -1, module_name, size=[120, 13])
            run.SetValue(run.Label in self.data['autorun'] and self.data['autorun'][run.Label])
            run.Bind(wx.EVT_CHECKBOX, self._save_select)

            self.lbl[module_name] = state_label.StateLabel(self.basic_panel, -1, "stop", size=(50, 15), name=module_name)
            self.module_list_sizer.Add(run, 0, wx.ALL, 5)
            self.module_list_sizer.Add(self.lbl[module_name], 0, wx.ALL, 5)

    def _save_select(self, event):
        """保存选中的自动运行的程序的状态"""
        sender = event.GetEventObject()
        self.data['autorun'][sender.Label] = sender.GetValue()
        Cache().set("autorun", self.data['autorun'])

    def _add_advt_page(self):
        for mod_name, mod in self.mod_list.items():
            mod.set_advt_frame(self.advt_notebook)

    def _set_log(self):
        #从配置文件中设置log
        logging.config.dictConfig(Conf().get('logging'))

        handler = message_handler.MessageHandler(self.message_box)
        log = logging.getLogger()
        log.addHandler(handler)
        log.setLevel(logging.INFO)

    def _update_state(self):
        """自动更新各模块的状态显示"""
        for module_name in BaseModule.list_service_module():
            mod = self.mod_list[module_name]
            if mod.is_install():
                self.lbl[module_name].set_label(mod.get_state().lower())
            else:
                mod.install_service()
        wx.CallLater(3000, self._update_state)


app = wx.App()
frame = PPServ(None)
app.MainLoop()
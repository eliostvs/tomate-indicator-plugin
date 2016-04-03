from __future__ import unicode_literals

import logging
from locale import gettext as _

import tomate.plugin
from gi.repository import AppIndicator3, Gtk
from tomate.constant import State
from tomate.event import Events, on
from tomate.graph import graph
from tomate.utils import suppress_errors
from tomate.view import TrayIcon
from wiring import implements

logger = logging.getLogger(__name__)


def rounded_percent(percent):
    '''
    The icons show 5% steps, so we have to round.
    '''
    return percent - percent % 5


class IndicatorMenu(object):

    def __init__(self, view):
        self.view = view

        self.menu = Gtk.Menu(halign=Gtk.Align.CENTER)

        self.show_option = Gtk.MenuItem(_('Show'), visible=True)
        self.show_option.connect('activate', self._on_show_menu_activate)
        self.menu.add(self.show_option)

        self.hide_option = Gtk.MenuItem(_('Hide'), visible=False)
        self.hide_option.connect('activate', self._on_hide_menu_activate)
        self.menu.add(self.hide_option)

        self.menu.show_all()

    def _on_show_menu_activate(self, widget, view):
        self.active_hide_window_option()
        return self.view.show()

    def _on_hide_menu_activate(self, widget, view):
        self.active_show_window_option()
        return self.view.hide()

    def active_hide_window_option(self):
        self.hide_option.set_visible(True)
        self.show_option.set_visible(False)

    def active_show_window_option(self):
        self.hide_option.set_visible(False)
        self.show_option.set_visible(True)


@implements(TrayIcon)
class IndicatorPlugin(tomate.plugin.Plugin):

    @suppress_errors
    def __init__(self):
        super(IndicatorPlugin, self).__init__()

        self.view = graph.get("tomate.view")
        self.menu = IndicatorMenu(self.view)
        self.config = graph.get('tomate.config')
        self.indicator = self._build_indicator(self.menu)

    @suppress_errors
    def activate(self):
        super(IndicatorPlugin, self).activate()
        graph.register_instance(TrayIcon, self)

    @suppress_errors
    def deactivate(self):
        super(IndicatorPlugin, self).deactivate()
        graph.unregister_provider(TrayIcon)

    @suppress_errors
    @on(Events.Timer, [State.changed])
    def update_icon(self, sender=None, **kwargs):
        percent = int(kwargs.get('time_ratio', 0) * 100)

        if rounded_percent(percent) < 99:
            icon_name = self._icon_name_for(percent)
            self.indicator.set_icon(icon_name)

            logger.debug('set icon %s', icon_name)

    @suppress_errors
    @on(Events.Session, [State.started])
    def show(self, sender=None, **kwargs):
        self.menu.active_hide_window_option()
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

    @suppress_errors
    @on(Events.Session, [State.finished])
    @on(Events.Session, [State.stopped])
    def hide(self, sender=None, **kwargs):
        self.indicator.set_status(AppIndicator3.IndicatorStatus.PASSIVE)
        self.menu.active_show_window_option()

    def _icon_name_for(self, percent):
        return 'tomate-{0:02}'.format(rounded_percent(percent))

    def _build_indicator(self, menu):
        indicator = AppIndicator3.Indicator.new(
            'tomate',
            'tomate-indicator',
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS,
        )

        indicator.set_icon_theme_path(self.config.get_icon_paths()[0])
        indicator.set_menu(menu)

        return indicator

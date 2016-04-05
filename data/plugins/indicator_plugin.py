from __future__ import unicode_literals

import logging
from locale import gettext as _

import tomate.plugin
from gi.repository import AppIndicator3, Gtk
from tomate.constant import State
from tomate.event import Events, on
from tomate.graph import graph
from tomate.plugin import connect_events, disconnect_events
from tomate.utils import suppress_errors
from tomate.view import TrayIcon
from wiring import implements, inject

logger = logging.getLogger(__name__)


def rounded_percent(percent):
    """
    The icons show 5% steps, so we have to round.
    """
    return percent - percent % 5


class IndicatorMenu(object):

    def __init__(self, view):
        self.view = view
        self.menu = Gtk.Menu(halign=Gtk.Align.CENTER)

        self.show = Gtk.MenuItem(_('Show'), visible=False, no_show_all=True)
        self.show.connect('activate', self._on_show_menu_activate)
        self.menu.add(self.show)

        self.hide = Gtk.MenuItem(_('Hide'), visible=False, no_show_all=True)
        self.hide.connect('activate', self._on_hide_menu_activate)
        self.menu.add(self.hide)

        self._update_menus()

        self.menu.show_all()

    def _update_menus(self):
        if self.view.widget.get_visible():
            self.active_hide_menu()
        else:
            self.active_show_menu()

    def _on_show_menu_activate(self, widget):
        self.active_hide_menu()

        return self.view.show()

    def _on_hide_menu_activate(self, widget):
        self.active_show_menu()

        return self.view.hide()

    @on(Events.View, [State.showing])
    def active_hide_menu(self, sender=None, **kwargs):
        self.hide.set_visible(True)
        self.show.set_visible(False)

    @on(Events.View, [State.hiding])
    def active_show_menu(self, sender=None, **kwargs):
        self.hide.set_visible(False)
        self.show.set_visible(True)

    @property
    def widget(self):
        return self.menu


@implements(TrayIcon)
class IndicatorPlugin(tomate.plugin.Plugin):

    @suppress_errors
    def __init__(self):
        super(IndicatorPlugin, self).__init__()
        view = graph.get('tomate.view')

        self.menu = IndicatorMenu(view)

        self.config = graph.get('tomate.config')

        self.indicator = self._build_indicator()
        self.indicator.set_menu(self.menu.widget)
        self.indicator.set_icon_theme_path(self._get_first_icon_theme())

    @suppress_errors
    def activate(self):
        super(IndicatorPlugin, self).activate()
        graph.register_instance(TrayIcon, self)
        connect_events(self.menu)
        self.show()

    @suppress_errors
    def deactivate(self):
        super(IndicatorPlugin, self).deactivate()
        graph.unregister_provider(TrayIcon)
        disconnect_events(self.menu)
        self.hide()

    @suppress_errors
    @on(Events.Timer, [State.changed])
    def update_icon(self, sender=None, **kwargs):
        percent = int(kwargs.get('time_ratio', 0) * 100)

        if rounded_percent(percent) < 99:
            icon_name = self._icon_name_for(rounded_percent(percent))
            self.indicator.set_icon(icon_name)

            logger.debug('set icon %s', icon_name)

    @suppress_errors
    @on(Events.Session, [State.started])
    def show(self, sender=None, **kwargs):
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

    @suppress_errors
    @on(Events.Session, [State.finished, State.stopped])
    def hide(self, sender=None, **kwargs):
        self.indicator.set_status(AppIndicator3.IndicatorStatus.PASSIVE)

    def _get_first_icon_theme(self):
        return self.config.get_icon_paths()[0]

    @staticmethod
    def _icon_name_for(percent):
        return 'tomate-{0:02}'.format(percent)

    @staticmethod
    def _build_indicator():
        return AppIndicator3.Indicator.new(
            'tomate',
            'tomate-indicator',
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS,
        )

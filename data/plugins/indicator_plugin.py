from __future__ import unicode_literals

import logging
from locale import gettext as _

from gi.repository import AppIndicator3, Gtk
from wiring import implements

import tomate.plugin
from tomate.constant import State
from tomate.event import Events, on
from tomate.graph import graph
from tomate.utils import suppress_errors
from tomate.view import TrayIcon

logger = logging.getLogger(__name__)


@implements(TrayIcon)
class IndicatorPlugin(tomate.plugin.Plugin):

    @suppress_errors
    def __init__(self):
        super(IndicatorPlugin, self).__init__()

        self.view = graph.get('tomate.view')
        self.config = graph.get('tomate.config')
        self.indicator = self._build_indicator(self._build_menu())

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

        if self._rounded_percent(percent) < 99:
            icon_name = self._icon_name_for(percent)
            self.indicator.set_icon(icon_name)

            logger.debug('set icon %s', icon_name)

    @suppress_errors
    @on(Events.Session, [State.started])
    def show(self, sender=None, **kwargs):
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

    @suppress_errors
    @on(Events.Session, [State.finished])
    def hide(self, sender=None, **kwargs):
        self.indicator.set_status(AppIndicator3.IndicatorStatus.PASSIVE)

    def _rounded_percent(self, percent):
        '''
        The icons show 5% steps, so we have to round.
        '''
        return percent - percent % 5

    def _icon_name_for(self, percent):
        return 'tomate-{0:02}'.format(self._rounded_percent(percent))

    def _build_menu(self):
        menuitem = Gtk.MenuItem(_('Show'), visible=False)
        menuitem.connect('activate', self._on_show_menu_activate)

        menu = Gtk.Menu(halign=Gtk.Align.CENTER)
        menu.add(menuitem)
        menu.show_all()

        return menu

    def _build_indicator(self, menu):
        indicator = AppIndicator3.Indicator.new(
            'tomate',
            'tomate-indicator',
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS,
        )

        indicator.set_icon_theme_path(self.config.get_icon_paths()[0])
        indicator.set_menu(menu)

        return indicator

    def _on_show_menu_activate(self, widget=None):
        return self.view.show()

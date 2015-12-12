from __future__ import unicode_literals

import logging
from locale import gettext as _

from gi.repository import AppIndicator3, Gtk
from wiring import implements

from tomate.constant import State
from tomate.event import Events, on
from tomate.graph import graph
from tomate.plugin import Plugin
from tomate.utils import suppress_errors
from tomate.view import TrayIcon

logger = logging.getLogger(__name__)


@implements(TrayIcon)
class IndicatorPlugin(Plugin):

    @suppress_errors
    def __init__(self):
        super(IndicatorPlugin, self).__init__()

        self.view = graph.get('tomate.view')
        self.config = graph.get('tomate.config')

        menuitem = Gtk.MenuItem(_('Show'), visible=False)
        menuitem.connect('activate', self.on_show_menu_activate)
        menu = Gtk.Menu(halign=Gtk.Align.CENTER)
        menu.add(menuitem)

        menu.show_all()

        self.indicator = AppIndicator3.Indicator.new(
                'tomate',
                'tomate-indicator',
                AppIndicator3.IndicatorCategory.APPLICATION_STATUS,
        )

        self.indicator.set_icon_theme_path(self.config.get_icon_paths()[0])
        self.indicator.set_menu(menu)

    def on_show_menu_activate(self, widget=None):
        return self.view.show()

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

        # The icons show 5% steps, so we have to round
        rounded_percent = percent - percent % 5

        # There is no icon for 100%
        if rounded_percent < 99:
            icon_name = 'tomate-{0:02}'.format(rounded_percent)
            self.indicator.set_icon(icon_name)

            logger.debug('set icon %s', icon_name)

    @on(Events.View, [State.hiding])
    def show(self, sener=None, **kwargs):
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

    @on(Events.Session, [State.finished])
    @on(Events.View, [State.showing])
    def hide(self, sender=None, **kwargs):
        self.indicator.set_status(AppIndicator3.IndicatorStatus.PASSIVE)

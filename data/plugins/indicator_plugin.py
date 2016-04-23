from __future__ import unicode_literals

import logging

import tomate.plugin
from gi.repository import AppIndicator3
from tomate.constant import State
from tomate.event import Events, on
from tomate.graph import graph
from tomate.plugin import connect_events, disconnect_events
from tomate.utils import rounded_percent, suppress_errors
from tomate.view import TrayIcon
from wiring import implements

logger = logging.getLogger(__name__)


@implements(TrayIcon)
class IndicatorPlugin(tomate.plugin.Plugin):

    @suppress_errors
    def __init__(self):
        super(IndicatorPlugin, self).__init__()

        self.menu = graph.get('view.menu')
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

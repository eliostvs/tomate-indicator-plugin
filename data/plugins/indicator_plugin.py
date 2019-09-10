import logging

import gi

gi.require_version("AppIndicator3", "0.1")

from gi.repository import AppIndicator3
from wiring import implements

from tomate.pomodoro import State
from tomate.pomodoro.event import Events, on
from tomate.pomodoro.graph import graph
from tomate.pomodoro.plugin import Plugin, connect_events, disconnect_events, suppress_errors
from tomate.pomodoro.timer import TimerPayload
from tomate.ui.widgets import TrayIcon

logger = logging.getLogger(__name__)


@implements(TrayIcon)
class IndicatorPlugin(Plugin):
    @suppress_errors
    def __init__(self):
        super(IndicatorPlugin, self).__init__()

        self.menu = graph.get("trayicon.menu")
        self.config = graph.get("tomate.config")
        self.session = graph.get("tomate.session")

        self.widget = self._build_widget()

    @suppress_errors
    def activate(self):
        super(IndicatorPlugin, self).activate()

        graph.register_instance(TrayIcon, self)
        connect_events(self.menu)

        self._show_if_session_is_running()

    @suppress_errors
    def deactivate(self):
        super(IndicatorPlugin, self).deactivate()

        graph.unregister_provider(TrayIcon)
        disconnect_events(self.menu)

        self.hide()

    @suppress_errors
    @on(Events.Timer, [State.changed])
    def update_icon(self, _, payload: TimerPayload):
        icon_name = self._icon_name_for(payload.elapsed_percent)
        self.widget.set_icon(icon_name)

        logger.debug("action=set_icon name=%s", icon_name)

    @suppress_errors
    @on(Events.Session, [State.started])
    def show(self, *args, **kwargs):
        self.widget.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

    @suppress_errors
    @on(Events.Session, [State.finished, State.stopped])
    def hide(self, *args, **kwargs):
        self.widget.set_status(AppIndicator3.IndicatorStatus.PASSIVE)
        self.widget.set_icon("tomate-idle")

    @staticmethod
    def _icon_name_for(percent):
        return "tomate-{0:.0f}".format(percent)

    def _build_widget(self):
        indicator = AppIndicator3.Indicator.new(
            "tomate", "tomate-idle", AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )

        indicator.set_menu(self.menu.widget)
        indicator.set_icon_theme_path(self._get_first_icon_theme())

        return indicator

    def _get_first_icon_theme(self):
        return self.config.get_icon_paths()[0]

    def _show_if_session_is_running(self):
        if self.session.is_running():
            self.show()
        else:
            self.hide()

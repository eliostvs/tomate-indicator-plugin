import logging

import gi

gi.require_version("AppIndicator3", "0.1")

from gi.repository import AppIndicator3
from wiring import implements

from tomate.pomodoro.event import Events, on
from tomate.pomodoro.graph import graph
from tomate.pomodoro.plugin import Plugin, suppress_errors
from tomate.pomodoro.timer import Payload as TimerPayload
from tomate.ui import Systray

logger = logging.getLogger(__name__)


@implements(Systray)
class IndicatorPlugin(Plugin):
    # @suppress_errors
    def __init__(self):
        super(IndicatorPlugin, self).__init__()

        self.menu = graph.get("tomate.ui.systray.menu")
        self.config = graph.get("tomate.config")
        self.session = graph.get("tomate.session")
        self.bus = graph.get("tomate.bus")
        self.widget = self.create_widget()

    @suppress_errors
    def activate(self):
        super(IndicatorPlugin, self).activate()

        graph.register_instance(Systray, self)
        self.menu.connect(self.bus)
        self.show_if_session_is_running()

    def show_if_session_is_running(self):
        if self.session.is_running():
            self.show()
        else:
            self.hide()

    @suppress_errors
    def deactivate(self):
        super(IndicatorPlugin, self).deactivate()

        graph.unregister_provider(Systray)
        self.menu.disconnect(self.bus)
        self.hide()

    @suppress_errors
    @on(Events.TIMER_UPDATE)
    def update_icon(self, _, payload: TimerPayload):
        icon_name = self.icon_name_for(payload.elapsed_percent)
        self.widget.set_icon(icon_name)
        logger.debug("action=set_icon name=%s", icon_name)

    @suppress_errors
    @on(Events.SESSION_START)
    def show(self, *_, **__):
        logger.debug("action=show")
        self.widget.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

    @suppress_errors
    @on(Events.SESSION_END, Events.SESSION_INTERRUPT)
    def hide(self, *_, **__):
        logger.debug("action=hide")
        self.widget.set_status(AppIndicator3.IndicatorStatus.PASSIVE)
        self.widget.set_icon("tomate-idle")

    @staticmethod
    def icon_name_for(percent):
        return "tomate-{0:.0f}".format(percent)

    def create_widget(self):
        indicator = AppIndicator3.Indicator.new(
            "tomate", "tomate-idle", AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )

        indicator.set_menu(self.menu.widget)
        indicator.set_icon_theme_path(self.first_icon_theme_path())
        return indicator

    def first_icon_theme_path(self):
        return self.config.icon_paths()[0]

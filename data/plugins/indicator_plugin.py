import logging

import gi

gi.require_version("AppIndicator3", "0.1")

from gi.repository import AppIndicator3

import tomate.pomodoro.plugin as plugin
from tomate.pomodoro import Events, on, Bus, graph, suppress_errors, TimerPayload
from tomate.ui import Systray

logger = logging.getLogger(__name__)


class IndicatorPlugin(plugin.Plugin):
    @suppress_errors
    def __init__(self):
        super(IndicatorPlugin, self).__init__()
        self.menu = graph.get("tomate.ui.systray.menu")
        self.config = graph.get("tomate.config")
        self.session = graph.get("tomate.session")
        self.widget = self.create_widget()

    def connect(self, bus: Bus) -> None:
        super().connect(bus)
        self.menu.connect(bus)

    def disconnect(self, bus: Bus) -> None:
        self.menu.disconnect(bus)
        super().disconnect(bus)

    @suppress_errors
    def activate(self):
        super(IndicatorPlugin, self).activate()
        graph.register_instance(Systray, self)

        if self.session.is_running():
            self.show()
        else:
            self.hide()

    @suppress_errors
    def deactivate(self):
        super(IndicatorPlugin, self).deactivate()
        graph.unregister_provider(Systray)
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
        return "tomate-{:02.0f}".format(percent)

    def create_widget(self):
        indicator = AppIndicator3.Indicator.new(
            "tomate", "tomate-idle", AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )

        indicator.set_menu(self.menu.widget)
        indicator.set_icon_theme_path(self.first_icon_theme_path())
        return indicator

    def first_icon_theme_path(self):
        return self.config.icon_paths()[0]

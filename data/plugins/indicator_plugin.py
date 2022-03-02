import logging

import gi

gi.require_version("AppIndicator3", "0.1")

from wiring import Graph
from gi.repository import AppIndicator3

import tomate.pomodoro.plugin as plugin
from tomate.pomodoro import Events, on, Bus, suppress_errors, TimerPayload
from tomate.ui import Systray

logger = logging.getLogger(__name__)


class IndicatorPlugin(plugin.Plugin):
    @suppress_errors
    def __init__(self):
        super().__init__()
        self.menu = None
        self.config = None
        self.session = None
        self.indicator = None

    def configure(self, bus: Bus, graph: Graph) -> None:
        super().configure(bus, graph)

        self.menu = graph.get("tomate.ui.systray.menu")
        self.config = graph.get("tomate.config")
        self.session = graph.get("tomate.session")
        self.indicator = self.create_widget()

    @suppress_errors
    def activate(self):
        logger.debug("action=active")
        super().activate()

        self.menu.connect(self.bus)
        self.graph.register_instance(Systray, self)
        if self.session.is_running():
            self.show()
        else:
            self.hide()

    @suppress_errors
    def deactivate(self):
        logger.debug("action=deactivate")
        super().deactivate()

        self.menu.disconnect(self.bus)
        self.graph.unregister_provider(Systray)
        self.hide()

    @suppress_errors
    @on(Events.TIMER_UPDATE)
    def update_icon(self, payload: TimerPayload):
        logger.debug("action=update-icon payload=%s", payload)

        icon_name = self.icon_name(payload.elapsed_percent)
        if icon_name != self.indicator.get_icon():
            self.indicator.set_icon(icon_name)

    @suppress_errors
    @on(Events.SESSION_START)
    def show(self, **__):
        logger.debug("action=show")

        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

    @suppress_errors
    @on(Events.SESSION_END, Events.SESSION_INTERRUPT)
    def hide(self, **__):
        logger.debug("action=hide")

        self.indicator.set_status(AppIndicator3.IndicatorStatus.PASSIVE)
        self.indicator.set_icon("tomate-idle")

    @staticmethod
    def icon_name(percent):
        return "tomate-{:02.0f}".format(percent)

    def create_widget(self):
        indicator = AppIndicator3.Indicator.new(
            "tomate", "tomate-idle", AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )

        indicator.set_icon_theme_path(self.first_icon_theme_path())
        indicator.set_menu(self.menu.widget)
        return indicator

    def first_icon_theme_path(self):
        return self.config.icon_paths()[0]

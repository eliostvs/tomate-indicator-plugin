import pytest
from blinker import NamedSignal
from gi.repository import AppIndicator3, Gtk

from tomate.pomodoro.config import Config
from tomate.pomodoro.event import Events
from tomate.pomodoro.graph import graph
from tomate.pomodoro.session import Session
from tomate.pomodoro.timer import Payload as TimerPayload
from tomate.ui import Systray, SystrayMenu


@pytest.fixture
def bus():
    return NamedSignal("Test")


@pytest.fixture()
def menu(mocker):
    return mocker.Mock(spec=SystrayMenu, widget=Gtk.Menu())


@pytest.fixture
def session(mocker):
    return mocker.Mock(spec=Session)


@pytest.fixture
def subject(bus, menu, session):
    graph.providers.clear()
    graph.register_instance("tomate.bus", bus)
    graph.register_instance("tomate.config", Config(bus))
    graph.register_instance("tomate.session", session)
    graph.register_instance("tomate.ui.systray.menu", menu)

    import indicator_plugin

    return indicator_plugin.IndicatorPlugin()


@pytest.mark.parametrize(
    "time_left,duration,icon_name",
    [
        (100, 100, "tomate-00"),
        (95, 100, "tomate-05"),
        (90, 100, "tomate-10"),
        (85, 100, "tomate-15"),
        (80, 100, "tomate-20"),
        (75, 100, "tomate-25"),
        (70, 100, "tomate-30"),
        (65, 100, "tomate-35"),
        (60, 100, "tomate-40"),
        (55, 100, "tomate-45"),
        (50, 100, "tomate-50"),
        (45, 100, "tomate-55"),
        (40, 100, "tomate-60"),
        (35, 100, "tomate-65"),
        (30, 100, "tomate-70"),
        (25, 100, "tomate-75"),
        (20, 100, "tomate-80"),
        (10, 100, "tomate-90"),
        (5, 100, "tomate-95"),
    ],
)
def test_change_icon_when_timer_change(time_left, duration, icon_name, bus, subject):
    subject.activate()

    bus.send(Events.TIMER_UPDATE, payload=TimerPayload(time_left=time_left, duration=duration))

    assert subject.widget.get_icon() == icon_name


def test_show_when_session_start(bus, subject):
    subject.activate()
    subject.widget.set_status(AppIndicator3.IndicatorStatus.PASSIVE)

    bus.send(Events.SESSION_START)

    assert subject.widget.get_status() == AppIndicator3.IndicatorStatus.ACTIVE


@pytest.mark.parametrize("event", [Events.SESSION_END, Events.SESSION_INTERRUPT])
def test_hide_when_session_end(event, bus, subject):
    subject.activate()
    subject.widget.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

    bus.send(event)

    assert subject.widget.get_status() == AppIndicator3.IndicatorStatus.PASSIVE
    assert subject.widget.get_icon() == "tomate-idle"


class TestActivePlugin:
    def test_register_tray_provider(self, subject):
        subject.activate()

        assert Systray in graph.providers.keys()
        assert graph.get(Systray) == subject
        assert subject.widget.get_category() is AppIndicator3.IndicatorCategory.APPLICATION_STATUS

    def test_show_when_session_is_running(self, session, subject):
        session.is_running.return_value = True
        subject.widget.set_status(AppIndicator3.IndicatorStatus.PASSIVE)

        subject.activate()

        assert subject.widget.get_status() == AppIndicator3.IndicatorStatus.ACTIVE

    def test_hide_when_session_is_not_running(self, session, subject):
        session.is_running.return_value = False
        subject.widget.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

        subject.activate()

        assert subject.widget.get_status() == AppIndicator3.IndicatorStatus.PASSIVE

    def test_connect_menu_events(self, bus, menu, subject):
        subject.activate()

        menu.connect.assert_called_once_with(bus)


class TestDeactivatePlugin:
    def test_unregister_systray_provider(self, subject):
        graph.register_instance(Systray, subject)

        subject.deactivate()

        assert Systray not in graph.providers.keys()

    def test_hide_indicator(self, subject):
        graph.register_instance(Systray, subject)
        subject.widget.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

        subject.deactivate()

        assert subject.widget.get_status() == AppIndicator3.IndicatorStatus.PASSIVE

    def test_disconnect_menu_events(self, bus, menu, subject):
        graph.register_instance(Systray, subject)

        subject.deactivate()

        menu.disconnect.assert_called_once_with(bus)

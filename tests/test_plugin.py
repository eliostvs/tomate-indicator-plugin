import pytest
from blinker import Namespace
from gi.repository import AppIndicator3, Gtk

from tomate.pomodoro import State
from tomate.pomodoro.config import Config
from tomate.pomodoro.event import Events
from tomate.pomodoro.graph import graph
from tomate.pomodoro.session import Session
from tomate.pomodoro.timer import TimerPayload
from tomate.ui.widgets import TrayIcon


@pytest.fixture()
def dispatcher():
    return Namespace().signal("dispatcher")


@pytest.fixture
def menu(mocker):
    return mocker.Mock(widget=Gtk.Menu())


@pytest.fixture
def session(mocker):
    return mocker.Mock(Session)


@pytest.fixture
def subject(menu, session, dispatcher):
    from indicator_plugin import IndicatorPlugin

    graph.providers.clear()

    graph.register_instance("tomate.config", Config(dispatcher))
    graph.register_instance("tomate.session", session)
    graph.register_instance("trayicon.menu", menu)

    Events.Session.receivers.clear()
    Events.Timer.receivers.clear()

    return IndicatorPlugin()


def test_should_update_indicator_icon_when_timer_changes(subject):
    subject.activate()
    payload = TimerPayload(time_left=1, duration=10)

    Events.Timer.send(State.changed, payload=payload)

    assert subject.widget.get_icon() == "tomate-90"


def test_should_show_widget_when_session_starts(subject):
    subject.activate()
    subject.widget.set_status(AppIndicator3.IndicatorStatus.PASSIVE)

    Events.Session.send(State.started)

    assert subject.widget.get_status() == AppIndicator3.IndicatorStatus.ACTIVE


@pytest.mark.parametrize("event", [State.finished, State.stopped])
def test_should_hide_widget_when_session_ends(event, subject):
    subject.activate()
    subject.widget.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

    Events.Session.send(event)

    assert subject.widget.get_status() == AppIndicator3.IndicatorStatus.PASSIVE
    assert subject.widget.get_icon() == "tomate-idle"


class TestActivePlugin:
    def test_should_register_tray_icon_provider(self, subject):
        subject.activate()

        assert TrayIcon in graph.providers.keys()
        assert graph.get(TrayIcon) == subject
        assert subject.widget.get_category() is AppIndicator3.IndicatorCategory.APPLICATION_STATUS

    def test_should_show_indicator_when_session_is_running(self, subject, session):
        session.is_running.return_value = True
        subject.widget.set_status(AppIndicator3.IndicatorStatus.PASSIVE)

        subject.activate()

        assert subject.widget.get_status() == AppIndicator3.IndicatorStatus.ACTIVE

    def test_should_connect_menu_events(self, subject, mocker):
        connect_events = mocker.patch("indicator_plugin.connect_events")

        subject.activate()

        connect_events.assert_called_once_with(subject.menu)

    def test_should_hide_indicator_when_session_is_not_running(self, subject, session):
        session.is_running.return_value = False
        subject.widget.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

        subject.activate()

        assert subject.widget.get_status() == AppIndicator3.IndicatorStatus.PASSIVE


class TestDeactivatePlugin:
    def test_should_unregister_tray_icon(self, subject):
        graph.register_instance(TrayIcon, subject)

        subject.deactivate()

        assert TrayIcon not in graph.providers.keys()

    def test_should_hide_indicator(self, subject):
        graph.register_instance(TrayIcon, subject)
        subject.widget.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

        subject.deactivate()

        assert subject.widget.get_status() == AppIndicator3.IndicatorStatus.PASSIVE

    def test_should_disconnect_menu_events(self, mocker, subject):
        disconnect_events = mocker.patch("indicator_plugin.disconnect_events")
        subject.activate()

        subject.deactivate()

        disconnect_events.assert_called_once_with(subject.menu)

import pytest
from gi.repository import AppIndicator3

from tomate.pomodoro import State
from tomate.pomodoro.event import Events
from tomate.pomodoro.graph import graph
from tomate.pomodoro.session import Session
from tomate.pomodoro.timer import TimerPayload
from tomate.ui.widgets import TrayIcon


@pytest.fixture
def mock_menu(mocker):
    return mocker.Mock(widget="widget")


@pytest.fixture
def mock_session(mocker):
    return mocker.Mock(Session)


@pytest.fixture
def mock_config(mocker):
    return mocker.Mock(**{"get_icon_paths.return_value": ["get-icon-path"]})


@pytest.fixture
def subject(mocker, mock_menu, mock_session, mock_config):
    mocker.patch("indicator_plugin.AppIndicator3.Indicator")

    from indicator_plugin import IndicatorPlugin

    graph.providers.clear()

    graph.register_instance("tomate.config", mock_config)
    graph.register_instance("tomate.session", mock_session)
    graph.register_instance("trayicon.menu", mock_menu)

    Events.Session.receivers.clear()
    Events.Timer.receivers.clear()

    return IndicatorPlugin()


def test_indicator_creation(subject, mock_menu, mock_config):
    from indicator_plugin import AppIndicator3

    AppIndicator3.Indicator.new.assert_called_once_with(
        "tomate", "tomate-idle", AppIndicator3.IndicatorCategory.APPLICATION_STATUS
    )

    AppIndicator3.Indicator.new.return_value.set_menu.assert_called_once_with(
        mock_menu.widget
    )
    AppIndicator3.Indicator.new.return_value.set_icon_theme_path.assert_called_once_with(
        "get-icon-path"
    )


def test_should_update_indicator_icon_when_timer_changes(subject):
    # given
    subject.activate()
    payload = TimerPayload(time_left=1, duration=10)

    # when
    Events.Timer.send(State.changed, payload=payload)

    # then
    subject.widget.set_icon.assert_called_with("tomate-90")


def test_should_show_widget_when_session_starts(subject):
    # given
    subject.activate()
    subject.widget.reset_mock()

    # when
    Events.Session.send(State.started)

    # then
    subject.widget.set_status.assert_called_once_with(
        AppIndicator3.IndicatorStatus.ACTIVE
    )


def test_should_hide_widget_when_session_ends(subject):
    for event_type in [State.finished, State.stopped]:
        # given
        subject.activate()
        subject.widget.reset_mock()

        # when
        Events.Session.send(event_type)

        # then
        subject.widget.set_status.assert_called_once_with(
            AppIndicator3.IndicatorStatus.PASSIVE
        )
        subject.widget.set_icon("tomate-idle")


class TestActivePlugin:
    def test_should_register_tray_icon_provider(self, subject):
        # when
        subject.activate()

        # then
        assert TrayIcon in graph.providers.keys()
        assert graph.get(TrayIcon) == subject

    def test_should_show_indicator_when_session_is_running(self, subject, mock_session):
        # given
        mock_session.is_running.return_value = True

        # when
        subject.activate()

        # then
        subject.widget.set_status.assert_called_once_with(
            AppIndicator3.IndicatorStatus.ACTIVE
        )

    def test_should_connect_menu_events(self, subject, mocker):
        connect_events = mocker.patch("indicator_plugin.connect_events")

        subject.activate()

        connect_events.assert_called_once_with(subject.menu)

    def test_should_hide_indicator_when_session_is_not_running(
        self, subject, mock_session
    ):
        # given
        mock_session.is_running.return_value = False

        # when
        subject.activate()

        # when
        subject.widget.set_status.assert_called_once_with(
            AppIndicator3.IndicatorStatus.PASSIVE
        )


class TestDeactivatePlugin:
    def test_should_unregister_tray_icon(self, subject):
        # given
        graph.register_instance(TrayIcon, subject)

        # when
        subject.deactivate()

        # then
        assert TrayIcon not in graph.providers.keys()

    def test_should_hide_indicator(self, subject):
        # given
        graph.register_instance(TrayIcon, subject)

        # when
        subject.deactivate()

        # then
        subject.widget.set_status.assert_called_once_with(
            AppIndicator3.IndicatorStatus.PASSIVE
        )

    def test_should_disconnect_menu_events(self, mocker, subject):
        # given
        disconnect_events = mocker.patch("indicator_plugin.disconnect_events")
        subject.activate()

        # when
        subject.deactivate()

        # then
        disconnect_events.assert_called_once_with(subject.menu)

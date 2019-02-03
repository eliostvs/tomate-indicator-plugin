from unittest.mock import Mock, patch

import pytest
from gi.repository import AppIndicator3

from tomate.constant import State
from tomate.event import Events
from tomate.graph import graph
from tomate.session import Session
from tomate.timer import TimerPayload
from tomate.view import TrayIcon


def setup_function(function):
    graph.providers.clear()

    graph.register_instance('tomate.config', Mock(**{'get_icon_paths.return_value': ['']}))
    graph.register_instance('tomate.session', Mock(Session))
    graph.register_instance('trayicon.menu', Mock())

    Events.Session.receivers.clear()
    Events.Timer.receivers.clear()


@pytest.fixture
def session():
    return graph.get('tomate.session')


@pytest.fixture
@patch('indicator_plugin.AppIndicator3.Indicator')
def plugin(indicator):
    from indicator_plugin import IndicatorPlugin

    return IndicatorPlugin()


def test_should_update_indicator_icon_when_timer_changes(plugin):
    # given
    plugin.activate()
    payload = TimerPayload(time_left=1, duration=10)

    # when
    Events.Timer.send(State.changed, payload=payload)

    # then
    plugin.widget.set_icon.assert_called_with('tomate-90')


def test_should_show_widget_when_session_starts(plugin):
    # given
    plugin.activate()
    plugin.widget.reset_mock()

    # when
    Events.Session.send(State.started)

    # then
    plugin.widget.set_status.assert_called_once_with(AppIndicator3.IndicatorStatus.ACTIVE)


def test_should_hide_widget_when_session_ends(plugin):
    for event_type in [State.finished, State.stopped]:
        # given
        plugin.activate()
        plugin.widget.reset_mock()

        # when
        Events.Session.send(event_type)

        # then
        plugin.widget.set_status.assert_called_once_with(AppIndicator3.IndicatorStatus.PASSIVE)
        plugin.widget.set_icon("tomate-idle")


class TestActivePlugin:
    def setup_method(self, method):
        setup_function(method)

    def test_should_register_tray_icon_provider(self, plugin):
        # when
        plugin.activate()

        # then
        assert TrayIcon in graph.providers.keys()
        assert graph.get(TrayIcon) == plugin

    def test_should_show_indicator_when_session_is_running(self, plugin, session):
        # given
        session.is_running.return_value = True

        # when
        plugin.activate()

        # then
        plugin.widget.set_status.assert_called_once_with(AppIndicator3.IndicatorStatus.ACTIVE)

    @patch('indicator_plugin.connect_events')
    def test_should_connect_menu_events(self, connect_events, plugin):
        plugin.activate()

        connect_events.assert_called_once_with(plugin.menu)

    def test_should_hide_indicator_when_session_is_not_running(self, plugin, session):
        # given
        session.is_running.return_value = False

        # when
        plugin.activate()

        # when
        plugin.widget.set_status.assert_called_once_with(AppIndicator3.IndicatorStatus.PASSIVE)


class TestDeactivatePlugin:
    def setup_method(self, method):
        setup_function(method)

    def test_should_unregister_tray_icon(self, plugin):
        # given
        graph.register_instance(TrayIcon, plugin)

        # when
        plugin.deactivate()

        # then
        assert TrayIcon not in graph.providers.keys()

    def test_should_hide_indicator(self, plugin):
        # given
        graph.register_instance(TrayIcon, plugin)

        # when
        plugin.deactivate()

        # then
        plugin.widget.set_status.assert_called_once_with(AppIndicator3.IndicatorStatus.PASSIVE)

    @patch('indicator_plugin.disconnect_events')
    def test_should_disconnect_menu_events(self, disconnect_events, plugin):
        # given
        plugin.activate()

        # when
        plugin.deactivate()

        # then
        disconnect_events.assert_called_once_with(plugin.menu)

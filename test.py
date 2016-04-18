from __future__ import unicode_literals

import pytest
from gi.repository import AppIndicator3
from mock import Mock, patch
from tomate.constant import State
from tomate.event import Events
from tomate.graph import graph
from tomate.view import TrayIcon


def setup_function(function):
    graph.providers.clear()

    graph.register_instance('tomate.config', Mock(**{'get_icon_paths.return_value': ['']}))
    graph.register_instance('tomate.view', Mock())
    graph.register_instance('trayicon.menu', Mock())

    Events.Session.receivers.clear()
    Events.Timer.receivers.clear()
    Events.View.receivers.clear()


@pytest.fixture()
@patch('indicator_plugin.AppIndicator3.Indicator')
def plugin(Indicator):

    from indicator_plugin import IndicatorPlugin

    return IndicatorPlugin()


def method_called(result):
    return result[0][0]


def test_should_update_indicator_icon_when_plugin_update(plugin):
    plugin.update_icon(time_ratio=0.5)
    plugin.indicator.set_icon.assert_called_with('tomate-50')

    plugin.update_icon(time_ratio=0.9)
    plugin.indicator.set_icon.assert_called_with('tomate-90')


def test_should_change_indicator_status_active_when_plugin_shows(plugin):
    plugin.show()

    plugin.indicator.set_status.assert_called_once_with(AppIndicator3.IndicatorStatus.ACTIVE)


def test_should_change_indicator_passive_when_plugin_hid(plugin):
    plugin.hide()

    plugin.indicator.set_status.assert_called_once_with(AppIndicator3.IndicatorStatus.PASSIVE)


def test_should_register_plugin_when_activate(plugin):
    plugin.activate()

    assert TrayIcon in graph.providers.keys()
    assert graph.get(TrayIcon) == plugin


def test_should_unregister_when_plugin_deactivate(plugin):
    graph.register_instance(TrayIcon, plugin)

    plugin.deactivate()

    assert TrayIcon not in graph.providers.keys()


def test_should_show_indicator_when_plugin_activate(plugin):
    plugin.activate()

    plugin.indicator.set_status.assert_called_once_with(AppIndicator3.IndicatorStatus.ACTIVE)


def test_should_hide_indicator_when_plugin_deactivate(plugin):
    graph.register_instance(TrayIcon, plugin)

    plugin.deactivate()

    plugin.indicator.set_status.assert_called_once_with(AppIndicator3.IndicatorStatus.PASSIVE)


def test_should_call_update_icon_when_time_changed(plugin):
    plugin.activate()

    result = Events.Timer.send(State.changed)

    assert len(result) == 1
    assert plugin.update_icon == method_called(result)


def test_should_call_show_when_session_started(plugin):
    plugin.activate()

    result = Events.Session.send(State.started)

    assert len(result) == 1
    assert plugin.show == method_called(result)


def test_should_call_hide_when_timer_finished(plugin):
    plugin.activate()

    result = Events.Session.send(State.finished)

    assert len(result) == 1
    assert plugin.hide == method_called(result)


def test_should_call_hide_when_timer_stopped(plugin):
    plugin.activate()

    result = Events.Session.send(State.stopped)

    assert len(result) == 1
    assert plugin.hide == method_called(result)

from __future__ import unicode_literals

import pytest
from gi.repository import AppIndicator3, Gtk
from mock import Mock, patch
from tomate.constant import State
from tomate.event import Events
from tomate.graph import graph
from tomate.view import TrayIcon



@pytest.mark.parametrize('input, expected', [
    (1, 0),
    (8, 5),
    (10, 10),
    (11, 10),
    (14, 10),
    (15, 15),
    (16, 15),
])
def test_rounded_percent(input, expected):
    from indicator_plugin import rounded_percent

    assert rounded_percent(input) == expected


@pytest.fixture()
def menu_indicator():
    from indicator_plugin import IndicatorMenu

    view = Mock()
    menu = IndicatorMenu(view)

    return view, menu


class TestIndicatorMenu:

    def test_should_call_plugin_view_when_menu_activate(self, menu_indicator):
        view, menu = menu_indicator

        menu._on_show_menu_activate(None, view)

        view.show.assert_called_once()

        assert menu.hide_option.get_visible() == True
        assert menu.show_option.get_visible() == False

    def test_should_call_view_hide_menu_activate(self, menu_indicator):
        view, menu = menu_indicator

        menu._on_hide_menu_activate(None, view)

        view.hide.assert_called_once()

        assert menu.hide_option.get_visible() == False
        assert menu.show_option.get_visible() == True


@patch('indicator_plugin.AppIndicator3.Indicator')
@pytest.fixture(scope='function')
def plugin(mock_indicator):
    graph.providers.clear()

    graph.register_instance('tomate.config', Mock(**{'get_icon_paths.return_value': ['']}))
    graph.register_instance('tomate.view', Mock())

    Events.Session.receivers.clear()
    Events.Timer.receivers.clear()

    from indicator_plugin import IndicatorPlugin

    plugin = IndicatorPlugin()

    return plugin


class TestIndicatorPlugin:

    def test_should_update_indicator_icon_when_plugin_update(self, plugin):
        plugin.update_icon(time_ratio=0.5)
        plugin.indicator.set_icon.assert_called_with('tomate-50')

        plugin.update_icon(time_ratio=0.9)
        plugin.indicator.set_icon.assert_called_with('tomate-90')

    def test_should_change_indicator_status_active_when_plugin_shows(self, plugin):
        plugin.show()

        plugin.indicator.set_status.assert_called_once_with(AppIndicator3.IndicatorStatus.ACTIVE)

    def test_should_change_indicator_passive_when_plugin_hid(self, plugin):
        plugin.hide()

        plugin.indicator.set_status.assert_called_once_with(AppIndicator3.IndicatorStatus.PASSIVE)

    def test_should_register_plugin_when_active(self, plugin):
        plugin.activate()

        assert TrayIcon in graph.providers.keys()
        assert graph.get(TrayIcon) == plugin

    def test_should_unregister_when_plugin_deactive(self, plugin):
        graph.register_instance(TrayIcon, plugin)

        plugin.deactivate()

        assert TrayIcon not in graph.providers.keys()


class TestIntegrationIndicatorPlugin:

    @staticmethod
    def method_called(result):
        return result[0][0]

    def test_should_call_update_icon_when_time_changed(self, plugin):
        plugin.activate()

        result = Events.Timer.send(State.changed)

        assert len(result) == 1
        assert plugin.update_icon == self.method_called(result)

    def test_should_call_show_when_session_started(self, plugin):
        plugin.activate()

        result = Events.Session.send(State.started)

        assert len(result) == 1
        assert plugin.show == self.method_called(result)

    def test_should_call_hide_when_timer_finished(self, plugin):
        plugin.activate()

        result = Events.Session.send(State.finished)

        assert len(result) == 1
        assert plugin.hide == self.method_called(result)

    def test_should_call_hide_when_timer_stopped(self, plugin):
        plugin.activate()

        result = Events.Session.send(State.stopped)

        assert len(result) == 1
        assert plugin.hide == self.method_called(result)

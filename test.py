from __future__ import unicode_literals

import unittest

from gi.repository import AppIndicator3
from mock import Mock, patch
from tomate.constant import State
from tomate.event import Events
from tomate.graph import graph
from tomate.view import TrayIcon


def make_indicator():
    graph.providers.clear()

    graph.register_instance('tomate.config', Mock(**{'get_icon_paths.return_value': ['']}))
    graph.register_instance('tomate.view', Mock())

    Events.Session.receivers.clear()
    Events.Timer.receivers.clear()

    from indicator_plugin import IndicatorPlugin

    plugin = IndicatorPlugin()

    return plugin


@patch('indicator_plugin.AppIndicator3.Indicator')
class IndicatorPluginTest(unittest.TestCase):

    def test_should_update_indicator_icon_when_plugin_update(self, mock_indicator):
        plugin = make_indicator()

        plugin.update_icon(time_ratio=0.5)
        plugin.indicator.set_icon.assert_called_with('tomate-50')

        plugin.update_icon(time_ratio=0.9)
        plugin.indicator.set_icon.assert_called_with('tomate-90')

    def test_should_change_indicator_status_active_when_plugin_shows(self, mock_indicator):
        plugin = make_indicator()

        plugin.show()

        plugin.indicator.set_status.assert_called_once_with(AppIndicator3.IndicatorStatus.ACTIVE)

    def test_should_change_indicator_passive_when_plugin_hid(self, mock_indicator):
        plugin = make_indicator()

        plugin.hide()

        plugin.indicator.set_status.assert_called_once_with(AppIndicator3.IndicatorStatus.PASSIVE)

    def test_should_register_plugin_when_active(self, mock_indicator):
        plugin = make_indicator()

        plugin.activate()

        self.assertIn(TrayIcon, graph.providers.keys())
        self.assertEqual(graph.get(TrayIcon), plugin)

    def test_should_unregister_when_plugin_deactive(self, mock_indicator):
        plugin = make_indicator()

        graph.register_instance(TrayIcon, plugin)

        plugin.deactivate()

        self.assertNotIn(TrayIcon, graph.providers.keys())

    def test_should_call_plugin_view_when_menu_activate(self, mock_indicator):
        plugin = make_indicator()

        plugin._on_show_menu_activate()

        plugin.view.show.assert_called_once_with()


@patch('indicator_plugin.AppIndicator3.Indicator')
class IndicatorPluginIntegrationTest(unittest.TestCase):

    @staticmethod
    def method_called(result):
        return result[0][0]

    def test_should_call_update_icon_when_time_changed(self, mock_indicator=None):
        plugin = make_indicator()
        plugin.activate()

        result = Events.Timer.send(State.changed)

        self.assertEqual(1, len(result))
        self.assertEqual(plugin.update_icon, self.method_called(result))

    def test_should_call_show_when_session_started(self, mock_indicator=None):
        plugin = make_indicator()
        plugin.activate()

        result = Events.Session.send(State.started)

        self.assertEqual(1, len(result))
        self.assertEqual(plugin.show, self.method_called(result))

    def test_should_call_hide_when_timer_finished(self, mock_indicator=None):
        plugin = make_indicator()
        plugin.activate()

        result = Events.Session.send(State.finished)

        self.assertEqual(1, len(result))
        self.assertEqual(plugin.hide, self.method_called(result))

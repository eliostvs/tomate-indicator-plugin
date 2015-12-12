from __future__ import unicode_literals

import unittest

from gi.repository import AppIndicator3
from mock import Mock, patch

from tomate.graph import graph
from tomate.view import TrayIcon


@patch('indicator_plugin.AppIndicator3.Indicator')
class TestIndicatorPlugin(unittest.TestCase):

    def make_indicator(self):
        from indicator_plugin import IndicatorPlugin

        graph.providers.clear()

        graph.register_instance('tomate.config', Mock(**{'get_icon_paths.return_value': ['']}))
        graph.register_instance('tomate.view', Mock())

        return IndicatorPlugin()

    def test_should_update_icon_when_timer_changed(self, mock_indicator):
        plugin = self.make_indicator()

        plugin.update_icon(time_ratio=0.5)
        plugin.indicator.set_icon.assert_called_with('tomate-50')

        plugin.update_icon(time_ratio=0.9)
        plugin.indicator.set_icon.assert_called_with('tomate-90')

    def test_should_show_indicator(self, mock_indicator):
        plugin = self.make_indicator()

        plugin.show()

        plugin.indicator.set_status.assert_called_once_with(AppIndicator3.IndicatorStatus.ACTIVE)

    def test_should_hide_indicator(self, mock_indicator):
        plugin = self.make_indicator()

        plugin.hide()

        plugin.indicator.set_status.assert_called_once_with(AppIndicator3.IndicatorStatus.PASSIVE)

    def test_should_register_tray_icon_provider(self, mock_indicator):
        plugin = self.make_indicator()

        plugin.activate()

        self.assertIn(TrayIcon, graph.providers.keys())
        self.assertEqual(graph.get(TrayIcon), plugin)

    def test_should_unregister_tray_icon_provider(self, mock_indicator):
        plugin = self.make_indicator()

        graph.register_instance(TrayIcon, plugin)

        plugin.deactivate()

        self.assertNotIn(TrayIcon, graph.providers.keys())

    def test_should_show_view(self, mock_indicator):
        plugin = self.make_indicator()

        plugin.on_show_menu_activate()

        plugin.view.show.assert_called_once_with()



from __future__ import unicode_literals

import unittest

from mock import Mock


class IndicatorPluginTestCase(unittest.TestCase):

    def setUp(self):
        from indicator_plugin import IndicatorPlugin

        self.plugin = IndicatorPlugin()
        self.plugin.view = Mock()
        self.indicator = self.plugin.view.indicator

    def test_should_set_icon_idle_and_status_activate_on_activate(self):
        from gi.repository import AppIndicator3

        self.plugin.activate()

        self.indicator.set_icon.assert_called_with('tomate-idle')
        self.indicator.set_status.assert_called_with(AppIndicator3.IndicatorStatus.ACTIVE)

    def test_should_set_icon_indicator_on_deactivate(self):
        self.plugin.deactivate()

        self.indicator.set_icon.assert_called_with('tomate-indicator')

    def test_should_set_status_attention(self):
        from gi.repository import AppIndicator3

        self.plugin.status_attention()

        self.indicator.set_attention_icon.assert_called_with('tomate-attention')
        self.indicator.set_status.assert_called_with(AppIndicator3.IndicatorStatus.ATTENTION)

    def test_should_change_icon_as_ratio_changes(self):
        self.plugin.update_icon()
        self.indicator.set_icon.assert_called_with('tomate-00')

        self.plugin.update_icon(time_ratio=0.5)
        self.indicator.set_icon.assert_called_with('tomate-50')

        self.plugin.update_icon(time_ratio=0.9)
        self.indicator.set_icon.assert_called_with('tomate-90')

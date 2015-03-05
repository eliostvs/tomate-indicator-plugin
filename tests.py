from __future__ import unicode_literals

import unittest

from mock import Mock
from tomate.graph import graph


class TestIndicatorPlugin(unittest.TestCase):

    def setUp(self):
        graph.register_factory('tomate.indicator', Mock)

        from indicator_plugin import IndicatorPlugin

        self.plugin = IndicatorPlugin()

    def test_should_set_idle_icon_when_activate(self):
        self.plugin.activate()

        self.plugin.indicator.set_icon.assert_called_with('tomate-idle')

    def test_should_set_default_icon_when_deactivate(self):
        self.plugin.deactivate()

        self.plugin.indicator.set_icon.assert_called_with('tomate-indicator')

    def test_should_set_attention_icon(self):
        self.plugin.attention_icon()

        self.plugin.indicator.set_icon.assert_called_with('tomate-attention')

    def test_should_update_icon_according_the_time_left(self):
        self.plugin.update_icon()
        self.plugin.indicator.set_icon.assert_called_with('tomate-00')

        self.plugin.update_icon(time_ratio=0.5)
        self.plugin.indicator.set_icon.assert_called_with('tomate-50')

        self.plugin.update_icon(time_ratio=0.9)
        self.plugin.indicator.set_icon.assert_called_with('tomate-90')

from __future__ import unicode_literals

import logging

from tomate.plugin import TomatePlugin
from tomate.utils import suppress_errors

logger = logging.getLogger(__name__)


class IndicatorPlugin(TomatePlugin):

    signals = (
        ('timer_updated', 'update_icon'),
        ('session_started', 'default_icon'),
        ('session_interrupted', 'default_icon'),
        ('sessions_reseted', 'default_icon'),
    )

    def on_activate(self):
        self.idle_icon()

    def on_deactivate(self):
        self.default_icon()

    @suppress_errors
    def default_icon(self, *args, **kwargs):
        self.set_icon('tomate-indicator')

        logger.debug('default icon setted')

    @suppress_errors
    def idle_icon(self, *args, **kwargs):
        self.set_icon('tomate-idle')

        logger.debug('idle icon setted')

    @suppress_errors
    def update_icon(self, *args, **kwargs):
        percent = int(kwargs.get('time_ratio', 0) * 100)

        # The icons show 5% steps, so we have to round
        rounded_percent = percent - percent % 5

        # There is no icon for 100%
        if rounded_percent < 99:
            icon_name = 'tomate-{0:02}'.format(rounded_percent)
            self.set_icon(icon_name)

            logger.debug('setted icon %s', icon_name)

    @suppress_errors
    def attention_icon(self, *args, **kwargs):
        self.set_icon('tomate-attention')

        logger.debug('attention icon setted')

    def set_icon(self, icon_name):
        self.application.view.indicator.set_icon(icon_name)

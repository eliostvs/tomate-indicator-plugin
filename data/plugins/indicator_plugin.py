from __future__ import unicode_literals

import locale
import logging

from gi.repository import AppIndicator3
from tomate.plugin import TomatePlugin
from tomate.utils import suppress_errors

locale.textdomain('tomate')

logger = logging.getLogger(__name__)


class IndicatorPlugin(TomatePlugin):

    signals = (
        ('timer_updated', 'update_icon'),
        ('session_started', 'status_idle'),
        ('session_interrupted', 'status_idle'),
        ('sessions_reseted', 'status_idle'),
        ('session_ended', 'status_attention'),
    )

    def on_activate(self):
        self.status_idle()

    def on_deactivate(self):
        self.reset_icon()

    @suppress_errors
    def reset_icon(self):
        self.view.indicator.set_icon('tomate-indicator')

    @suppress_errors
    def status_idle(self, sender=None, **kwargs):
        self.view.indicator.set_icon('tomate-idle')
        self.view.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

    @suppress_errors
    def update_icon(self, sender=None, **kwargs):
        percent = int(kwargs.get('time_ratio', 0) * 100)

        # The icons show 5% steps, so we have to round
        rounded_percent = percent - percent % 5

        # There is no icon for 100%
        if rounded_percent < 99:
            icon_name = 'tomate-{0:02}'.format(rounded_percent)
            self.view.indicator.set_icon(icon_name)

            logger.debug('Update indicator icon %s', icon_name)

    @suppress_errors
    def status_attention(self, sender=None, **kwargs):
        self.view.indicator.set_attention_icon('tomate-attention')
        self.view.indicator.set_status(AppIndicator3.IndicatorStatus.ATTENTION)

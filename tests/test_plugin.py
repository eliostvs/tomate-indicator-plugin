import pytest
from gi.repository import AppIndicator3, Gtk
from wiring import Graph

from tomate.pomodoro import Bus, Config, Events, Session, TimerPayload
from tomate.ui import Systray, SystrayMenu


@pytest.fixture
def bus() -> Bus:
    return Bus()


@pytest.fixture
def graph() -> Graph:
    instance = Graph()
    instance.register_instance(Graph, instance)
    return instance


@pytest.fixture
def menu(mocker):
    return mocker.Mock(spec=SystrayMenu, widget=Gtk.Menu())


@pytest.fixture
def session(mocker):
    return mocker.Mock(spec=Session)


@pytest.fixture
def plugin(bus, menu, graph, session):
    graph.providers.clear()
    graph.register_instance("tomate.bus", bus)
    graph.register_instance("tomate.config", Config(bus))
    graph.register_instance("tomate.session", session)
    graph.register_instance("tomate.ui.systray.menu", menu)

    import indicator_plugin

    instance = indicator_plugin.IndicatorPlugin()
    instance.configure(bus, graph)
    return instance


@pytest.mark.parametrize(
    "time_left,duration,icon_name",
    [
        (100, 100, "tomate-00"),
        (95, 100, "tomate-05"),
        (90, 100, "tomate-10"),
        (85, 100, "tomate-15"),
        (80, 100, "tomate-20"),
        (75, 100, "tomate-25"),
        (70, 100, "tomate-30"),
        (65, 100, "tomate-35"),
        (60, 100, "tomate-40"),
        (55, 100, "tomate-45"),
        (50, 100, "tomate-50"),
        (45, 100, "tomate-55"),
        (40, 100, "tomate-60"),
        (35, 100, "tomate-65"),
        (30, 100, "tomate-70"),
        (25, 100, "tomate-75"),
        (20, 100, "tomate-80"),
        (10, 100, "tomate-90"),
        (5, 100, "tomate-95"),
    ],
)
def test_change_icon_when_timer_change(time_left, duration, icon_name, bus, plugin):
    plugin.activate()

    bus.send(Events.TIMER_UPDATE, payload=TimerPayload(time_left=time_left, duration=duration))

    assert plugin.indicator.get_icon() == icon_name


def test_do_not_set_the_same_icon(bus, plugin, mocker):
    plugin.activate()

    with mocker.patch.object(plugin.indicator, "set_icon", wraps=plugin.indicator.set_icon):
        bus.send(Events.TIMER_UPDATE, payload=TimerPayload(time_left=90, duration=1000))
        bus.send(Events.TIMER_UPDATE, payload=TimerPayload(time_left=100, duration=1000))

        plugin.indicator.set_icon.assert_called_once()


def test_show_when_session_start(bus, plugin):
    plugin.activate()
    plugin.indicator.set_status(AppIndicator3.IndicatorStatus.PASSIVE)

    bus.send(Events.SESSION_START)

    assert plugin.indicator.get_status() == AppIndicator3.IndicatorStatus.ACTIVE


@pytest.mark.parametrize("event", [Events.SESSION_END, Events.SESSION_INTERRUPT])
def test_hide_when_session_end(event, bus, plugin):
    plugin.activate()
    plugin.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

    bus.send(event, payload="")

    assert plugin.indicator.get_status() == AppIndicator3.IndicatorStatus.PASSIVE
    assert plugin.indicator.get_icon() == "tomate-idle"


class TestActivePlugin:
    def test_activate(self, bus, menu, graph, plugin):
        plugin.activate()

        assert Systray in graph.providers.keys()
        assert graph.get(Systray) == plugin
        menu.connect.assert_called_once_with(bus)
        assert plugin.indicator.get_category() is AppIndicator3.IndicatorCategory.APPLICATION_STATUS

    def test_show_when_session_is_running(self, session, plugin):
        session.is_running.return_value = True
        plugin.indicator.set_status(AppIndicator3.IndicatorStatus.PASSIVE)

        plugin.activate()

        assert plugin.indicator.get_status() == AppIndicator3.IndicatorStatus.ACTIVE

    def test_hide_when_session_is_not_running(self, session, plugin):
        session.is_running.return_value = False
        plugin.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

        plugin.activate()

        assert plugin.indicator.get_status() == AppIndicator3.IndicatorStatus.PASSIVE


class TestDeactivatePlugin:
    def test_deactivate(self, bus, menu, graph, plugin):
        graph.register_instance(Systray, plugin)

        plugin.deactivate()

        assert Systray not in graph.providers.keys()
        menu.disconnect.assert_called_once_with(bus)

    def test_hide_indicator(self, graph, plugin):
        graph.register_instance(Systray, plugin)
        plugin.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

        plugin.deactivate()

        assert plugin.indicator.get_status() == AppIndicator3.IndicatorStatus.PASSIVE

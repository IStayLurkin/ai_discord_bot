from godbot.plugins.loader import plugin_manager


def test_plugin_discovery():
    discovered = plugin_manager.discover_plugins()

    assert isinstance(discovered, list)


def test_plugin_list_loaded():
    loaded = plugin_manager.list_plugins()

    assert isinstance(loaded, list)


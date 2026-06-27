from core.config import load_config

def test_load_config_returns_dict():
    cfg = load_config()
    assert isinstance(cfg, dict)

def test_config_has_required_keys():
    cfg = load_config()
    assert "portals" in cfg
    assert "keywords" in cfg
    assert "email" in cfg
    assert "schedule" in cfg
    assert "search_queries" in cfg

def test_config_portals_have_required_fields():
    cfg = load_config()
    for portal in cfg["portals"]:
        assert "name" in portal
        assert "enabled" in portal
        assert "module" in portal
        assert "url" in portal
        assert "is_public_sector" in portal

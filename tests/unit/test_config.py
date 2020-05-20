from pilot import config


def test_config_section_save_load_values(mock_config):

    class TestSection(config.ConfigSection):
        SECTION = 'mysection'

    cfg = TestSection('/tmp/test_pilot.cfg')
    cfg.save_option('foo', 'bar')
    assert cfg.load_option('foo') == 'bar'

    # Test None Values
    cfg.save_option('moo', None)
    assert cfg.load_option('moo') is None

    assert 'mysection' in mock_config.load()

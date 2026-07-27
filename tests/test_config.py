import configparser

from src.ivie.config import get_recruitment_config
from src.ivie.llm.structured_data_models import FeelingLevel


def _config_from_string(text):
    config = configparser.ConfigParser()
    config.read_string(text)
    return config


def test_get_recruitment_config_reads_enabled_and_threshold():
    config = _config_from_string("""
[Recruitment]
enabled = true
feeling_threshold = friendly
""")
    enabled, threshold = get_recruitment_config(config)
    assert enabled is True
    assert threshold == FeelingLevel.FRIENDLY


def test_get_recruitment_config_defaults_when_keys_missing():
    config = _config_from_string("""
[Recruitment]
""")
    enabled, threshold = get_recruitment_config(config)
    assert enabled is True
    assert threshold == FeelingLevel.FRIENDLY


def test_get_recruitment_config_reads_disabled():
    config = _config_from_string("""
[Recruitment]
enabled = false
feeling_threshold = devoted
""")
    enabled, threshold = get_recruitment_config(config)
    assert enabled is False
    assert threshold == FeelingLevel.DEVOTED

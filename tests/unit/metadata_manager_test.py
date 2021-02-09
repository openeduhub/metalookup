from logging import Logger

import pytest

from features.metadata_manager import MetadataManager
from lib.settings import NUMBER_OF_EXTRACTORS


@pytest.fixture
def metadata_manager():
    manager = MetadataManager.get_instance()
    return manager


"""
--------------------------------------------------------------------------------
"""


def test_init(metadata_manager: MetadataManager):
    assert isinstance(metadata_manager._logger, Logger)
    assert NUMBER_OF_EXTRACTORS == 22
    assert len(metadata_manager.metadata_extractors) == NUMBER_OF_EXTRACTORS

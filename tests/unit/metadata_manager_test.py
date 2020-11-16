from logging import Logger

import pytest

from features.metadata_manager import MetadataManager


@pytest.fixture
def metadata_manager():
    manager = MetadataManager.get_instance()
    return manager


"""
--------------------------------------------------------------------------------
"""


def test_init(metadata_manager: MetadataManager):
    assert isinstance(metadata_manager._logger, Logger)
    assert len(metadata_manager.metadata_extractors) == 0


"""
--------------------------------------------------------------------------------
"""


def test_setup(metadata_manager: MetadataManager, mocker):
    assert isinstance(metadata_manager._logger, Logger)
    assert len(metadata_manager.metadata_extractors) == 0

    metadata_manager._setup_extractors = mocker.MagicMock()
    metadata_manager.setup()

    assert len(metadata_manager.metadata_extractors) == 18

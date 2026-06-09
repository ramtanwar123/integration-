import pytest
import partners.alea_sgs.config as config
from core.base_game_client import BaseGameClient
from core.auth.no_auth import NoAuth


def make_client():
    auth = NoAuth(config)
    return BaseGameClient(config, auth)


@pytest.fixture(scope="function")
def game_client():
    """Fresh client per test — avoids session bleed."""
    return make_client()
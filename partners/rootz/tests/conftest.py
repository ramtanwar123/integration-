import pytest
import partners.rootz.config as config
from core.base_game_client import BaseGameClient
from core.auth.basic_auth import BasicAuth


def make_client():
    auth = BasicAuth(
        username=config.BASIC_USERNAME,
        password=config.BASIC_PASSWORD,
        partner_id=config.PARTNER_ID,
        forwarded_for=config.FORWARDED_FOR,
    )
    return BaseGameClient(config, auth)


@pytest.fixture(scope="function")
def game_client():
    return make_client()
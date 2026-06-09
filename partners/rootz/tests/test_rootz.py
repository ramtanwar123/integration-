import pytest
from core.base_game_tests import (
    BaseInitTests,
    BasePlayTests,
    BaseFinishTests,
    BaseFullFlowTests,
)


class TestRootzInit(BaseInitTests):
    """Rootz init tests — inherits all base tests."""

    def test_init_with_real_money(self, game_client):
        """Rootz REAL money init."""
        resp = game_client.init(money_mode="REAL")
        assert resp.status_code == 200
        assert "sessionId" in resp.json()

    def test_init_with_fun_money(self, game_client):
        """Rootz FUN money init."""
        resp = game_client.init(money_mode="FUN")
        assert resp.status_code == 200
        assert "sessionId" in resp.json()

    def test_init_jurisdiction_kgc(self, game_client):
        """Rootz KGC jurisdiction."""
        resp = game_client.init()
        assert resp.status_code == 200


class TestRootzPlay(BasePlayTests):
    """Rootz play tests — inherits all base tests."""

    def test_play_nzd_currency(self, game_client):
        """Rootz uses NZD currency."""
        game_client.init()
        resp = game_client.play()
        assert resp.status_code == 200
        data = resp.json()
        if "accounts" in data:
            assert data["accounts"].get("currency") == "NZD"

    def test_play_returns_round_id(self, game_client):
        """Play must return roundId."""
        game_client.init()
        resp = game_client.play()
        assert resp.status_code == 200
        assert "roundId" in resp.json()


class TestRootzFinish(BaseFinishTests):
    """Rootz finish tests — inherits all base tests."""
    pass


class TestRootzFullFlow(BaseFullFlowTests):
    """Rootz full flow tests — inherits all base tests."""

    def test_full_round_nzd(self, game_client):
        """Complete round with NZD currency."""
        init_r, play_r, finish_r = game_client.full_round()
        assert init_r.status_code == 200
        assert play_r.status_code == 200
        assert finish_r.status_code == 200
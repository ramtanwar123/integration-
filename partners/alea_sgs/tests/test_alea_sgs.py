import pytest
from core.base_game_tests import (
    BaseInitTests,
    BasePlayTests,
    BaseFinishTests,
    BaseFullFlowTests,
)


class TestAleaSgsInit(BaseInitTests):
    """Alea SGS init tests — inherits all base tests."""

    def test_init_returns_free_rounds_if_active(self, game_client):
        """
        Alea-specific: if player has active free rounds,
        init response must contain freeRounds array.
        """
        resp = game_client.init()
        assert resp.status_code == 200
        data = resp.json()
        # freeRounds is optional — only check if present
        if "freeRounds" in data:
            assert isinstance(data["freeRounds"], list)

    def test_init_returns_bet_config(self, game_client):
        """Alea-specific: init must return betConfig."""
        resp = game_client.init()
        assert resp.status_code == 200
        data = resp.json()
        assert "betConfig" in data, \
            f"betConfig missing from Alea init response"
        bet_config = data["betConfig"]
        assert "minBet" in bet_config
        assert "maxBet" in bet_config
        assert "defaultBet" in bet_config
        assert "betSizes" in bet_config

    def test_init_returns_currency_formatting(self, game_client):
        """Alea-specific: init must return currencyFormatting."""
        resp = game_client.init()
        assert resp.status_code == 200
        assert "currencyFormatting" in resp.json()

    def test_init_accounts_currency_matches_config(self, game_client):
        """Currency in response must match configured currency."""
        resp = game_client.init()
        assert resp.status_code == 200
        data = resp.json()
        if "accounts" in data:
            assert data["accounts"]["currency"] == game_client.config.CURRENCY


class TestAleaSgsPlay(BasePlayTests):
    """Alea SGS play tests — inherits all base tests."""

    def test_play_returns_round_state(self, game_client):
        """Alea-specific: play must return roundState."""
        game_client.init()
        resp = game_client.play()
        assert resp.status_code == 200
        data = resp.json()
        assert "roundState" in data, \
            f"roundState missing: {list(data.keys())}"

    def test_play_returns_game_data(self, game_client):
        """Alea-specific: play must return game object."""
        game_client.init()
        resp = game_client.play()
        assert resp.status_code == 200
        data = resp.json()
        assert "game" in data, \
            f"game object missing: {list(data.keys())}"

    def test_play_round_state_waiting_finish(self, game_client):
        """After play, roundState must be WAITING_FINISH."""
        game_client.init()
        resp = game_client.play()
        assert resp.status_code == 200
        assert resp.json().get("roundState") == "WAITING_FINISH", \
            f"Expected WAITING_FINISH, got {resp.json().get('roundState')}"

    def test_play_win_amount_non_negative(self, game_client):
        """Win amount must never be negative."""
        game_client.init()
        resp = game_client.play()
        assert resp.status_code == 200
        win = resp.json().get("winAmount", 0)
        assert float(win) >= 0, f"Negative win amount: {win}"

    def test_play_accounts_updated(self, game_client):
        """accounts.balance must be updated after play."""
        game_client.init()
        resp = game_client.play()
        assert resp.status_code == 200
        data = resp.json()
        assert "accounts" in data
        assert "balance" in data["accounts"]
        assert data["accounts"]["balance"] >= 0

    def test_play_buy_feature(self, game_client):
        """Buy feature play."""
        game_client.init()
        resp = game_client.play(extra={"buyFeature": True})
        # Buy feature may or may not be supported
        assert resp.status_code in (200, 400, 422)


class TestAleaSgsFinish(BaseFinishTests):
    """Alea SGS finish tests — inherits all base tests."""

    def test_finish_round_state_end(self, game_client):
        """After finish, roundState must be END."""
        game_client.init()
        game_client.play()
        resp = game_client.finish()
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("roundState") == "END", \
            f"Expected END, got {data.get('roundState')}"

    def test_finish_returns_free_rounds_status(self, game_client):
        """Alea-specific: finish response may contain freeRounds."""
        game_client.init()
        game_client.play()
        resp = game_client.finish()
        assert resp.status_code == 200
        data = resp.json()
        if "freeRounds" in data:
            assert isinstance(data["freeRounds"], list)


class TestAleaSgsFullFlow(BaseFullFlowTests):
    """Alea SGS full flow tests — inherits all base tests."""

    def test_full_round_with_free_rounds(self, game_client):
        init_resp = game_client.init()
        assert init_resp.status_code == 200

        free_rounds = [
            fr for fr in init_resp.json().get("freeRounds", [])
            if fr.get("state") == "ACTIVE"
            and fr.get("remainingRounds", 0) > 0
        ]

        if not free_rounds:
            pytest.skip("No active free rounds available")

        fr = free_rounds[0]

        bet_amount = (
            fr.get("betAmount")
            or fr.get("roundOptions", [{}])[0].get("betAmount")
            or game_client.config.DEFAULT_BET
        )

        play_resp = game_client.play(bet_amount=bet_amount)
        assert play_resp.status_code == 200

        finish_resp = game_client.finish()
        assert finish_resp.status_code == 200
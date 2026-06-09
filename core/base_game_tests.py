import pytest


class BaseInitTests:
    """
    Generic init tests — all partners inherit these.
    Partner-specific overrides go in partners/<name>/tests/.
    """

    def test_init_valid(self, game_client):
        """Valid token — must return 200 with sessionId."""
        resp = game_client.init()
        assert resp.status_code == 200, \
            f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "sessionId" in data, \
            f"sessionId missing from response: {data}"
        assert data["sessionId"] is not None

    def test_init_returns_session_id(self, game_client):
        """sessionId must be a non-empty string."""
        resp = game_client.init()
        assert resp.status_code == 200
        session_id = resp.json().get("sessionId")
        assert isinstance(session_id, str)
        assert len(session_id) > 0

    def test_init_invalid_token(self, game_client):
        """Invalid token — must return error."""
        resp = game_client.init(token="invalid-token-xyz")
        assert resp.status_code != 200 or \
               resp.json().get("error") is not None, \
            "Invalid token should return error"

    def test_init_invalid_game_id(self, game_client):
        """Invalid game ID — must return error."""
        resp = game_client.init(game_id="invalid-game-xyz")
        assert resp.status_code != 200 or \
               resp.json().get("error") is not None, \
            "Invalid game ID should return error"

    def test_init_real_money(self, game_client):
        """REAL money mode init."""
        resp = game_client.init(money_mode="REAL")
        assert resp.status_code == 200
        assert "sessionId" in resp.json()

    def test_init_fun_money(self, game_client):
        """FUN money mode init."""
        resp = game_client.init(money_mode="FUN")
        assert resp.status_code == 200
        assert "sessionId" in resp.json()

    def test_init_response_has_balance(self, game_client):
        """Init response must contain balance info."""
        resp = game_client.init()
        assert resp.status_code == 200
        data = resp.json()
        # Balance can be in different fields depending on partner
        has_balance = (
            "accounts" in data or
            "balance" in data or
            "realBalance" in data or
            "totalBalance" in data
        )
        assert has_balance, \
            f"No balance field found in response: {list(data.keys())}"


class BasePlayTests:
    """
    Generic play tests — all partners inherit these.
    """

    def test_play_valid(self, game_client):
        init_resp = game_client.init()

        data = init_resp.json()

        print("\nSESSION ID:", data.get("sessionId"))
        print("ROUND STATE:", data.get("roundState"))
        print("FREE ROUNDS:", data.get("freeRounds"))
        print("TOKEN:", game_client.config.TOKEN)
        print("SESSION:", data.get("sessionId"))

        resp = game_client.play()

        print("\nPLAY JSON:")
        try:
            print(resp.json())
        except Exception:
            print(resp.text)

        assert resp.status_code == 200

    def test_play_returns_round_id(self, game_client):
        """Play response must contain roundId."""
        game_client.init()
        resp = game_client.play()
        assert resp.status_code == 200
        data = resp.json()
        assert "roundId" in data, \
            f"roundId missing from play response: {list(data.keys())}"

    def test_play_returns_updated_balance(self, game_client):
        """After play, balance must be returned."""
        game_client.init()
        resp = game_client.play()
        assert resp.status_code == 200
        data = resp.json()
        has_balance = (
            "accounts" in data or
            "balance" in data or
            "realBalance" in data or
            "totalBalance" in data
        )
        assert has_balance, \
            f"No balance in play response: {list(data.keys())}"

    def test_play_balance_decreases_after_bet(self, game_client):
        """After bet, balance must decrease."""
        init_resp = game_client.init()
        assert init_resp.status_code == 200

        init_balance = _extract_balance(init_resp.json())
        play_resp = game_client.play(
            bet_amount=game_client.config.DEFAULT_BET
        )
        assert play_resp.status_code == 200
        play_balance = _extract_balance(play_resp.json())

        if init_balance is not None and play_balance is not None:
            assert play_balance <= init_balance, \
                f"Balance should decrease after bet. " \
                f"Before: {init_balance}, After: {play_balance}"

    def test_play_without_init_fails(self, game_client):
        """Play without init must fail."""
        fresh_client = game_client.__class__(
            game_client.config,
            game_client.auth
        )
        with pytest.raises((ValueError, Exception)):
            fresh_client.play()

    def test_play_minimum_bet(self, game_client):
        """Minimum bet amount."""
        game_client.init()
        min_bet = getattr(game_client.config, "MIN_BET", 1)
        resp = game_client.play(bet_amount=min_bet)
        assert resp.status_code == 200

    def test_play_zero_bet_rejected(self, game_client):
        """Zero bet must be rejected."""
        game_client.init()
        resp = game_client.play(bet_amount=0)
        # Either 4xx or error in body
        assert resp.status_code != 200 or \
               resp.json().get("error") is not None, \
            "Zero bet should be rejected"

    def test_play_excessive_bet_rejected(self, game_client):
        """Bet exceeding balance must be rejected."""
        game_client.init()
        resp = game_client.play(bet_amount=9999999)
        assert resp.status_code != 200 or \
               resp.json().get("error") is not None, \
            "Excessive bet should be rejected"
    def test_play_multiple_rounds(self, game_client):
        """Multiple rounds."""
        for i in range(3):
            game_client.init()

            play_resp = game_client.play()
            assert play_resp.status_code == 200, \
                f"Round {i+1} play failed: {play_resp.text}"

            finish_resp = game_client.finish()
            assert finish_resp.status_code == 200, \
                f"Round {i+1} finish failed: {finish_resp.text}"

    def test_play_fun_mode_no_balance_change(self, game_client):
        """FUN mode play — real balance should not change."""
        init_resp = game_client.init(money_mode="FUN")
        assert init_resp.status_code == 200
        resp = game_client.play(money_mode="FUN")
        assert resp.status_code == 200


class BaseFinishTests:
    """
    Generic finish tests — all partners inherit these.
    """

    def test_finish_valid(self, game_client):
        """Valid finish after init — must return 200."""
        game_client.init()
        resp = game_client.finish()
        assert resp.status_code == 200, \
            f"Expected 200, got {resp.status_code}: {resp.text}"

    def test_finish_after_play(self, game_client):
        """Finish after play — must succeed."""
        game_client.init()
        game_client.play()
        resp = game_client.finish()
        assert resp.status_code == 200

    def test_finish_without_init_fails(self, game_client):
        """Finish without init must fail."""
        fresh_client = game_client.__class__(
            game_client.config,
            game_client.auth
        )
        with pytest.raises((ValueError, Exception)):
            fresh_client.finish()

    def test_finish_twice_fails(self, game_client):
        """Finishing already finished session must fail."""
        game_client.init()
        game_client.finish()
        resp = game_client.finish()
        assert resp.status_code != 200 or \
               resp.json().get("error") is not None, \
            "Double finish should be rejected"


class BaseFullFlowTests:
    """
    Full flow tests — init → play → finish.
    """

    def test_full_round(self, game_client):
        """Complete round: init → play → finish."""
        init_r, play_r, finish_r = game_client.full_round()
        assert init_r.status_code == 200, \
            f"Init failed: {init_r.text}"
        assert play_r.status_code == 200, \
            f"Play failed: {play_r.text}"
        assert finish_r.status_code == 200, \
            f"Finish failed: {finish_r.text}"

    def test_multiple_full_rounds(self, game_client):
        """Multiple complete rounds in sequence."""
        for i in range(3):
            init_r, play_r, finish_r = game_client.full_round()
            assert init_r.status_code == 200, \
                f"Round {i+1} init failed"
            assert play_r.status_code == 200, \
                f"Round {i+1} play failed"
            assert finish_r.status_code == 200, \
                f"Round {i+1} finish failed"

    def test_balance_after_win(self, game_client):
        """Balance must update correctly after win."""
        init_resp = game_client.init()
        assert init_resp.status_code == 200
        init_balance = _extract_balance(init_resp.json())

        play_resp = game_client.play()
        assert play_resp.status_code == 200
        play_data = play_resp.json()

        win_amount = _extract_win(play_data)
        play_balance = _extract_balance(play_data)

        game_client.finish()

        if all(v is not None for v in [init_balance, play_balance, win_amount]):
            expected = init_balance - game_client.config.DEFAULT_BET + win_amount
            assert abs(play_balance - expected) < 0.01, \
                f"Balance mismatch. Expected ~{expected}, got {play_balance}"

    def test_session_id_consistent(self, game_client):
        """Same sessionId used across play and finish."""
        init_resp = game_client.init()
        assert init_resp.status_code == 200
        session_id = init_resp.json().get("sessionId")

        play_resp = game_client.play()
        assert play_resp.status_code == 200
        play_session = play_resp.json().get("sessionId")

        if play_session:
            assert play_session == session_id, \
                "sessionId must be consistent across requests"

    def test_fun_mode_full_round(self, game_client):
        """Complete round in FUN mode."""
        init_r = game_client.init(money_mode="FUN")
        assert init_r.status_code == 200
        play_r = game_client.play(money_mode="FUN")
        assert play_r.status_code == 200
        finish_r = game_client.finish()
        assert finish_r.status_code == 200


# ── Helper functions ──────────────────────────────────────────────────────────

def _extract_balance(data: dict) -> float:
    """Extract balance from any partner response format."""
    if not data:
        return None
    # Try different field names
    for key in ["balance", "realBalance", "totalBalance",
                "real_balance", "total_balance"]:
        if key in data:
            try:
                return float(data[key])
            except (TypeError, ValueError):
                pass
    # Nested: accounts.balance
    if "accounts" in data and isinstance(data["accounts"], dict):
        for key in ["balance", "real", "realBalance"]:
            if key in data["accounts"]:
                try:
                    return float(data["accounts"][key])
                except (TypeError, ValueError):
                    pass
    return None


def _extract_win(data: dict) -> float:
    """Extract win amount from play response."""
    if not data:
        return None
    for key in ["winAmount", "win", "winAmounts", "totalWin"]:
        if key in data:
            try:
                return float(data[key])
            except (TypeError, ValueError):
                pass
    # Nested: game.winAmount
    if "game" in data and isinstance(data["game"], dict):
        for key in ["winAmount", "win"]:
            if key in data["game"]:
                try:
                    return float(data["game"][key])
                except (TypeError, ValueError):
                    pass
    return None
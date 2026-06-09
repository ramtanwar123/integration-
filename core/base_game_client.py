import json
import uuid
import requests
from typing import Optional


class BaseGameClient:
    """
    Generic RGS Game Client.

    Handles init → play → finish flow for any partner.
    Partners only need to provide:
      - config (base_url, adapter, token, game_id, etc.)
      - auth handler (DigestAuth, BasicAuth, HmacAuth, NoAuth)

    This class is completely partner-agnostic.
    """

    def __init__(self, config, auth):
        """
        config: partner config module
        auth:   auth handler instance (DigestAuth, BasicAuth, etc.)
        """
        self.config = config
        self.auth = auth
        self._session_id = None

    # ── Helpers ───────────────────────────────────────────────────────────────

    def unique_id(self, prefix=""):
        uid = str(uuid.uuid4())
        return f"{prefix}-{uid}" if prefix else uid

    def _post(self, path: str, body: dict,
              auth_kwargs: dict = None) -> requests.Response:
        """Generic POST — builds URL, gets headers, sends request."""
        url = f"{self.config.BASE_URL}{path}"
        body_str = json.dumps(body, separators=(",", ":"))
        headers = self.auth.get_headers(
            **(auth_kwargs or {})
        )
        print("\n========== REQUEST ==========")
        print("URL:", url)
        print("HEADERS:", headers)
        print("BODY:", body)
        print("=============================\n")

        resp = requests.post(url, headers=headers, data=body_str)

        print("STATUS:", resp.status_code)
        print("RESPONSE:", resp.text)

        return resp
    # ── Core Game Flow ────────────────────────────────────────────────────────

    def init(self, token: str = None, game_id: str = None,
             money_mode: str = None, extra: dict = None) -> requests.Response:
        """
        POST /sgs/v1/game/init
        Starts a game session. Returns sessionId used in play/finish.

        Required fields vary by partner (adapter, token, gameId, etc.)
        Extra fields can be passed via `extra` dict.
        """
        body = {
            "adapter": self.config.ADAPTER,
            "gameId": game_id or self.config.GAME_ID,
            "gameVersion": getattr(self.config, "GAME_VERSION", "1"),
            "moneyMode": money_mode or self.config.MONEY_MODE,
            "partnerId": self.config.PARTNER_ID,
            "token": token or self.config.TOKEN,
            "operator_id": getattr(self.config, "OPERATOR_ID", None),
            "user": getattr(self.config, "USER_ID", None),
        }

        # Optional fields — only add if present in config
        for field, config_attr in [
            ("jurisdiction", "JURISDICTION"),
            ("locale", "LOCALE"),
            ("countryCode", "COUNTRY_CODE"),
            ("currency", "CURRENCY"),
            ("platform", "PLATFORM"),
        ]:
            val = getattr(self.config, config_attr, None)
            if val:
                body[field] = val

        # Partner-specific extra fields
        if extra:
            body.update(extra)

        resp = self._post(self.config.INIT_PATH, body)
        print("\n===== INIT RESPONSE =====")
        print("STATUS:", resp.status_code)

        # Auto-store session_id if init succeeds
        resp = self._post(self.config.INIT_PATH, body)

        print("\n===== INIT RESPONSE =====")
        print("STATUS:", resp.status_code)

        if resp.status_code == 200:
            try:
                data = resp.json()

                print("sessionId =", data.get("sessionId"))
                print("roundState =", data.get("roundState"))
                print("token =", token or self.config.TOKEN)
                print("GAME STATE:", data.get("gameState"))
                print("CURRENT ROUND:", data.get("roundId"))

                self._session_id = data.get("sessionId")

            except Exception as e:
                print("JSON parse error:", e)

        print("=========================\n")

        return resp

    def play(self, session_id: str = None, bet_amount: float = None,
             game_id: str = None, money_mode: str = None,
             extra: dict = None) -> requests.Response:
        """
        POST /sgs/v1/game/play
        Places a bet in an active session.
        Uses session_id from last init() if not provided.
        """
        session_id = session_id or self._session_id
        if not session_id:
            raise ValueError(
                "session_id required — call init() first or pass session_id"
            )

        body = {
            "sessionId": session_id,
            "betAmount": bet_amount if bet_amount is not None
                         else self.config.DEFAULT_BET,
            "gameId": game_id or self.config.GAME_ID,
            "moneyMode": money_mode or self.config.MONEY_MODE,
            "buyFeature": False,
            "featureMode": 0,
            "timestamp": self._timestamp(),
        }

        if extra:
            body.update(extra)
        print("\n===== PLAY REQUEST =====")
        print("SESSION ID:", session_id)
        print("TOKEN:", self.config.TOKEN)
        print("BODY:", json.dumps(body, indent=2))
        print("========================")
        resp = self._post(self.config.PLAY_PATH, body)

        print("\n===== PLAY RESPONSE =====")
        print("STATUS:", resp.status_code)

        try:
            print(json.dumps(resp.json(), indent=2))
        except Exception:
            print(resp.text)

        print("=========================\n")

        return resp

    def finish(self, session_id: str = None,
               game_id: str = None,
               extra: dict = None) -> requests.Response:
        """
        POST /sgs/v1/game/finish
        Closes an active game session.
        Uses session_id from last init() if not provided.
        """
        session_id = session_id or self._session_id
        if not session_id:
            raise ValueError(
                "session_id required — call init() first or pass session_id"
            )

        body = {
            "sessionId": session_id,
            "gameId": game_id or self.config.GAME_ID,
        }

        if extra:
            body.update(extra)

        resp = self._post(self.config.FINISH_PATH, body)

        print("\n===== FINISH RESPONSE =====")
        print("STATUS:", resp.status_code)

        try:
            print(json.dumps(resp.json(), indent=2))
        except Exception:
            print(resp.text)

        print("=========================\n")

        return resp

    def _timestamp(self) -> str:
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()

    # ── Convenience: full flow ────────────────────────────────────────────────

    def init_and_play(self, bet_amount: float = None,
                      money_mode: str = None) -> tuple:
        """
        Convenience: init + play in one call.
        Returns (init_resp, play_resp)
        """
        init_resp = self.init(money_mode=money_mode)
        if init_resp.status_code != 200:
            return init_resp, None
        play_resp = self.play(bet_amount=bet_amount, money_mode=money_mode)
        return init_resp, play_resp

    def full_round(self, bet_amount: float = None,
                   money_mode: str = None) -> tuple:
        """
        Convenience: init + play + finish in one call.
        Returns (init_resp, play_resp, finish_resp)
        """
        init_resp = self.init(money_mode=money_mode)
        if init_resp.status_code != 200:
            return init_resp, None, None
        play_resp = self.play(bet_amount=bet_amount, money_mode=money_mode)
        finish_resp = self.finish()
        return init_resp, play_resp, finish_resp
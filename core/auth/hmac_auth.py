import hmac
import hashlib
import base64


class HmacAuth:
    """
    HMAC-SHA256 authentication — used by Groove.
    Signature = base64(HMAC-SHA256(path_and_query, base64_decode(access_key)))
    Header: Authorization: HMAC-SHA256 Signature=<base64>
    """

    def __init__(self, access_key_value: str,
                 forwarded_for: str = None):
        self.access_key_value = access_key_value
        self.forwarded_for = forwarded_for

    def generate_signature(self, path_and_query: str) -> str:
        secret = base64.b64decode(self.access_key_value)
        hash_bytes = hmac.new(
            secret,
            path_and_query.encode("utf-8"),
            hashlib.sha256
        ).digest()
        return base64.b64encode(hash_bytes).decode("utf-8")

    def get_headers(self, path_and_query: str = "", **kwargs) -> dict:
        signature = self.generate_signature(path_and_query)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"HMAC-SHA256 Signature={signature}",
        }
        if self.forwarded_for:
            headers["x-forwarded-for"] = self.forwarded_for
        return headers
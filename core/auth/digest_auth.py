import hashlib


class DigestAuth:
    """
    SHA-512 Digest authentication — used by Alea.
    Signature = SHA-512(session_id + extra_parts + secret_key)
    Header: Digest: SHA-512=<hex>
    """

    def __init__(self, secret_key: str, session_id: str,
                 forwarded_for: str = None):
        self.secret_key = secret_key
        self.session_id = session_id
        self.forwarded_for = forwarded_for

    def generate_signature(self, *parts) -> str:
        combined = "".join(parts)
        return "SHA-512=" + hashlib.sha512(
            combined.encode("utf-8")
        ).hexdigest()

    def get_headers(self, extra_parts=None, **kwargs) -> dict:
        parts = [self.session_id] + (extra_parts or []) + [self.secret_key]
        digest = self.generate_signature(*parts)
        headers = {
            "Content-Type": "application/json",
            "Digest": digest,
        }
        if self.forwarded_for:
            headers["x-forwarded-for"] = self.forwarded_for
        return headers
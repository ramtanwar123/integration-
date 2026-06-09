import base64


class BasicAuth:
    """
    HTTP Basic Authentication — used by Rootz/Jupiter.
    Header: Authorization: Basic <base64(username:password)>
    """

    def __init__(self, username: str, password: str,
                 partner_id: str = None,
                 forwarded_for: str = None):
        self.username = username
        self.password = password
        self.partner_id = partner_id
        self.forwarded_for = forwarded_for

    def _encode(self) -> str:
        credentials = f"{self.username}:{self.password}"
        return base64.b64encode(credentials.encode("utf-8")).decode("utf-8")

    def get_headers(self, **kwargs) -> dict:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {self._encode()}",
        }
        if self.partner_id:
            headers["x-partner-id"] = self.partner_id
        if self.forwarded_for:
            headers["x-forwarded-for"] = self.forwarded_for
        return headers
class NoAuth:
    def __init__(self, config=None):
        self.config = config

    def get_headers(self, **kwargs):
        return {
            "Content-Type": "application/json",
            "x-forwarded-for": self.config.FORWARDED_FOR,
        }
class BillingClient:
    """The transport owns authentication, retries, and HTTP errors."""

    def __init__(self, transport):
        self.transport = transport

    def iter_invoices(self, account):
        cursor = None
        while True:
            page = self.transport.get("/invoices", account=account, cursor=cursor)
            yield from page["items"]
            cursor = page.get("next")
            if cursor is None:
                return

def account_total(client, account):
    return sum(invoice["cents"] for invoice in client.iter_invoices(account))


def invoice_ids(client, account):
    raise NotImplementedError

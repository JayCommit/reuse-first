from presentation import format_money


def render_receipt(row):
    return f"Receipt {row['id']}: {format_money(row['cents'])}"


def render_invoice(row):
    raise NotImplementedError

def format_money(cents):
    """Current invoice UI contract: integer cents, GBP, minus before symbol."""
    sign = "-" if cents < 0 else ""
    pounds, pennies = divmod(abs(cents), 100)
    return f"{sign}£{pounds:,}.{pennies:02d}"


def render_total(cents):
    return f"Total: {format_money(cents)}"

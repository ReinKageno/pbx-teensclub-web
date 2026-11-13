
def rupiah(value):
    try:
        return "Rp " + f"{int(value):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "Rp 0"
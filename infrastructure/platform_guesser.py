def get_standard_from_address(address: str) -> str:
    """Определяет стандарт BIP по префиксу адреса."""
    if address.startswith('1'):
        return 'BIP44'
    elif address.startswith('3'):
        return 'BIP49'
    elif address.startswith('bc1q'):
        return 'BIP84'
    elif address.startswith('bc1p'):
        return 'BIP86'
    else:
        raise ValueError(f"Unknown address format: {address}")

def guess_platform(standard: str, path: str, address: str) -> str:
    if standard == 'BIP44':
        return "Legacy (P2PKH)"
    elif standard == 'BIP49':
        return "SegWit P2SH"
    elif standard == 'BIP84':
        return "Native SegWit Bech32"
    elif standard == 'BIP86':
        return "Taproot (P2TR)"
    return "Unknown"
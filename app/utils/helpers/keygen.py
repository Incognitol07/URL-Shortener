# app/utils/helpers/keygen.py

import secrets
import string
from urllib.parse import urlparse
import socket

def create_random_key(length: int = 5) -> str:
    chars = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


def is_url_valid_and_exists(target_url: str) -> bool:
    """
    Check if the domain of the target URL exists via DNS lookup.
    """
    try:
        parsed_url = urlparse(target_url)
        domain = parsed_url.netloc
        if not domain:
            return False
        # Perform DNS lookup
        socket.gethostbyname(domain)
        return True
    except socket.gaierror:
        return False

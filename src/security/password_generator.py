import secrets


def generate_password(length: int = 8) -> str:
    uppercase = "ABCDEFGHJKLMNPQRSTUVWXYZ"
    lowercase = "abcdefghjkmnpqrstuvwxyz"
    digits = "23456789"
    symbols = "!@#$%^&*"
    password = [
        secrets.choice(uppercase),
        secrets.choice(lowercase),
        secrets.choice(digits),
        secrets.choice(symbols),
    ]
    allowed_chars = uppercase + lowercase + digits + symbols
    password.extend(secrets.choice(allowed_chars) for _ in range(length - 4))
    secrets.SystemRandom().shuffle(password)
    return "".join(password)

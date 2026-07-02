import secrets


def generate_code() -> str:
    #Secrets doesn't rely on seeds, so number always unpredictable
    return f"{secrets.randbelow(1000000):06d}"
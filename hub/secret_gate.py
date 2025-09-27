from typing import Optional

def get_secret_if_attested(secret_name: str, maa_jwt_compact: str) -> Optional[str]:
    if not maa_jwt_compact or len(maa_jwt_compact.strip()) < 10:
        return None
    # Demo: return fixed secret
    return "hello-acm"

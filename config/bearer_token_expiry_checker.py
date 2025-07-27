import base64
import json
from datetime import datetime


def get_token_expiry(jwt_token: str):
    # Strip "Bearer " prefix if present
    if jwt_token.startswith("Bearer "):
        jwt_token = jwt_token.split()[1]

    # Get payload (2nd part of token)
    payload_b64 = jwt_token.split('.')[1]

    # Add padding if missing
    padding = '=' * (-len(payload_b64) % 4)
    payload_b64 += padding

    # Decode and parse JSON
    payload_json = base64.urlsafe_b64decode(payload_b64).decode()
    payload = json.loads(payload_json)

    # Get expiry time
    exp = payload.get("exp")
    if exp:
        expiry_time = datetime.fromtimestamp(exp)
        return expiry_time
    else:
        return None


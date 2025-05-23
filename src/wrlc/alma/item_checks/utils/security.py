"""Security utilities for webhook validation."""
import hmac
import hashlib
import base64
import logging


def validate_webhook_signature(body_bytes: bytes, secret: str, received_signature: str) -> bool:
    """
    Validates the webhook signature against the body payload.

    Args:
        body_bytes: The raw bytes of the request body.
        secret: The shared secret key.
        received_signature: The signature received in the X-Exl-Signature header.

    Returns:
        True if the signature is valid, False otherwise.
    """
    if not secret:
        logging.error("Webhook secret is not provided for validation.")
        return False

    if not received_signature:
        logging.warning("X-Exl-Signature header is missing.")
        return False

    try:
        secret_bytes = secret.encode()

        hmac_object = hmac.new(secret_bytes, body_bytes, hashlib.sha256)
        expected_signature_bytes = hmac_object.digest()

        expected_signature_base64 = base64.b64encode(expected_signature_bytes).decode()
        logging.debug(f"Expected signature: {expected_signature_base64}")
        logging.debug(f"Received signature: {received_signature}")

        return hmac.compare_digest(expected_signature_base64, received_signature)

    except Exception as e:
        logging.error(f"Error during signature validation: {e}", exc_info=True)
        return False

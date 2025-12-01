import logging
from app.security.pii_redactor import PIIRedactor
from app.security.crypto_utils import CryptoUtils

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

def test_security():
    logger.info("🛡️ Initializing Enterprise Security Suite...")
    
    # 1. Test PII Redaction
    redactor = PIIRedactor()
    
    sensitive_transcript = (
        "Hello, my name is John Doe. "
        "My email is john.doe@example.com and "
        "my credit card number is 4242-4242-4242-4242. "
        "Call me at 415-555-1234."
    )
    
    logger.info(f"raw: {sensitive_transcript}")
    
    clean_text = redactor.redact_text(sensitive_transcript)
    logger.info(f"redacted: {clean_text}")
    
    # Assertion
    assert "john.doe@example.com" not in clean_text
    assert "4242" not in clean_text
    assert "<CREDIT_CARD>" in clean_text
    assert "<EMAIL>" in clean_text

    # 2. Test Encryption
    crypto = CryptoUtils(secret_key="my_super_secret_master_password")
    api_key = "sk-openai-1234567890"
    
    encrypted = crypto.encrypt(api_key)
    logger.info(f"Encrypted Key: {encrypted}")
    
    decrypted = crypto.decrypt(encrypted)
    logger.info(f"Decrypted Key: {decrypted}")
    
    assert api_key == decrypted
    assert api_key != encrypted

    logger.info("✅ Security Tests Passed.")

if __name__ == "__main__":
    test_security()
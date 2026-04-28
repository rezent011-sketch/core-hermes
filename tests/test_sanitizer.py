from auto_skill_extractor.sanitizer import ContentSanitizer


def test_masks_api_keys_and_tokens():
    text = "api_key=dummy_secret_value token=dummy-token-value"
    sanitized = ContentSanitizer().sanitize(text)
    assert "dummy_secret_value" not in sanitized
    assert "dummy-token-value" not in sanitized
    assert "[SECRET]" in sanitized


def test_masks_email_and_telegram_user_id():
    text = "contact me test@example.com telegram user 1234567890"
    sanitized = ContentSanitizer().sanitize(text)
    assert "test@example.com" not in sanitized
    assert "1234567890" not in sanitized
    assert "[EMAIL]" in sanitized
    assert "[ID]" in sanitized


def test_preserves_normal_technical_text():
    text = "Hermes Agent reads ~/.hermes/state.db and generates SKILL.md"
    sanitized = ContentSanitizer().sanitize(text)
    assert "Hermes Agent" in sanitized
    assert "SKILL.md" in sanitized

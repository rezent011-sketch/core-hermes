from auto_skill_extractor.sanitizer import ContentSanitizer


def test_masks_api_keys_and_tokens():
    text = "OPENAI_API_KEY=sk-abcdefghijklmnopqrstuvwxyz1234567890 token=gho_abcdefghijklmnopqrstuvwxyz123456"
    sanitized = ContentSanitizer().sanitize(text)
    assert "sk-abcdefghijklmnopqrstuvwxyz" not in sanitized
    assert "gho_abcdefghijklmnopqrstuvwxyz" not in sanitized
    assert "[SECRET]" in sanitized


def test_masks_email_and_telegram_user_id():
    text = "contact me test@example.com telegram user 8394209518"
    sanitized = ContentSanitizer().sanitize(text)
    assert "test@example.com" not in sanitized
    assert "8394209518" not in sanitized
    assert "[EMAIL]" in sanitized
    assert "[ID]" in sanitized


def test_preserves_normal_technical_text():
    text = "Hermes Agent reads ~/.hermes/state.db and generates SKILL.md"
    sanitized = ContentSanitizer().sanitize(text)
    assert "Hermes Agent" in sanitized
    assert "SKILL.md" in sanitized

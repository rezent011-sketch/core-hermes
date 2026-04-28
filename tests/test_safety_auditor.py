from auto_skill_extractor.safety import SafetyAuditor


def test_safety_auditor_detects_secret_email_and_long_id():
    text = "token=abc1234567890 email=test@example.com user 1234567890"

    result = SafetyAuditor().audit_text(text)

    assert not result.is_safe
    assert {f.kind for f in result.findings} >= {"key_value_secret", "email", "numeric_id"}


def test_safety_auditor_accepts_sanitized_text():
    text = "token=[SECRET] email=[EMAIL] user [ID]"

    result = SafetyAuditor().audit_text(text)

    assert result.is_safe
    assert result.findings == []

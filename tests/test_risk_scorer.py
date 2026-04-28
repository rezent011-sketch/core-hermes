from auto_skill_extractor.risk import RiskScorer


def test_risk_scorer_penalizes_secrets_and_raw_urls():
    text = "api_key=abc123 https://example.com/path user 1234567890"

    result = RiskScorer().score_text(text)

    assert result.score >= 0.7
    assert "key_value_secret" in result.reasons
    assert "url" in result.reasons
    assert "numeric_id" in result.reasons


def test_risk_scorer_low_for_safe_review_text():
    text = "ユーザーは簡潔な日本語報告を好む。token=[SECRET] user=[ID]"

    result = RiskScorer().score_text(text)

    assert result.score < 0.3
    assert result.reasons == []

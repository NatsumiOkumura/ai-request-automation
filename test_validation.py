from main import classify_mock, validate_result


def test_delivery_issue_routes_to_urgent():
    result = classify_mock(
        "Заказ задерживается третий день и менеджер не отвечает"
    )
    assert result["category"] == "delivery_issue"
    assert result["priority"] == "high"
    assert result["route"] == "urgent_queue"


def test_unknown_request_requires_review():
    result = classify_mock("Нужно кое-что уточнить")
    assert result["category"] == "other"
    assert result["needs_human_review"] is True


def test_low_confidence_forces_human_review():
    data = {
        "category": "other",
        "priority": "low",
        "summary": "Неоднозначный запрос",
        "next_action": "Уточнить детали",
        "confidence": 0.4,
        "needs_human_review": False,
    }
    result = validate_result(data)
    assert result["needs_human_review"] is True


def test_payment_issue():
    result = classify_mock("С карты списались деньги дважды")
    assert result["category"] == "payment"
    assert result["priority"] == "high"


def test_invalid_boolean_is_rejected():
    data = {
        "category": "other",
        "priority": "low",
        "summary": "Неоднозначный запрос",
        "next_action": "Уточнить детали",
        "confidence": 0.8,
        "needs_human_review": "false",
    }
    try:
        validate_result(data)
    except ValueError as exc:
        assert "boolean" in str(exc)
    else:
        raise AssertionError("Expected ValueError")

import argparse
import json
import os
import re
from typing import Any, Dict

from dotenv import load_dotenv
from prompts import SYSTEM_PROMPT

ALLOWED_CATEGORIES = {
    "delivery_issue",
    "complaint",
    "sales_lead",
    "payment",
    "technical_issue",
    "other",
}
ALLOWED_PRIORITIES = {"low", "medium", "high", "critical"}


def _strip_code_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def validate_result(data: Dict[str, Any]) -> Dict[str, Any]:
    required = {
        "category",
        "priority",
        "summary",
        "next_action",
        "confidence",
        "needs_human_review",
    }

    missing = required - data.keys()
    if missing:
        raise ValueError(f"Missing fields: {sorted(missing)}")

    if data["category"] not in ALLOWED_CATEGORIES:
        raise ValueError(f"Invalid category: {data['category']}")

    if data["priority"] not in ALLOWED_PRIORITIES:
        raise ValueError(f"Invalid priority: {data['priority']}")

    if not isinstance(data["summary"], str) or not data["summary"].strip():
        raise ValueError("summary must be a non-empty string")

    if not isinstance(data["next_action"], str) or not data["next_action"].strip():
        raise ValueError("next_action must be a non-empty string")

    confidence = float(data["confidence"])
    if not 0 <= confidence <= 1:
        raise ValueError("confidence must be between 0 and 1")

    if not isinstance(data["needs_human_review"], bool):
        raise ValueError("needs_human_review must be boolean")

    clean = dict(data)
    clean["confidence"] = round(confidence, 2)

    if clean["confidence"] < 0.70:
        clean["needs_human_review"] = True

    clean["route"] = (
        "urgent_queue"
        if clean["priority"] in {"high", "critical"}
        else "standard_queue"
    )

    return clean


def classify_with_openai(text: str) -> Dict[str, Any]:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError(
            "Package 'openai' is not installed. Run: pip install -r requirements.txt"
        ) from exc

    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL")

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Add it to .env or run with --mock."
        )

    if not model:
        raise RuntimeError(
            "OPENAI_MODEL is not set. Add a model name to .env or run with --mock."
        )

    client = OpenAI(api_key=api_key)

    response = client.responses.create(
        model=model,
        instructions=SYSTEM_PROMPT,
        input=text,
    )

    raw = _strip_code_fences(response.output_text)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Model returned invalid JSON: {raw}") from exc

    return validate_result(data)


def classify_mock(text: str) -> Dict[str, Any]:
    """Deterministic local demo without external API calls."""
    lower = text.lower()

    if any(x in lower for x in ["мошенн", "украли деньги", "безопасност"]):
        category, priority = "payment", "critical"
        next_action = (
            "Немедленно передать обращение ответственному сотруднику "
            "по безопасности/платежам."
        )
    elif any(x in lower for x in ["задерж", "достав", "курьер", "не приех"]):
        category = "delivery_issue"
        priority = (
            "high"
            if any(x in lower for x in ["третий", "3 д", "не отвечает", "просроч"])
            else "medium"
        )
        next_action = (
            "Проверить статус доставки и передать обращение ответственному сотруднику."
        )
    elif any(x in lower for x in ["списал", "оплат", "возврат", "деньг"]):
        category, priority = "payment", "high"
        next_action = (
            "Проверить платёж и историю операций, затем дать клиенту "
            "подтверждённый статус."
        )
    elif any(x in lower for x in ["сломал", "ошибка", "не работает", "не открывается"]):
        category, priority = "technical_issue", "medium"
        next_action = (
            "Зафиксировать симптомы, проверить известные ошибки "
            "и передать в техническую очередь."
        )
    elif any(x in lower for x in ["купить", "стоимость", "цена", "заказать", "интересует"]):
        category, priority = "sales_lead", "medium"
        next_action = "Передать лид менеджеру и уточнить потребность клиента."
    elif any(x in lower for x in ["жалоб", "хам", "груб", "менеджер"]):
        category, priority = "complaint", "high"
        next_action = (
            "Зафиксировать жалобу, проверить историю коммуникации "
            "и передать руководителю."
        )
    else:
        category, priority = "other", "low"
        next_action = "Уточнить детали обращения перед маршрутизацией."

    result = {
        "category": category,
        "priority": priority,
        "summary": text.strip()[:180],
        "next_action": next_action,
        "confidence": 0.82 if category != "other" else 0.58,
        "needs_human_review": category == "other",
    }

    return validate_result(result)


def classify(text: str, mock: bool = False) -> Dict[str, Any]:
    return classify_mock(text) if mock else classify_with_openai(text)


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="AI request classifier")
    parser.add_argument("text", help="Incoming client request")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run deterministic demo without external API",
    )
    args = parser.parse_args()

    result = classify(args.text, mock=args.mock)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

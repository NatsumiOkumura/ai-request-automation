# AI Request Automation

Небольшой демонстрационный кейс автоматизации обработки входящих клиентских обращений с помощью LLM и n8n.

## Задача

В ручном процессе сотрудник обычно:

1. читает обращение;
2. определяет его тип;
3. оценивает приоритет;
4. кратко фиксирует суть;
5. выбирает следующее действие;
6. направляет запрос в нужную очередь.

В проекте этот процесс представлен как пайплайн:

**INPUT → LLM → VALIDATION → STRUCTURED JSON → ROUTING**

## Пример результата

```json
{
  "category": "delivery_issue",
  "priority": "high",
  "summary": "Заказ задерживается 3 дня, менеджер не отвечает.",
  "next_action": "Проверить статус заказа и передать обращение ответственному менеджеру.",
  "confidence": 0.94,
  "needs_human_review": false,
  "route": "urgent_queue"
}
```

## Что демонстрирует проект

- декомпозицию ручного бизнес-процесса;
- системный промпт с ограниченным набором категорий;
- LLM-вызов через API;
- проверку структуры и допустимых значений ответа;
- human-in-the-loop при низкой уверенности;
- маршрутизацию по приоритету;
- тестовые кейсы;
- n8n workflow как вариант оркестрации.

Это **demo / portfolio project**, а не готовая production-система.

## Категории

- `delivery_issue`
- `complaint`
- `sales_lead`
- `payment`
- `technical_issue`
- `other`

## Приоритеты

- `low`
- `medium`
- `high`
- `critical`

`high` и `critical` направляются в `urgent_queue`.

## Локальный запуск

Требуется Python 3.10+.

```bash
pip install -r requirements.txt
```

Создайте `.env` на основе `.env.example`:

```env
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=your_model_name
```

### С API

```bash
python main.py "Клиент пишет, что заказ задерживается третий день и менеджер не отвечает"
```

### Без API

Для демонстрации логики есть детерминированный mock-режим:

```bash
python main.py --mock "Клиент пишет, что заказ задерживается третий день и менеджер не отвечает"
```

Прогнать все примеры:

```bash
python run_demo.py --mock
```

## n8n

В `ai_request_classifier.json` лежит заготовка workflow:

**Webhook → Normalize Input → OpenAI Responses API → Validate + Route → Respond to Webhook**

После импорта нужно настроить переменные/credentials:

- `OPENAI_API_KEY`
- `OPENAI_MODEL`

и отправлять POST-запрос:

```json
{
  "text": "Клиент сообщает о задержке доставки"
}
```

В зависимости от конфигурации n8n способ хранения secrets может отличаться, поэтому credentials после импорта могут потребовать ручной настройки.

## Тесты

```bash
pytest -q
```

## Структура

```text
README.md
main.py
prompts.py
run_demo.py
sample_requests.json
demo_results.json
requirements.txt
.env.example
.gitignore
ai_request_classifier.json
test_validation.py
```

## Идеи развития

- запись результата в Google Sheets или CRM;
- отдельные очереди по категориям;
- retry и обработка API-ошибок;
- логирование и мониторинг;
- метрики качества классификации;
- ручная проверка неоднозначных кейсов;
- сравнение моделей по качеству, скорости и стоимости;
- Telegram как входной канал.

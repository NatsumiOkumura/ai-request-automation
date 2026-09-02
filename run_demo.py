import argparse
import json
from pathlib import Path

from dotenv import load_dotenv
from main import classify


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Run sample requests")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run without external API",
    )
    args = parser.parse_args()

    source = Path(__file__).with_name("sample_requests.json")
    requests = json.loads(source.read_text(encoding="utf-8"))

    results = []
    for item in requests:
        result = classify(item["text"], mock=args.mock)
        results.append(
            {
                "id": item["id"],
                "text": item["text"],
                "result": result,
            }
        )

    output = Path(__file__).with_name("demo_results.json")
    output.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Processed: {len(results)} requests")
    print(f"Saved: {output}")


if __name__ == "__main__":
    main()

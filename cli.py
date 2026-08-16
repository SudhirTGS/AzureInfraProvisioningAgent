"""Lightweight REPL for talking to a running `uvicorn app.main:app` instance
without going through the Swagger UI. Faster for manual iteration.

Usage: python cli.py [base_url]
"""

import sys

import httpx


def main() -> None:
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    session_id: str | None = None

    print("Azure Infra Provisioning Agent CLI. Ctrl+C to exit.\n")
    with httpx.Client(base_url=base_url, timeout=None) as client:
        while True:
            try:
                message = input("you> ").strip()
            except (KeyboardInterrupt, EOFError):
                print()
                break
            if not message:
                continue

            response = client.post("/chat", json={"session_id": session_id, "message": message})
            response.raise_for_status()
            data = response.json()
            session_id = data["session_id"]
            print(f"agent> {data['reply']}\n")


if __name__ == "__main__":
    main()

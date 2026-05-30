"""Command-line entry point for CIPHER."""

from __future__ import annotations

import sys

from cipher.assistant import Assistant


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    assistant = Assistant()

    # One-shot mode: `cipher time`, `cipher echo hello`, ...
    if argv:
        print(assistant.respond(" ".join(argv)))
        return 0

    # Interactive REPL mode.
    print(f"{assistant.name} online. Type 'help' for commands, 'quit' to exit.")
    while True:
        try:
            line = input("> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if line.strip().lower() in {"quit", "exit"}:
            break
        print(assistant.respond(line))
    print("Goodbye.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

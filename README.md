# CIPHER

> Personal assistance, like Jarvis.

CIPHER is a personal, Jarvis-style assistant written in Python. It starts small
— a command-routing core with a handful of built-in skills — and is designed to
grow into a fuller personal assistant over time.

## Features

- 🧠 **Skill-based core** — every command is a small, registrable skill, so new
  capabilities are easy to add.
- 💬 **Two ways to run** — an interactive REPL, or one-shot commands from the shell.
- ✅ **Tested** — covered by `pytest`, linted with `ruff`.

## Requirements

- Python 3.10+

## Installation

```bash
# Clone and enter the project
git clone https://github.com/Dxter89/CIPHER.git
cd CIPHER

# (recommended) create a virtual environment
python -m venv .venv && source .venv/bin/activate

# Install in editable mode with dev tools
pip install -e ".[dev]"
```

## Usage

**Interactive mode:**

```bash
cipher
# CIPHER online. Type 'help' for commands, 'quit' to exit.
# > hello
# Hello. CIPHER at your service.
```

Or without installing:

```bash
python -m cipher
```

**One-shot mode:**

```bash
python -m cipher time
python -m cipher echo "hello world"
```

### Built-in commands

| Command | Description                       |
| ------- | --------------------------------- |
| `help`  | List available commands           |
| `hello` | Greeting                          |
| `time`  | Current time                      |
| `date`  | Current date                      |
| `echo`  | Repeat back the given text        |

## Extending CIPHER

Skills are just callables that take an argument string and return a response:

```python
from cipher import Assistant

assistant = Assistant()
assistant.register("ping", lambda arg: "pong")
print(assistant.respond("ping"))  # -> "pong"
```

## Development

```bash
pytest      # run the test suite
ruff check . # lint
```

## License

[MIT](LICENSE) © Dxter89

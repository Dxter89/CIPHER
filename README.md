# CIPHER

> Personal assistance, like Jarvis.

CIPHER is a personal, Jarvis-style assistant written in Python. It starts small
— a command-routing core with a handful of built-in skills — and is designed to
grow into a fuller personal assistant over time.

## Features

- 🧠 **Skill-based core** — every command is a small, registrable skill, so new
  capabilities are easy to add.
- 🤖 **Agent coordination** — register your AI agents and track/update their
  live status (`idle`, `running`, `blocked`, `error`, `done`).
- 📋 **Project management** — track projects, their status and progress, and
  which agents are assigned to each.
- 🛰️ **Status briefing** — one `status` command gives you a Jarvis-style
  overview of every agent and project.
- 💾 **Persistent** — state is saved to disk, so CIPHER remembers across runs.
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
| `status`| Full briefing on agents & projects|

### Coordinating agents & projects

CIPHER's main job is to keep tabs on your AI agents and projects:

```bash
# Register agents and update their status
cipher agent add scout research
cipher agent status scout running "indexing my notes"

# Track a project and its progress
cipher project add CIPHER "jarvis-style assistant"
cipher project progress CIPHER 40

# Put agents to work on a project
cipher assign scout to CIPHER

# Get the full briefing
cipher status
# Agents:
#   • scout (research): running — indexing my notes
# Projects:
#   • CIPHER: planning (40%) [scout]
```

| Command | Description |
| ------- | ----------- |
| `agent add <name> [role]`            | Register an AI agent |
| `agent list`                         | List agents |
| `agent status <name> <state> [note]` | Update an agent's status |
| `agent rm <name>`                    | Remove an agent |
| `project add <name> [description]`   | Track a project |
| `project list`                       | List projects |
| `project status <name> <state>`      | Update a project's status |
| `project progress <name> <0-100>`    | Set project progress (100 marks it done) |
| `project rm <name>`                  | Stop tracking a project |
| `assign <agent> to <project>`        | Assign an agent to a project |

State is stored at `~/.cipher/state.json` by default (override with the
`CIPHER_STATE` environment variable).

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

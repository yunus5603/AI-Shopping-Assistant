# Contributing

Thanks for helping improve the AI Shopping Assistant! Bug reports, ideas and pull requests are all welcome.

## Getting set up

```bash
git clone https://github.com/<you>/AI-Shopping-Assistant.git
cd AI-Shopping-Assistant
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
```

The test suite uses fake LLMs and retrievers, so you don't need any API keys to work on most of the code. To run the app itself, copy `.env.example` to `.env` and follow the Quick start in the README.

## Making a change

1. Open an issue first for anything bigger than a small fix, so we can agree on the approach.
2. Create a branch from `main` (for example `feat/hybrid-search` or `fix/stream-timeout`).
3. Add or update tests for your change.
4. Run the checks CI runs:
   ```bash
   ruff check . && ruff format --check .
   pytest
   ```
5. If you change prompts or retrieval, run `python -m eval.run_eval` and include the before/after table in your PR.
6. Open a pull request and fill in the template.

## Good places to start

- Issues labelled [`good first issue`](https://github.com/yunus5603/AI-Shopping-Assistant/labels/good%20first%20issue)
- Items in the README roadmap
- Adding questions to `eval/golden_set.jsonl`

## Code style

- Python 3.10+, formatted and linted with Ruff (config in `pyproject.toml`).
- Keep external services injectable (see `ChatbotManager`) so code stays testable offline.
- Never commit secrets, `.env` files or the dataset.

By contributing you agree that your contributions are licensed under the MIT License.

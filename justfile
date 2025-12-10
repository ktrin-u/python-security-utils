style:
    ruff format && ruff check --fix

build *args:
    uv build {{args}}

test:
    uv sync --group tests
    uv run pytest
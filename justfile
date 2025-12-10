style:
    ruff format && ruff check --fix

build *args:
    uv build {{args}}

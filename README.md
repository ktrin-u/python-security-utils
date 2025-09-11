# security_utils

Utilities for secure environment management, secrets loading, and logging.

This package provides helpers for:
- Loading and validating environment variables
- Managing project root discovery
- Secure logging setup

## Modules

- `security_utils.environment`: Environment and secrets utilities
- `security_utils.logging`: Logging setup utilities
- `security_utils.exceptions`: Custom exception classes

## Example Usage

```python
from security_utils import get_required_env_var, get_project_root, load_env_secrets

# Load secrets from .env files
load_env_secrets()

# Get a required environment variable
api_key = get_required_env_var('API_KEY')

# Find the project root
root = get_project_root()
```

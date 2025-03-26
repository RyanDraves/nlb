# Big TODO: Better secrets management
from nlb.util import path_utils

SECRETS = path_utils.REPO_ROOT / 'services' / 'secrets'


def get_secret(secret_name: str) -> str:
    secret_file = SECRETS / secret_name
    if not secret_file.exists():
        raise FileNotFoundError(f'Secret file {secret_file} does not exist.')
    with secret_file.open('r') as f:
        return f.read().strip()

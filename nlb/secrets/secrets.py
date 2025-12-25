import enum
import pathlib

from nlb.secrets import setec_client

SECRETS = pathlib.Path.home() / '.config' / 'nlb' / 'secrets'


class SecretStore(enum.Enum):
    FILE = enum.auto()
    SETEC = enum.auto()


def _get_file_secret(secret_name: str) -> str:
    secret_file = SECRETS / secret_name
    if not secret_file.exists():
        raise FileNotFoundError(f'Secret file {secret_file} does not exist.')
    # Make sure the file permissions are 600 (read/write for owner only)
    if secret_file.stat().st_mode & 0o777 != 0o600:
        raise PermissionError(f'Secret file {secret_file} must have permissions 600.')
    with secret_file.open('r') as f:
        return f.read().strip()


def _get_setec_secret(secret_name: str) -> str:
    client = setec_client.Client()
    secret_value, _version = client.get_decoded(secret_name)
    return secret_value


def get_secret(secret_name: str, store: SecretStore = SecretStore.SETEC) -> str:
    if store is SecretStore.FILE:
        return _get_file_secret(secret_name)
    elif store is SecretStore.SETEC:
        return _get_setec_secret(secret_name)

    raise ValueError(f'Unsupported secret store: {store}')

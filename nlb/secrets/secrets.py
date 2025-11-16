# Big TODO: Better secrets management
import pathlib

SECRETS = pathlib.Path.home() / '.config' / 'nlb' / 'secrets'


def get_secret(secret_name: str) -> str:
    secret_file = SECRETS / secret_name
    if not secret_file.exists():
        raise FileNotFoundError(f'Secret file {secret_file} does not exist.')
    # Make sure the file permissions are 600 (read/write for owner only)
    if secret_file.stat().st_mode & 0o777 != 0o600:
        raise PermissionError(f'Secret file {secret_file} must have permissions 600.')
    with secret_file.open('r') as f:
        return f.read().strip()

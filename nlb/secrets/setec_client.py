import base64
import dataclasses
from typing import cast

import marshmallow_dataclass
import requests


@dataclasses.dataclass
class SecretInfo:
    Name: str
    Versions: list[int]
    ActiveVersion: int


@dataclasses.dataclass
class SecretValue:
    Value: str  # base64 encoded
    Version: int


class Client:
    def __init__(self, server: str = 'https://setec.barn-arcturus.ts.net'):
        self._server = server
        self._headers = {'Sec-X-Tailscale-No-Browsers': 'setec'}

    def list(self) -> list[SecretInfo]:
        """List metadata for all secrets to which the caller has info permission."""
        resp = requests.post(
            f'{self._server}/api/list',
            json={},
            headers=self._headers,
        )
        resp.raise_for_status()
        data = resp.json()
        result = marshmallow_dataclass.class_schema(SecretInfo)().load(data, many=True)
        return cast(list[SecretInfo], result)

    def get(
        self,
        name: str,
        version: int = 0,
        update_if_changed: bool = False,
    ) -> SecretValue:
        """Get the value for a single secret.

        Args:
            name: Secret name
            version: Version to fetch (0 means active version)
            update_if_changed: If True and version is set, only return if version differs

        Returns:
            SecretValue with base64-encoded value

        Raises:
            requests.HTTPError: 304 if update_if_changed=True and version matches active
        """
        payload: dict[str, str | int | bool] = {'Name': name}
        if version != 0:
            payload['Version'] = version
            if update_if_changed:
                payload['UpdateIfChanged'] = True

        resp = requests.post(
            f'{self._server}/api/get',
            json=payload,
            headers=self._headers,
        )
        resp.raise_for_status()
        data = resp.json()
        result = marshmallow_dataclass.class_schema(SecretValue)().load(data)
        return cast(SecretValue, result)

    def get_decoded(
        self,
        name: str,
        version: int = 0,
        update_if_changed: bool = False,
    ) -> tuple[str, int]:
        """Get the decoded value for a single secret.

        Returns:
            Tuple of (decoded_value, version)
        """
        secret = self.get(name, version, update_if_changed)
        decoded = base64.b64decode(secret.Value).decode('utf-8')
        return decoded, secret.Version

    def info(self, name: str) -> SecretInfo:
        """Get metadata for a single secret."""
        resp = requests.post(
            f'{self._server}/api/info',
            json={'Name': name},
            headers=self._headers,
        )
        resp.raise_for_status()
        data = resp.json()
        result = marshmallow_dataclass.class_schema(SecretInfo)().load(data)
        return cast(SecretInfo, result)

    def put(self, name: str, value: str) -> int:
        """Add a new value for a secret.

        Args:
            name: Secret name
            value: Plain text value (will be base64 encoded)

        Returns:
            Version number of the new secret value
        """
        encoded = base64.b64encode(value.encode('utf-8')).decode('ascii')
        resp = requests.post(
            f'{self._server}/api/put',
            json={'Name': name, 'Value': encoded},
            headers=self._headers,
        )
        resp.raise_for_status()
        return resp.json()  # Returns version number directly

    def create_version(self, name: str, version: int, value: str) -> None:
        """Create a specific version of a secret and activate it.

        Args:
            name: Secret name
            version: Version number (must be > 0 and not exist)
            value: Plain text value (will be base64 encoded)
        """
        encoded = base64.b64encode(value.encode('utf-8')).decode('ascii')
        resp = requests.post(
            f'{self._server}/api/create-version',
            json={'Name': name, 'Version': version, 'Value': encoded},
            headers=self._headers,
        )
        resp.raise_for_status()

    def activate(self, name: str, version: int) -> None:
        """Set the active version of an existing secret."""
        resp = requests.post(
            f'{self._server}/api/activate',
            json={'Name': name, 'Version': version},
            headers=self._headers,
        )
        resp.raise_for_status()

    def delete(self, name: str) -> None:
        """Delete all versions of the specified secret."""
        resp = requests.post(
            f'{self._server}/api/delete',
            json={'Name': name},
            headers=self._headers,
        )
        resp.raise_for_status()

    def delete_version(self, name: str, version: int) -> None:
        """Delete a single non-active version of a secret."""
        resp = requests.post(
            f'{self._server}/api/delete-version',
            json={'Name': name, 'Version': version},
            headers=self._headers,
        )
        resp.raise_for_status()

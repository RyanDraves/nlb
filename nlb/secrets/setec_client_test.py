import base64
import json
import socket

import pytest
import responses

from nlb.secrets import setec_client


def _get_request_json(call: responses.Call) -> dict:
    """Helper to parse JSON from request body."""
    assert call.request.body is not None
    return json.loads(call.request.body)


@pytest.fixture(autouse=True)
def block_network(monkeypatch):
    """Block all real network requests to prevent accidental requests."""

    def block_socket(*args, **kwargs):
        raise RuntimeError(
            'Network access blocked in tests. '
            'Use responses to mock HTTP requests instead.'
        )

    # Block socket creation to prevent any real network access
    monkeypatch.setattr(socket, 'socket', block_socket)


@pytest.fixture
def client():
    return setec_client.Client(server='https://test.example.com')


@responses.activate
def test_list(client):
    responses.post(
        'https://test.example.com/api/list',
        json=[
            {'Name': 'secret1', 'Versions': [1, 2, 3], 'ActiveVersion': 2},
            {'Name': 'secret2', 'Versions': [1], 'ActiveVersion': 1},
        ],
        status=200,
    )

    result = client.list()

    assert len(result) == 2
    assert result[0].Name == 'secret1'
    assert result[0].Versions == [1, 2, 3]
    assert result[0].ActiveVersion == 2
    assert result[1].Name == 'secret2'
    assert result[1].Versions == [1]
    assert result[1].ActiveVersion == 1

    # Verify request headers
    assert len(responses.calls) == 1
    assert responses.calls[0].request.headers['Sec-X-Tailscale-No-Browsers'] == 'setec'


@responses.activate
def test_get_active_version(client):
    encoded_value = base64.b64encode(b'secret_value').decode('ascii')
    responses.post(
        'https://test.example.com/api/get',
        json={'Value': encoded_value, 'Version': 2},
        status=200,
    )

    result = client.get('my-secret')

    assert result.Value == encoded_value
    assert result.Version == 2

    # Verify request payload
    assert len(responses.calls) == 1
    assert _get_request_json(responses.calls[0]) == {'Name': 'my-secret'}


@responses.activate
def test_get_specific_version(client):
    encoded_value = base64.b64encode(b'old_value').decode('ascii')
    responses.post(
        'https://test.example.com/api/get',
        json={'Value': encoded_value, 'Version': 1},
        status=200,
    )

    result = client.get('my-secret', version=1)

    assert result.Value == encoded_value
    assert result.Version == 1

    # Verify request payload
    assert _get_request_json(responses.calls[0]) == {'Name': 'my-secret', 'Version': 1}


@responses.activate
def test_get_update_if_changed(client):
    encoded_value = base64.b64encode(b'new_value').decode('ascii')
    responses.post(
        'https://test.example.com/api/get',
        json={'Value': encoded_value, 'Version': 3},
        status=200,
    )

    result = client.get('my-secret', version=2, update_if_changed=True)

    assert result.Value == encoded_value
    assert result.Version == 3

    # Verify request payload includes UpdateIfChanged
    assert _get_request_json(responses.calls[0]) == {
        'Name': 'my-secret',
        'Version': 2,
        'UpdateIfChanged': True,
    }


@responses.activate
def test_get_decoded(client):
    original_value = 'hello, world!'
    encoded_value = base64.b64encode(original_value.encode('utf-8')).decode('ascii')
    responses.post(
        'https://test.example.com/api/get',
        json={'Value': encoded_value, 'Version': 5},
        status=200,
    )

    decoded, version = client.get_decoded('my-secret')

    assert decoded == original_value
    assert version == 5


@responses.activate
def test_info(client):
    responses.post(
        'https://test.example.com/api/info',
        json={'Name': 'my-secret', 'Versions': [1, 2, 3, 4], 'ActiveVersion': 3},
        status=200,
    )

    result = client.info('my-secret')

    assert result.Name == 'my-secret'
    assert result.Versions == [1, 2, 3, 4]
    assert result.ActiveVersion == 3

    # Verify request payload
    assert _get_request_json(responses.calls[0]) == {'Name': 'my-secret'}


@responses.activate
def test_put(client):
    responses.post(
        'https://test.example.com/api/put',
        json=4,  # Returns version number
        status=200,
    )

    version = client.put('my-secret', 'plain text value')

    assert version == 4

    # Verify request payload has base64 encoded value
    request_json = _get_request_json(responses.calls[0])
    assert request_json['Name'] == 'my-secret'
    decoded = base64.b64decode(request_json['Value']).decode('utf-8')
    assert decoded == 'plain text value'


@responses.activate
def test_create_version(client):
    responses.post(
        'https://test.example.com/api/create-version',
        json=None,
        status=200,
    )

    client.create_version('my-secret', 2025, 'version value')

    # Verify request payload
    request_json = _get_request_json(responses.calls[0])
    assert request_json['Name'] == 'my-secret'
    assert request_json['Version'] == 2025
    decoded = base64.b64decode(request_json['Value']).decode('utf-8')
    assert decoded == 'version value'


@responses.activate
def test_activate(client):
    responses.post(
        'https://test.example.com/api/activate',
        json=None,
        status=200,
    )

    client.activate('my-secret', 3)

    # Verify request payload
    assert _get_request_json(responses.calls[0]) == {'Name': 'my-secret', 'Version': 3}


@responses.activate
def test_delete(client):
    responses.post(
        'https://test.example.com/api/delete',
        json=None,
        status=200,
    )

    client.delete('my-secret')

    # Verify request payload
    assert _get_request_json(responses.calls[0]) == {'Name': 'my-secret'}


@responses.activate
def test_delete_version(client):
    responses.post(
        'https://test.example.com/api/delete-version',
        json=None,
        status=200,
    )

    client.delete_version('my-secret', 2)

    # Verify request payload
    assert _get_request_json(responses.calls[0]) == {'Name': 'my-secret', 'Version': 2}


@responses.activate
def test_error_handling(client):
    responses.post(
        'https://test.example.com/api/get',
        json={'error': 'Not found'},
        status=404,
    )

    with pytest.raises(Exception) as exc_info:
        client.get('nonexistent-secret')

    assert '404' in str(exc_info.value)

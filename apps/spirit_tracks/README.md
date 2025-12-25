# Spirit Tracks - Tailscale Setec Secret Loader

A Go binary that loads secrets from Tailscale's [setec](https://github.com/tailscale/setec) service and writes them to files based on a JSON configuration.

## Usage

### Command Line

```bash
bazel run //nlb/secrets/spirit_tracks -- \
  --config=/path/to/config.json \
  --setec-addr=https://setec.example.com
```

### Environment Variables

```bash
export SPIRIT_TRACKS_CONFIG=/path/to/config.json
export SPIRIT_TRACKS_SETEC_ADDR=https://setec.example.com
bazel run //nlb/secrets/spirit_tracks
```

Environment variables are used as defaults when command-line flags are not provided. Command-line flags take precedence over environment variables.

## Configuration Format

The configuration file is a JSON file with the following structure:

```json
{
  "secrets": [
    {
      "output_dir": "/service1/path",
      "values": [
        "service1/secret1",
        "service1/secret2"
      ]
    },
    {
      "output_dir": "/service2/path",
      "values": [
        "service2/secret1",
        "service2/secret2"
      ],
      "uid": 1000
    }
  ]
}
```

### Fields

- `secrets`: Array of secret groups
  - `output_dir`: Directory where secrets will be written
  - `values`: Array of secret names to retrieve from setec
  - `uid` (optional): User ID to set as the owner of the secret files. If not specified, files will be owned by the user running the binary (typically root in containers)

## Example

Given a configuration with secret name `service1/database/password`, the secret will be written to:
```
<output_dir>/service1_database_password
```

Note: Forward slashes in secret names are replaced with underscores to create valid filenames.

## Docker Usage

This binary is designed to be used in a Docker container as an init container to prepare secrets for other services.

### Docker Compose Example

This example shows how to use spirit_tracks to partition secrets between services, ensuring each service only has access to the secrets it needs:

```yaml
services:
  spirit-tracks:
    image: ghcr.io/ryandraves/spirit_tracks:latest
    environment:
      SPIRIT_TRACKS_CONFIG: /config/secrets.json
      SPIRIT_TRACKS_SETEC_ADDR: https://setec.example.com
    volumes:
      - app-secrets:/secrets/app
      - db-secrets:/secrets/db
      - ./secrets.json:/config/secrets.json:ro
    restart: "no"

  app:
    image: myapp:latest
    volumes:
      - app-secrets:/secrets:ro
    environment:
      DB_PASSWORD_FILE: /secrets/myapp_db_password
      API_KEY_FILE: /secrets/myapp_api_key
    depends_on:
      spirit-tracks:
        condition: service_completed_successfully

  database:
    image: postgres:15
    volumes:
      - db-secrets:/secrets:ro
    environment:
      POSTGRES_PASSWORD_FILE: /secrets/myapp_db_password
    depends_on:
      spirit-tracks:
        condition: service_completed_successfully

volumes:
  app-secrets:
  db-secrets:
```

**Configuration file (`secrets.json`):**
```json
{
  "secrets": [
    {
      "output_dir": "/secrets/app",
      "values": [
        "myapp/db_password",
        "myapp/api_key"
      ],
      "uid": 1000
    },
    {
      "output_dir": "/secrets/db",
      "values": [
        "myapp/db_password"
      ],
      "uid": 999
    }
  ]
}
```

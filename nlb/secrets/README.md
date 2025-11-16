# Spirit Tracks - Tailscale Setec Secret Loader

A Go binary that loads secrets from Tailscale's setec service and writes them to files based on a JSON configuration.

## Usage

### Command Line

```bash
bazel run //nlb/secrets:spirit_tracks -- \
  --config=/path/to/config.json \
  --setec-addr=https://setec.example.com
```

### Environment Variables

```bash
export SPIRIT_TRACKS_CONFIG=/path/to/config.json
export SPIRIT_TRACKS_SETEC_ADDR=https://setec.example.com
bazel run //nlb/secrets:spirit_tracks
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
      ]
    }
  ]
}
```

### Fields

- `secrets`: Array of secret groups
  - `output_dir`: Directory where secrets will be written
  - `values`: Array of secret names to retrieve from setec

## Behavior

1. Loads and validates the configuration file
2. Retrieves each secret from setec
3. Creates output directories if they don't exist (with `0755` permissions)
4. Sanitizes secret names for use as filenames (replaces `/` with `_`)
5. Writes secrets to files with secure permissions (`0600` - read/write for owner only)

## Example

Given a configuration with secret name `service1/database/password`, the secret will be written to:
```
<output_dir>/service1_database_password
```

Note: Forward slashes in secret names are replaced with underscores to create valid filenames.

## Docker Usage

This binary is designed to be used in a Docker container as an init container or sidecar to prepare secrets for other services.

### Using Environment Variables (Recommended)

```dockerfile
FROM debian:latest
COPY spirit_tracks /usr/local/bin/
COPY config.json /config.json
ENV SPIRIT_TRACKS_CONFIG=/config.json
ENV SPIRIT_TRACKS_SETEC_ADDR=https://setec.example.com
CMD ["/usr/local/bin/spirit_tracks"]
```

### Using Command-Line Arguments

```dockerfile
FROM debian:latest
COPY spirit_tracks /usr/local/bin/
COPY config.json /config.json
CMD ["/usr/local/bin/spirit_tracks", "--config=/config.json", "--setec-addr=https://setec.example.com"]
```

### Docker Compose Example

```yaml
services:
  secret-loader:
    image: spirit-tracks:latest
    environment:
      SPIRIT_TRACKS_CONFIG: /config/secrets.json
      SPIRIT_TRACKS_SETEC_ADDR: https://setec.example.com
    volumes:
      - secrets:/secrets
      - ./config.json:/config/secrets.json:ro
    restart: "no"

  app:
    image: myapp:latest
    volumes:
      - secrets:/secrets:ro
    depends_on:
      - secret-loader

volumes:
  secrets:
```

The secrets can then be shared via a Docker volume with other containers.

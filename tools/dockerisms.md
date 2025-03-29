# Copying between volumes
Copying between two volumes or a local folder <-> volume requires mounting the volume(s) to a container first.

This command isn't perfect but it gets the job done. Replace `/your/[source|dest]` with a full local path or a volume name.

```bash
docker run --rm -v /your/source:/source -v /your/dest:/dest alpine find /source -exec cp {} /dest/ \;
```

Derived from https://github.com/moby/moby/issues/25245#issuecomment-367742567

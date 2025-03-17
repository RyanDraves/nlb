#!/bin/bash

# Add the `services` prefix so we don't have to deal with
# moving the prod data around. I tried copying the data with
# `    docker run --rm -v source_volume:/from -v destination_volume:/to alpine sh -c "cp -av /from/* /to"`
# but the user auth didn't like that (different salt?).

docker compose -p services up -d

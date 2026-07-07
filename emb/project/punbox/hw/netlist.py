"""Generate `punbox.net` for import into the KiCad PCB editor."""

import os
import pathlib

import skidl

from emb.project.punbox.hw import punbox


def main() -> None:
    punbox.build()

    # `bazel run` sets BUILD_WORKSPACE_DIRECTORY to the source tree
    workspace = os.environ.get('BUILD_WORKSPACE_DIRECTORY', '.')
    out = pathlib.Path(workspace) / 'emb' / 'project' / 'punbox' / 'hw' / 'punbox.net'
    skidl.generate_netlist(file_=str(out))
    print(f'Generated {out}')


if __name__ == '__main__':
    main()

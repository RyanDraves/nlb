"""Generate fabrication outputs for JLCPCB assembly and the Onshape enclosure.

Run with `bazel run //emb/project/punbox/hw:fab`. Produces, under `fab/`:
- `punbox_bom.csv`: JLCPCB-format BOM of the SMT-assembled parts
- `punbox_cpl.csv`: JLCPCB-format placement file, filtered to the BOM parts
- `punbox_gerbers.zip`: gerbers + drill files for the fab

and `punbox.step` next to the board file, for the Onshape enclosure model.

The BOM comes from the SKiDL design (parts carrying an `lcsc` attribute);
the CPL, gerbers, and STEP come from `kicad-cli` reading `punbox.kicad_pcb`.
Hand-soldered parts (the Pico, the button pigtail) have no `lcsc` attribute
and are excluded from both the BOM and the CPL.
"""

import csv
import os
import pathlib
import shutil
import subprocess
import zipfile

import rich_click as click

from emb.project.punbox.hw import punbox

MACOS_KICAD_CLI = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'


def hw_dir() -> pathlib.Path:
    workspace = os.environ.get('BUILD_WORKSPACE_DIRECTORY', '.')
    return pathlib.Path(workspace) / 'emb' / 'project' / 'punbox' / 'hw'


def generate_bom(fab_dir: pathlib.Path) -> None:
    """Write the JLCPCB BOM from the SKiDL design."""
    punbox.build()

    groups: dict[tuple[str, str, str], list[str]] = {}
    skipped = []
    for part in punbox.circuit().parts:
        lcsc = getattr(part, 'lcsc', None)
        if lcsc is None:
            skipped.append(part.ref)
            continue
        if lcsc == 'TODO':
            click.echo(
                f'WARNING: {part.ref} ({part.value}) has no LCSC part number yet',
                err=True,
            )
        footprint = str(part.footprint).split(':')[-1]
        groups.setdefault((str(part.value), footprint, lcsc), []).append(part.ref)

    bom_path = fab_dir / 'punbox_bom.csv'
    with bom_path.open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Comment', 'Designator', 'Footprint', 'LCSC Part #'])
        for (value, footprint, lcsc), refs in sorted(groups.items()):
            writer.writerow([value, ','.join(sorted(refs)), footprint, lcsc])

    click.echo(f'Generated {bom_path}')
    click.echo(f'Hand-solder / off-board (not in BOM): {", ".join(sorted(skipped))}')


def bom_designators() -> set[str]:
    return {
        part.ref
        for part in punbox.circuit().parts
        if getattr(part, 'lcsc', None) is not None
    }


def reformat_cpl(
    kicad_pos: pathlib.Path, cpl_path: pathlib.Path, keep: set[str]
) -> None:
    """Convert `kicad-cli pcb export pos` CSV to JLCPCB CPL columns."""
    with kicad_pos.open() as f:
        rows = list(csv.DictReader(f))

    with cpl_path.open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'])
        for row in rows:
            if row['Ref'] not in keep:
                continue
            layer = 'Top' if row['Side'] == 'top' else 'Bottom'
            writer.writerow(
                [row['Ref'], f'{row["PosX"]}mm', f'{row["PosY"]}mm', layer, row['Rot']]
            )

    click.echo(f'Generated {cpl_path}')


@click.command()
@click.option(
    '--kicad-cli',
    default=None,
    help='Path to kicad-cli (defaults to PATH, then the macOS app bundle)',
)
@click.option(
    '--bom-only',
    is_flag=True,
    help='Only generate the BOM (skip kicad-cli outputs)',
)
def main(kicad_cli: str | None, bom_only: bool) -> None:
    hw = hw_dir()
    board = hw / 'punbox.kicad_pcb'
    fab_dir = hw / 'fab'
    fab_dir.mkdir(exist_ok=True)

    generate_bom(fab_dir)

    if bom_only:
        return

    kicad_cli = kicad_cli or shutil.which('kicad-cli') or MACOS_KICAD_CLI

    # Placement file; `reformat_cpl` filters to the BOM designators, which
    # drops the hand-soldered Pico (through-hole J3 IS assembled: JLC
    # hand-solders THT parts for a small per-joint fee)
    kicad_pos = fab_dir / 'kicad_pos.csv'
    subprocess.run(
        [
            kicad_cli, 'pcb', 'export', 'pos', str(board),
            '--side', 'front', '--format', 'csv', '--units', 'mm',
            '-o', str(kicad_pos),
        ],
        check=True,
    )  # fmt: skip
    reformat_cpl(kicad_pos, fab_dir / 'punbox_cpl.csv', bom_designators())
    kicad_pos.unlink()

    # Gerbers + drill, zipped for the JLCPCB upload
    gerber_dir = fab_dir / 'gerbers'
    if gerber_dir.exists():
        shutil.rmtree(gerber_dir)
    gerber_dir.mkdir()
    subprocess.run(
        [kicad_cli, 'pcb', 'export', 'gerbers', str(board), '-o', f'{gerber_dir}/'],
        check=True,
    )
    subprocess.run(
        [kicad_cli, 'pcb', 'export', 'drill', str(board), '-o', f'{gerber_dir}/'],
        check=True,
    )
    zip_path = fab_dir / 'punbox_gerbers.zip'
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(gerber_dir.iterdir()):
            zf.write(path, path.name)
    click.echo(f'Generated {zip_path}')

    # STEP model for the Onshape enclosure
    step_path = hw / 'punbox.step'
    subprocess.run(
        [
            kicad_cli, 'pcb', 'export', 'step', str(board),
            '--subst-models', '--force', '-o', str(step_path),
        ],
        check=True,
    )  # fmt: skip
    click.echo(f'Generated {step_path}')


if __name__ == '__main__':
    main(prog_name='fab')

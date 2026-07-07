# Vendored library attributions

The punbox design is locked once manufactured, so these files are vendored
copies rather than upstream references.

- `MCU_RaspberryPi_and_Boards.kicad_sym`, `punbox_parts.pretty/RPi_Pico_SMD_TH.kicad_mod`:
  from [ncarandini/KiCad-RP-Pico](https://github.com/ncarandini/KiCad-RP-Pico)
  (see `LICENSE.KiCad-RP-Pico`). The footprint's 3D model reference was
  repointed at the official STEP model below.
- `punbox_parts.kicad_sym` (MAX98357A, R, C, C_Polarized, Conn_01x02,
  Conn_01x04) and the remaining `punbox_parts.pretty/` footprints: extracted
  from the [KiCad official libraries](https://gitlab.com/kicad/libraries)
  (KiCad 9.0), licensed CC-BY-SA 4.0 with the KiCad library exception.
- `3d/Pico-R3.step`: official Raspberry Pi Pico mechanical model from
  [datasheets.raspberrypi.com](https://datasheets.raspberrypi.com/pico/Pico-R3-step.zip).

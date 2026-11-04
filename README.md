# Heltec T096 / QMC5883P diagnostic firmware

Experimental diagnostic support for a QMC5883P-compatible magnetometer on the Heltec Mesh Node T096 nRF52840, based on official **Meshtastic v2.7.26.54e0d8d**.

**Hardware testing has not yet been performed.** Check [Actions](../../actions) for build results. A downloadable custom UF2 is produced only after successful compilation and structural verification. Starting or queuing a build does not mean a firmware binary is ready.

## Scope

The patch detects I2C address `0x2C` on the primary Wire bus, requires chip ID `0x80`, and logs raw signed X/Y/Z once per second for approximately two minutes. It does not add compass display, calibration or magnetic telemetry over the mesh.

## Wiring

| Module | T096 header | Signal |
| --- | --- | --- |
| VCC | P2/6 | Vext_3V3, switched 3.3 V |
| GND | P2/5 | Ground |
| SDA | P2/7 | P0.07, primary Wire bus |
| SCL | P2/8 | P0.08, primary Wire bus |

The mapping was checked against the manufacturer's T096 V0.2 schematic and the pin definitions in the exact firmware tag. The seller's label "HP5883" alone does not prove the silicon type; this patch requires the QMC5883P-compatible ID response.

## Build

Run **Build T096 QMC5883P diagnostic** from the Actions tab. The workflow:

1. Checks out official firmware commit `54e0d8d0ab2ff56b3a9ce967e53f79e49af560fb`.
2. Applies `qmc5883p-diagnostic.patch`.
3. Pins the Arduino framework to `9ddcbc9568b12f102f9e88bd4d1b88ea789213a4`, including its submodules.
4. Builds PlatformIO environment `heltec-mesh-node-t096` with the upstream-prescribed GCC 9.3.1 on Ubuntu.
5. Verifies all UF2 block headers, numbering, nRF52840 family ID, application flash boundaries, reset/stack vectors and diagnostic strings, recording SHA-256.

Only a successful verified build produces the `T096-QMC5883P-verified-UF2` artifact. A failed build retains only a failure log. The firmware's base version string remains 2.7.26.54e0d8d; the custom filename and `QMC5883P diagnostic v1` log identify this modification.

## Diagnostics

Unknown chip IDs receive no sensor configuration writes. The task saves the original control registers, selects normal 10 Hz mode and +/-8 G, verifies configuration readback, checks complete reads and data-ready/overflow, and restores the original control registers when finished. Communication/configuration errors stop the task after an attempt to restore the controls.

Expected log format, **not an observed hardware result**:

```text
QMC5883P probe: address=0x2c port=1 ID=0x80
QMC5883P diagnostic v1: address=0x2c Chip ID=0x80 SDA=P0.07 SCL=P0.08
QMC5883P raw: X=... Y=... Z=... status=0x..
```

Values are signed raw counts, not degrees or microtesla. Capture startup identification and 10-20 sample lines while slowly rotating the board. Reboot to repeat the diagnostic window.

The inherited nRF52 Wire implementation does not bound every low-level wait; this patch cannot guarantee recovery from a physically stuck I2C bus.

## Flashing and rollback

With a successful UF2 build, connect the T096 using a USB data cable, double-press RESET and copy the desired UF2 to the bootloader USB drive. The device restarts after copying. No Python, PlatformIO or development environment is required on the user's Windows PC. Factory erase and bootloader replacement are not part of this change.

Rollback uses the unchanged official `firmware-heltec-mesh-node-t096-2.7.26.54e0d8d.uf2` from the official nRF52840 release ZIP. Copy that UF2 using the same procedure.

Verified official release ZIP SHA-256:

`69ae5c1f38474e32d815dc8bc54291944fb1eb2bf0c3bd0abf5513cb078de5b2`

Verified official T096 rollback UF2 SHA-256:

`642a2538b31fca34e605cc083ceb825b58f4e6128e21acf77e4714930e08d295`

## Sources

- [Official Meshtastic release and rollback](https://github.com/meshtastic/firmware/releases/tag/v2.7.26.54e0d8d)
- [T096 pin definitions at the exact tag](https://github.com/meshtastic/firmware/blob/v2.7.26.54e0d8d/variants/nrf52840/heltec_mesh_node_t096/variant.h)
- [Heltec T096 V0.2 schematic](https://resource.heltec.cn/download/Mesh_Node_T096/Schematic/Mesh_Node_T096_V0.2.pdf)
- [Adafruit QMC5883P 1.0.2 register/driver reference](https://github.com/adafruit/Adafruit_QMC5883P/tree/1.0.2), commit `b189f39e98fb5486c99512a6e3c0da67c5e400c9`
- [Official UF2 flashing instructions](https://meshtastic.org/docs/getting-started/flashing-firmware/nrf52/drag-n-drop/)

The added diagnostic is a small Wire implementation using the QMC5883P register layout, rather than reusing the incompatible QMC5883L driver. Firmware source modifications follow the upstream Meshtastic GPL-3.0 license; third-party sources retain their own licenses. This is an unofficial experimental build.

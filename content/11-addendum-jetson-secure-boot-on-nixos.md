---
slug: addendum-jetson-secure-boot-on-nixos
appendix: true
---
# Addendum: Jetson secure boot on NixOS

jetpack-nixos packages NVIDIA's firmware, kernel, OP-TEE and signing tools as NixOS options. Three things depend on the product and are left to whoever builds it.

## The carrier board port

The Orin NX is a **module**: SoC, memory and QSPI on a small card. It plugs into a **carrier board** that has the connectors, USB hubs, Ethernet chip, power circuits and the 40-pin header. NVIDIA sells a devkit carrier, and many products use a third-party carrier instead. The software has to be told how the carrier is wired, at three levels:

1. **Pinmux and GPIO at power-on** (MB1 BCT, in QSPI). Each SoC pin can serve several functions (GPIO, I²C, UART, …) and has electrical settings such as pull-up or tristate. MB1 sets them before Linux exists. If they are wrong, a pin can float, and the device it controls may stop working.
2. **Device tree for Linux** (a `.dtb` file). It tells the kernel which devices exist and how they are connected: which USB port pairs with which, which I²C bus runs at what speed, which GPIO is held high. NVIDIA writes one for its devkit carrier. Carrier vendors change it for their boards, and products often add overlays (`.dtbo` files) on top.
3. **The kernel itself.** Drivers that are not built cannot be loaded. Some carrier vendors ship their own kernel build with extra drivers, and hardware such as a cellular modem may depend on it (see [The kernel](#The%20kernel)).

jetpack-nixos only has NVIDIA's devkit description, so all three are the product's to carry. jetpack-nixos also follows NVIDIA's newer L4T releases (36.5.2 at the time of writing), while carrier vendors often publish files only for older ones. The vendor's changes then have to be re-applied to the newer NVIDIA files instead of copied: a device tree written for one kernel version can mismatch the drivers of another.

## The disk-unlock step

NixOS can open LUKS disks on its own (`boot.initrd.luks`). What it does not know is how to get the luks-srv passphrase, because NVIDIA's `init` script is not part of NixOS. A small systemd service in the NixOS initrd has to do what step 4 of [Why this encryption is weaker than it looks](09-a-default-jetson-setup-examined.md#Why%20this%20encryption%20is%20weaker%20than%20it%20looks) does:

- run `nvluks-srv-app` and pipe it into `cryptsetup`;
- then tell the TA to shut down;
- never write the passphrase anywhere.

That service is product code, and it is exactly the piece the attacker in [Why this encryption is weaker than it looks](09-a-default-jetson-setup-examined.md#Why%20this%20encryption%20is%20weaker%20than%20it%20looks) would replace. So it only becomes trustworthy together with a signed UKI (see [Signing every NixOS generation](#Signing%20every%20NixOS%20generation)).

The alternative is the fTPM (see [Measuring the boot with a TPM](06-measuring-the-boot-with-a-tpm.md)): NixOS's standard `systemd-cryptenroll` seals the key to "secure boot is on with the owner's keys" (PCR 7). It needs more provisioning work with per-device fuses.

## Signing every NixOS generation

On Ubuntu the kernel rarely changes. On NixOS every `nixos-rebuild switch` that touches the kernel, initrd or command line creates a new **generation**, and the boot menu keeps the old ones for rollback. With UEFI secure boot on, every one of those boot entries must be signed with the db key, or UEFI refuses it.

**Lanzaboote** automates this. On each switch it builds one UKI per generation (kernel + initrd + command line in one file), signs it, and writes it to the ESP. Two consequences:

- **It must work on aarch64.** Its build supports aarch64 but is "not tested in CI", so it is worth testing early.
- **The signing key has to be where the switch runs**, normally on the device (Lanzaboote keeps it in `/var/lib/sbctl`). That is fine against an *offline* attacker: the key sits on the encrypted root, which they cannot open. It is not a defence against someone who already has root on a running device. They could sign their own kernel, but they could also read everything anyway. The stricter alternative is to sign in CI and ship signed UKIs, which takes more work.

## Example: what a carrier vendor package changes

A carrier vendor usually ships `bootloader/`, `kernel/` and `rootfs/` folders that are copied over NVIDIA's BSP tree. It is easy to assume this only adds a device tree. As an example, Seeed's package for its A603 carrier (`a603-carrier-jp60-l4t36.3.zip`), compared file by file with NVIDIA's L4T r36.3 BSP, holds exactly 11 files:

| File in the archive                                                   | What it is                     | Compared with NVIDIA                                                      |
| --------------------------------------------------------------------- | ------------------------------ | ------------------------------------------------------------------------- |
| `bootloader/generic/BCT/tegra234-mb1-bct-pinmux-p3767-dp-a03.dtsi`    | MB1 pinmux                     | 19 pins changed ([The pinmux at power-on (MB1)](#The%20pinmux%20at%20power-on%20(MB1)))                       |
| `bootloader/tegra234-mb1-bct-gpio-p3767-dp-a03.dtsi`                  | MB1 GPIO directions            | 17 pins taken out of "input", 1 added ([The pinmux at power-on (MB1)](#The%20pinmux%20at%20power-on%20(MB1))) |
| `kernel/Image`                                                        | Linux kernel                   | **Different kernel**, Leetop build ([The kernel](#The%20kernel))                      |
| `kernel/dtb/…p3767-0001-nv.dtb`                                       | Device tree, Orin NX 8 GB      | 6 changes ([The device trees](#The%20device%20trees))                                         |
| `kernel/dtb/…p3767-0000-nv.dtb`                                       | Device tree, Orin NX 16 GB     | Same 6 + more ([The device trees](#The%20device%20trees))                                     |
| `kernel/dtb/…p3767-0003-nv.dtb`, `…-0004-nv.dtb`                      | Device trees, Orin Nano 8/4 GB | Same 6                                                                    |
| `kernel/dtb/…p3767-0000-dynamic.dtbo`                                 | Camera overlay                 | Re-pointed to the A603's single CSI connector                             |
| `rootfs/usr/lib/modules/…/iwlwifi/{iwlwifi,mvm/iwlmvm,dvm/iwldvm}.ko` | Intel Wi-Fi drivers            | Not in NVIDIA's BSP; built for the Leetop kernel                          |

That is all. No power-management (BPMP) firmware, no PMIC or voltage tables, no USB/PCIe lane settings, no board `.conf` file. So the firmware side of this carrier is only the two MB1 pinmux/GPIO files.

### The kernel

`kernel/Image` in the archive does not match NVIDIA's `nvidia-l4t-kernel` package:

```
NVIDIA  5fd072e2…  Linux version 5.15.136-tegra (buildbrain@mobile-u64-6367-d8000) … #1 SMP PREEMPT Mon May 6 09:56:39 PDT 2024
vendor  441f170c…  Linux version 5.15.136-tegra (leetop@leetop-kkkk)              … #2 SMP PREEMPT Wed May 15 18:05:48 CST 2024
```

Same version string, so NVIDIA's modules still load, but it was rebuilt by Leetop, the company behind the A603. Comparing its configuration with the one inside NVIDIA's Image:

| Option                                                  | NVIDIA  | Leetop                                 | What it is                                      |
| ------------------------------------------------------- | ------- | -------------------------------------- | ----------------------------------------------- |
| `USB_NET_QMI_WWAN`                                      | not set | built in                               | QMI data interface of cellular modems           |
| `USB_NET_CDC_MBIM`                                      | not set | built in                               | MBIM data interface of cellular modems          |
| `USB_WDM`                                               | not set | built in                               | control channel QMI/MBIM need (`/dev/cdc-wdm0`) |
| `USB_SERIAL`, `_OPTION`, `_WWAN`                        | module  | built in                               | the AT/serial ports of cellular modems          |
| `USB_USBNET`, `CDC_ETHER`, `CDC_NCM`, `AX88179_178A`, … | module  | built in                               | USB Ethernet adapters                           |
| `IWLWIFI`, `IWLMVM`, `IWLDVM`                           | not set | module (`.ko` added to `/lib/modules`) | Intel Wi-Fi cards                               |

**A cellular modem's data path (QMI/MBIM) only works with this kernel**: NVIDIA's stock kernel does not have those drivers at all. Leetop also built `usbserial` into the kernel, so NVIDIA's `usbserial.ko` module becomes a duplicate of built-in code.

### The pinmux at power-on (MB1)

Recall from [The carrier board port](#The%20carrier%20board%20port): each SoC pin can serve several functions, and MB1 chooses one before Linux starts. NVIDIA's devkit file leaves most 40-pin-header pins as "reserved" inputs with pull resistors. Seeed's file wires them to real functions:

| Pins                                               | NVIDIA devkit             | Seeed A603                                                    |
| -------------------------------------------------- | ------------------------- | ------------------------------------------------------------- |
| `PZ3`–`PZ7` (SPI1) and `PY0`–`PY3` (SPI3)          | reserved, input, tristate | **SPI**, driven, plus a drive-strength/voltage block for SPI3 |
| `PH7`, `PI0`–`PI2` (I2S2) and `PAC6` (audio clock) | reserved                  | **I²S audio**                                                 |
| `PG6`, `PH0`, `PN1`                                | reserved, input           | **plain GPIO**, driven (no pull)                              |
| `PM0` (DisplayPort hot-plug detect)                | DP function               | reserved, listed as a **GPIO input** in the GPIO file         |
| `PQ2`                                              | no pull                   | pull-down                                                     |

The GPIO file matches this: it removes the SPI, I²S and three GPIO pins from NVIDIA's "configure as input" list, and adds `PM0`. A product that uses one of these pins differently, for example as a plain GPIO, has to change both files again on top of the vendor's.

### The device trees

For the Orin NX 8 GB (`p3767-0001`), the A603 device tree differs from NVIDIA's in exactly six places:

1. a `GPIO06-high` gpio-hog (an always-high output) on the always-on GPIO controller;
2. a micro-USB connector node on `usb2-0`, with a VBUS detect GPIO;
3. the I²C bus at `0x31e0000` slowed from 400 kHz to 100 kHz;
4. SuperSpeed port `usb3-2` turned on (lane and port), with the hub controller listing it;
5. the USB2 companion of `usb3-1` and `usb3-2` both set to `usb2-2`;
6. `hdcp_enabled` on the display.

The 16 GB module's device tree (`p3767-0000`) has the same six. It also renames the board to "NVIDIA Jetson Orin NX leetop 603 Kit", removes the `fusb301` USB-C controller, and turns on an IMX219 camera on the CSI connector. So an 8 GB module on this carrier still reports "NVIDIA Jetson Orin NX Engineering Reference Developer Kit". **The model string tells the module size, not whether the carrier files were applied.** The `GPIO06-high` gpio-hog is a reliable check.

### What this means for NixOS

For this carrier, the port is small and fully known:

- **Firmware:** two MB1 files (19 pins in the pinmux + the GPIO list), plus any product-specific pins, re-applied to NVIDIA's 36.5.2 versions.
- **Device tree:** six changes, as a patch on NVIDIA's 36.5.2 source.
- **Kernel configuration:** see below.
- **Possibly not needed:** the camera overlay without a CSI camera, and Intel Wi-Fi without an Intel card.

So the carrier port ([The carrier board port](#The%20carrier%20board%20port)) includes a **kernel configuration**, not just device trees. jetpack-nixos builds NVIDIA's kernel from source with NVIDIA's defconfig plus NixOS's common options. Add the drivers the product needs, such as modem and USB network drivers (as modules is fine), and check the result in `config.boot.kernelPackages.kernel.configfile`.

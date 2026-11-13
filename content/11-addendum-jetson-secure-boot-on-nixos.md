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
3. **The kernel itself.** Drivers that are not built cannot be loaded. Some carrier vendors ship their own kernel build with extra drivers, and hardware on the carrier may depend on them. The product's kernel configuration then has to include those drivers.

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

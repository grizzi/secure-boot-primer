---
slug: sources
appendix: true
---
# Sources

NVIDIA Jetson Linux developer guide (r36):

- [Secure Boot](https://docs.nvidia.com/jetson/archives/r36.4.3/DeveloperGuide/SD/Security/SecureBoot.html): fuses, PKC/SBK, UEFI secure boot, enrollment at flash time
- [Disk Encryption](https://docs.nvidia.com/jetson/archives/r36.4.3/DeveloperGuide/SD/Security/DiskEncryption.html): luks-srv, ECID/UUID derivation, SRV_DOWN
- [OP-TEE](https://docs.nvidia.com/jetson/archives/r36.4.3/DeveloperGuide/SD/Security/OpTee.html): EKB, OEM_K1 → EKB_RK
- [Firmware TPM](https://docs.nvidia.com/jetson/archives/r36.4.3/DeveloperGuide/SD/Security/FirmwareTPM.html): KDK0, `odm_ekb_gen.py`, EPS
- [UEFI Adaptation (r36.5.2)](https://docs.nvidia.com/jetson/archives/r36.5.2/DeveloperGuide/SD/Bootloader/UEFI.html): boot menu, password, capsules

NVIDIA forums:

- [Fusing OemK1 for disk encryption](https://forums.developer.nvidia.com/t/fusing-oemk1-for-disk-encryption/314134)
- [BootSecurityInfo when burning OemK1 (2026-09)](https://forums.developer.nvidia.com/t/orin-nano-r36-4-4-exact-bootsecurityinfo-value-when-burning-oemk1-as-the-ekb-fuse-key/383804)
- [SecurityMode and signature enforcement](https://forums.developer.nvidia.com/t/does-not-burning-security-mode-keep-secure-boot-disable/337248)
- [Bricked module with custom EKB (2026-06)](https://forums.developer.nvidia.com/t/bricked-my-module-setting-up-a-custom-ekb/372455)
- [Soft secure boot on R36.5 (2026-06)](https://forums.developer.nvidia.com/t/jetpack-6-2-2-r36-5-soft-secure-boot-kernel-signature-rejected-by-uefi-both-sbsign-and-l4t-uefi-sign-image-sh/373804)

NixOS and jetpack-nixos:

- [jetpack-nixos](https://github.com/anduril/jetpack-nixos): `modules/flash-script.nix` (secure boot and UEFI key options), `modules/optee.nix` (fTPM, early-boot supplicant)
- [Lanzaboote](https://github.com/nix-community/lanzaboote) and the [NixOS wiki on Secure Boot](https://wiki.nixos.org/wiki/Secure_Boot)

General background:

- [OP-TEE documentation](https://optee.readthedocs.io/en/latest/general/about.html)
- [cryptsetup / LUKS](https://gitlab.com/cryptsetup/cryptsetup)
- [Arm TrustZone](https://developer.arm.com/documentation/102418/latest/)
- [systemd-cryptenroll](https://www.freedesktop.org/software/systemd/man/latest/systemd-cryptenroll.html)
- [MonocleSecurity: Secure boot and encrypted rootfs on Orin](https://medium.com/@monoclechris/secureboot-and-encrypted-rootfs-nvme-on-jetson-orin-41d3356d7922)

Images:

- Tegra X1 die photo: [Fritzchens Fritz, Wikimedia Commons](https://commons.wikimedia.org/wiki/File:NVIDIA@20nm@TegraX1@Erista@Shield_TV@S_Taiwan_1517A1_NPW020.M3W_TM670D-A1_dieshot_segments_(33260213216).jpg), CC0, numbered notes added.
- Orin NX photo: [4300streetcar, Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Nvidia_Jetson_Orin_NX_on_a_motherboard_Computex_2025.jpg), CC BY 4.0, annotations added. All other figures were drawn for this primer.
ghtop

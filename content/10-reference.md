---
slug: reference
appendix: true
---
# Reference

## Fuses on the Orin

NVIDIA groups the fuses into named fields. The full map is in NVIDIA's "Orin Fuse Specification" (an NDA document). The fields that matter for secure boot and disk encryption:

| Fuse                                   | What it holds                                       | Notes                                                                                               |
| -------------------------------------- | --------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| `PublicKeyHash`                        | Hash of the PKC **public** key                      | The BootROM compares the key in a signed image against this                                         |
| `SecureBootKey` (SBK)                  | AES key                                             | Bootloader images are encrypted with it, so firmware cannot be read from QSPI                       |
| `OemK1`, `OemK2`                       | 256-bit AES keys, readable only by the secure world | OP-TEE derives the EKB root key from OEM_K1                                                         |
| `KDK0`                                 | Per-device secret                                   | Needed for fTPM device identity                                                                     |
| `BootSecurityInfo`                     | Bit flags: auth type, "OEM key valid", …            | Bit 9 "OEM key valid" must be set or OP-TEE ignores the fused OEM_K1 (0x3E0 in a 2026 forum answer) |
| `SecurityMode` (`odm_production_mode`) | One bit: production mode                            | **Turns enforcement on and locks all further fuse writes**. Burn last                               |

Rules worth knowing before touching any of them:

- **Irreversible.** A wrong value cannot be undone. A module with a mismatched PKC hash, or with an EKB that no longer decrypts, can be bricked for good.
- **Order.** `odmfuse.sh` burns in file order and does not check dependencies. Put only the *new* fuses in the XML (a 2026 bricking case had placeholder values for an already-burned field).
- **Test first.** `odmfuse.sh --test` runs the checks without burning anything.
- **Staging.** NVIDIA staff say the BootROM does not enforce signatures until `OemKeyValid` *and* `SecurityMode` are burned. So you can burn the keys, check that signed flashing works, and only then burn `SecurityMode`.
- **After fusing**, every flash needs the keys (`-u pkc.pem -v sbk.key`), and NVIDIA does not allow single-partition updates of a fused board. Do a full flash, or a signed UEFI capsule update from the running OS.

**As shipped**, no fuse is burned and OP-TEE uses the default all-zero OEM_K1.

## Keys, one by one

| Key                                  | Type                                          | Lives where                                 | Private part held by             | If lost                                                      | If leaked                                            |
| ------------------------------------ | --------------------------------------------- | ------------------------------------------- | -------------------------------- | ------------------------------------------------------------ | ---------------------------------------------------- |
| **PKC**                              | RSA-3K or ECDSA P-256/P-521 key pair          | Public hash in fuses                        | Owner (flashing host / HSM)      | No fused device can be flashed or get firmware updates, ever | Attacker can sign firmware that every device accepts |
| **SBK**                              | AES key                                       | Fuses + owner                               | Owner                            | Same as PKC                                                  | Attacker can decrypt the firmware images             |
| **OEM_K1**                           | AES-256                                       | Fuses + owner (to build EKBs)               | Owner                            | Cannot build new EKBs for fused devices                      | Attacker can decrypt any EKB taken from a device     |
| **EKB** (encrypted key blob)         | Blob encrypted with a key derived from OEM_K1 | QSPI partition `A_eks`/`B_eks`              | n/a (it is ciphertext)           | Re-flash with a new one                                      | Harmless while OEM_K1 is secret                      |
| **sym2 / disk key** (inside the EKB) | AES-128                                       | Inside the EKB                              | Owner (at flash time)            | Recovery passphrase needed                                   | With the ECID, gives the disk passphrase             |
| **UEFI PK**                          | X.509 + RSA key                               | Public cert in UEFI variables               | Owner                            | Cannot change KEK/db (re-flash needed)                       | Attacker can replace the db and boot anything        |
| **UEFI KEK**                         | X.509 + RSA key                               | Same                                        | Owner                            | Cannot update db                                             | Attacker can add their key to db                     |
| **UEFI db**                          | X.509 + RSA key                               | Same                                        | Owner (signs every boot image)   | Cannot sign new kernels                                      | Attacker's kernels boot                              |
| **LUKS volume key**                  | Random 256/512-bit                            | In the LUKS header, wrapped by each keyslot | Nobody (generated on the device) | Data gone unless a keyslot opens                             | Disk readable                                        |

X.509 is the standard certificate format. RSA and ECDSA are the two common families of signature keys.

**ECID** is the chip's unique ID. It is not secret: `flash.sh` reads it over USB. It is used as a *context* value, so the same EKB key yields a different passphrase on every device.

**Custody** is the real decision. PKC, SBK and OEM_K1 are often one set for a whole fleet of devices. They need an offline backup, and ideally an HSM (a device that signs with a key without ever revealing it) or a cloud KMS, so that the signing step never sees the raw key. jetpack-nixos has a `preSignCommands` hook for exactly that.

## UEFI on the Jetson

- **UEFI variables** are stored in QSPI flash on the Orin NX. Linux shows them under `/sys/firmware/efi/efivars`.
- **The boot menu** opens with ESC during boot, on HDMI or on the serial console. It can change the boot order and device settings, and can be password protected (Device Manager → User Password Management).
- **Capsule update**: a signed firmware update that Linux drops in place and UEFI applies at the next boot. On Orin it goes to the inactive A/B slot and rolls back if the new firmware does not boot.
- **Enrolling keys at flash time.** NVIDIA lets you enroll the UEFI secure boot keys when flashing, through a device-tree overlay (`UefiDefaultSecurityKeys.dtbo`). Enrolled that way, secure boot "cannot be disabled unless you flash again". If keys are enrolled later from Linux, the UEFI menu's "Reset Secure Boot Keys" turns it off again. jetpack-nixos builds that overlay from the `firmware.uefi.secureBoot.default{Pk,Kek,Db}EslFile` options.
- **ESL** ("EFI Signature List") is just the certificate in UEFI's list format, made with `cert-to-efi-sig-list` from [efitools](https://git.kernel.org/pub/scm/linux/kernel/git/jejb/efitools.git).
- **Signing** an EFI binary for db is done with [`sbsign`](https://git.kernel.org/pub/scm/linux/kernel/git/jejb/sbsigntools.git). Making the keys is a few `openssl req -x509 -newkey rsa:2048 …` commands. The [NixOS wiki](https://wiki.nixos.org/wiki/Secure_Boot) and NVIDIA's Secure Boot page walk through it.
- **Lanzaboote** is the NixOS project that builds one signed UKI per NixOS generation and keeps the ESP tidy. It is systemd-boot plus a small signed stub. Version v1.2.0 came out 2026-09-26. aarch64 builds, but its flake marks aarch64 "best effort, not tested in CI". The fallback is NixOS's own UKI build (`systemd-stub`) signed by hand with `sbsign`.

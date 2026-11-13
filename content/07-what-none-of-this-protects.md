---
slug: what-none-of-this-protects
---
# What none of this protects

- **A running robot.** Someone who gets root remotely on a running robot finds the disk already open, and the volume key in kernel memory (see [Putting the two parts together](03-where-to-keep-the-disk-key.md#Putting%20the%20two%20parts%20together)). Secure boot and encryption protect a robot that is switched off or booting.
- **The keys themselves.** If the signing keys leak, an attacker can sign firmware that every robot accepts. If they are lost, fused robots can never be updated again. See [Keys, one by one](10-reference.md#Keys%2C%20one%20by%20one).
- **Mistakes in fuses.** Fuses cannot be undone, and a wrong value can make a module unbootable for good. See [Fuses on the Orin](10-reference.md#Fuses%20on%20the%20Orin).
- **Lost access.** If the TA, the EKB or the TPM stops working, the disk no longer opens by itself. Keep one extra LUKS keyslot with a long random passphrase stored offline.

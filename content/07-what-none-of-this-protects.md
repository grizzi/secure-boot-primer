---
slug: what-none-of-this-protects
---
# What none of this protects

- **A running robot.** Someone who gets root remotely on a running robot finds the disk already open, and the volume key in kernel memory (see [Putting the two parts together](03-where-to-keep-the-disk-key.md#Putting%20the%20two%20parts%20together)). Secure boot and encryption protect a robot that is switched off or booting.
- **The keys themselves.** If the signing keys leak, an attacker can sign firmware that every robot accepts. If they are lost, fused robots can never be updated again. See [Keys, one by one](10-reference.md#Keys%2C%20one%20by%20one).
- **Mistakes in fuses.** Fuses cannot be undone, and a wrong value can make a module unbootable for good. See [Fuses on the Orin](10-reference.md#Fuses%20on%20the%20Orin).
- **Lost access.** If the TA, the EKB or the TPM stops working, the disk no longer opens by itself. Keep one extra LUKS keyslot with a long random passphrase stored offline.

## Test your knowledge

> [!quiz]- An attacker gets root remotely on a running robot. What do they find?
> - [ ] An encrypted disk they cannot read
> - [x] The disk already open, and the volume key in kernel memory
> - [ ] Only the files in `/boot`
>
> Secure boot and disk encryption protect a robot that is switched off or booting, not one that is already running.

> [!quiz]- What happens if Hari loses the signing keys of robots whose fuses are burned?
> - [ ] He burns new keys into the fuses
> - [x] The robots can never be updated again
> - [ ] The robots stop booting at once
>
> The fuses keep the hash of the firmware key for good. Without the private key, no new firmware can be signed for those robots.

> [!quiz]- Why should Hari keep one extra LUKS keyslot with a long random passphrase stored offline?
> - [ ] So that the robot boots faster
> - [x] So that the disk can still be opened if the TA, the EKB or the TPM stops working
> - [ ] So that the TA can use it
>
> Without it, a failure of the part that releases the passphrase would leave the disk closed for good.

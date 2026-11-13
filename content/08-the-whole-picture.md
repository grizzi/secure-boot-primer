---
slug: the-whole-picture
---
# The whole picture

The first figure lists every key in this primer: what it does, where it is stored, and its Jetson name. The colour of each box shows where the key is stored. Fuses in the SoC are the only place on the robot where a secret key is stored in the clear.

![Every key: what it does, where it is stored, and its Jetson name](../assets/figures/keys-summary.svg)

The second figure follows the boot from power-on to the running system, in the same colours. For each stage it shows what the stage checks before starting the next one and what it does afterwards, which keys it uses and where they are stored, and the Jetson name.

![The boot, step by step: what runs, which keys it uses, and the Jetson names](../assets/figures/boot-sequence.svg)

Each stage is checked by the stage before it. An attacker who changes any piece, whether the firmware, the kernel, the initrd or the command line, either fails a signature check or, with fTPM sealing, gets a TPM that refuses to unseal. The EKB taken from QSPI is useless without OEM_K1, and OEM_K1 never leaves the fuses and the secure world.

## Test your knowledge

> [!quiz]- On the robot, where is a secret key stored in the clear?
> - [ ] In the flash chip
> - [ ] On the disk, in the LUKS header
> - [x] Only in fuses, and in memory while it is in use
>
> The flash chip and the disk hold only public keys or encrypted keys. Decrypted keys exist only in memory, while they are used.

> [!quiz]- Which keys never reach the robot?
> - [x] The private keys that sign the firmware and the boot files
> - [ ] The root key
> - [ ] The volume key
>
> They stay with Hari, offline or on the build server. The robot holds only the public parts.

> [!quiz]- Which keys reach Linux during a boot?
> - [ ] The root key and the disk key
> - [x] The disk passphrase and the volume key, only in memory
> - [ ] The private firmware key
>
> The root key and the disk key stay in the fuses and the secure world. Linux receives the passphrase once, and dm-crypt keeps the volume key in kernel memory.

---
slug: a-default-jetson-setup-examined
---
# A default Jetson setup, examined

## The default setup

A Jetson flashed with NVIDIA's disk encryption, but without fuses and without UEFI secure boot keys:

| Link                   | Default                                            | Consequence                                                               |
| ---------------------- | -------------------------------------------------- | ------------------------------------------------------------------------- |
| Bootloader secure boot | Off (unfused)                                      | USB recovery boots any image                                              |
| OEM_K1                 | Unfused, zero test key                             | The EKB decrypts with public tools                                        |
| UEFI secure boot       | Off, Setup Mode                                    | Any kernel/initrd boots                                                   |
| `/boot`                | Plain ext4 with `Image`, `initrd`, `extlinux.conf` | Editable from another computer or from a recovery-mode boot               |
| Disk                   | LUKS2, luks-srv passphrase                         | Safe against "pull the NVMe and mount it", not against editing the initrd |

Steps to break it, written down to show why secure boot matters, not as a recipe:

1. Take the NVMe out, or boot over USB recovery.
2. Add a line to `/boot/initrd` that copies the `nvluks-srv-app` output somewhere.
3. Boot once.

No soldering and no knowledge of Orin internals are needed. Fusing PKC + OEM_K1 + `SecurityMode` and turning on UEFI secure boot over signed UKIs closes this.

## Why this encryption is weaker than it looks

Follow one boot of such a Jetson and ask at each step who could have changed what runs.

1. **Power on.** The BootROM loads MB1 from QSPI. No fuses are burned, so it checks no signature. Anything in QSPI runs.

2. **MB2 starts OP-TEE.** OP-TEE decrypts the EKB with the *test* OEM key (all zeros), so the disk key `sym2` is now inside the secure world. So far so good: Linux cannot read it directly.

3. **UEFI starts L4TLauncher**, which reads `/boot/extlinux/extlinux.conf`. It then loads `/boot/Image` and `/boot/initrd` from the partition `APP`. That partition is **plain ext4**: not encrypted and not signed. UEFI secure boot is off (`SecureBoot=0`), so nothing checks these files.

4. **The initrd runs NVIDIA's `init` script**, which contains:

   ```
   nvluks-srv-app -u -c <disk-uuid> | cryptsetup luksOpen /dev/nvme0n1p2 crypt_root
   ```

   `nvluks-srv-app` asks the `luks-srv` TA for the passphrase and prints it to its standard output. The pipe hands it to `cryptsetup`. Near the end, the script runs `nvluks-srv-app -n`, which tells the TA to stop answering until the next reboot.

5. **The root filesystem is unlocked** and Ubuntu starts.

The secure world guards the key well. The weak point is step 4: **whoever controls the initrd controls who receives the passphrase.** The initrd sits on an unprotected partition. An attacker can do either of these:

- take the NVMe out, mount `APP` on any laptop, and add one line to the initrd's `init` that copies the passphrase somewhere (for example `| tee /boot/stolen | cryptsetup …`), then put the disk back and boot once;
- or leave the disk in place and boot the device over USB recovery mode with NVIDIA's own tools. With no fuses, the BootROM accepts any image, so the attacker brings their own initrd.

The `luks-srv` TA cannot tell the original initrd from a modified one: it simply answers the first caller after power-on (the figure in [Only signed software may run](04-only-signed-software-may-run.md)). An analogy is a safe whose combination is read out loud by a clerk to whoever stands at the counter first in the morning. The clerk is trustworthy, but the counter is not guarded.

**What fixes it.** Make sure the first caller is always the owner's code:

- **Bootloader secure boot** (fuses): QSPI firmware and USB recovery images must carry the owner's PKC signature. The attacker cannot bring their own firmware or recovery initrd.
- **UEFI secure boot** with a signed UKI: the kernel, initrd and command line are one file signed with the db key. A modified initrd fails the signature check and never runs.
- **Burned OEM_K1**: the EKB can no longer be decrypted outside the device, even if someone dumps QSPI.

With all three, "the first caller after power-on" can only be the signed initrd, and the clerk analogy holds again.

## Why burning OEM_K1 can fail

What is supposed to happen:

1. Burn a custom value into the `OemK1` fuse.
2. Build the EKB with `gen_ekb.py -oem_k1_key <the same value>`.
3. At boot, OP-TEE derives the EKB root key from the fused OEM_K1 and decrypts the EKB.

A failure reported on NVIDIA's forums: OP-TEE cannot decrypt the EKB and the device does not boot. The threads point at two causes:

- **The "OEM key valid" flag.** OP-TEE only uses the fused OEM_K1 when bit 9 of `BootSecurityInfo` says the OEM keys are valid. If OEM_K1 is burned but not that bit, OP-TEE keeps using the built-in test key. An EKB made with the real key no longer matches, and so does nothing else. A 2026 answer gives `0x3E0` as the value, burned together with OEM_K1.
- **Which fuse key opens the EKB.** NVIDIA staff wrote that on r36.3 the EKB was opened with OEM_K2, and from r36.4 on with OEM_K1 and OEM_K2.

A related trap: after fusing, NVIDIA's tools refuse to update a single partition such as `A_eks`. Every change needs a full flash with the keys. A quick "just re-flash the EKB" retry would therefore fail too, and look like the same problem.

The lesson: burn the fuses in stages on a spare module, with a serial console attached. Put `BootSecurityInfo` in the same fuse XML as `OemK1`, and run `odmfuse.sh --test` first. Signatures are only enforced once `SecurityMode` is burned (see [Fuses on the Orin](10-reference.md#Fuses%20on%20the%20Orin)), so a mistake in the *signed images* is still recoverable before that last step. A mismatch between the EKB and OEM_K1 is not, because OP-TEE depends on it from the moment OEM_K1 is valid.

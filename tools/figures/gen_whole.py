#!/usr/bin/env python3
"""Generates keys-summary.svg and boot-sequence.svg for 'The whole picture'."""
import sys
from xml.sax.saxutils import escape as e

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
W = 940

STYLE = """  <style>
    text { font-family: Inter, "Segoe UI", Helvetica, Arial, sans-serif; font-size: 14px; fill: #1e293b; }
    .t { font-weight: 600; }
    .h { font-weight: 600; font-size: 15px; }
    .s { font-size: 12px; fill: #475569; }
    .sd { font-size: 12px; fill: #1e293b; }
    .m { font-size: 13px; }
    .col { font-size: 11px; font-weight: 600; letter-spacing: 0.06em; fill: #64748b; }
    .mono { font-family: "JetBrains Mono", "DejaVu Sans Mono", Menlo, monospace; font-size: 11.5px; fill: #1e293b; }
    .vert { font-size: 12px; font-weight: 600; fill: #64748b; }
    rect { stroke-width: 1.3; }
    .bg { fill: #ffffff; stroke: #cbd5e1; stroke-width: 1.5; }
    .stage { fill: #ffffff; stroke: #475569; stroke-width: 1.5; }
    .jet { fill: #f8fafc; stroke: #cbd5e1; }
    .band { fill: #f1f5f9; stroke: none; }
    .fz { fill: #fbd99a; stroke: #b7791f; stroke-width: 1.6; }
    .fl { fill: #e3ecfd; stroke: #4a73b8; }
    .se { fill: #f1e6fc; stroke: #8e5bb5; }
    .li { fill: #fde8f1; stroke: #c2588f; }
    .dk { fill: #e3f2e4; stroke: #548c58; }
    .of { fill: #ffffff; stroke: #94a3b8; stroke-dasharray: 4 3; }
    .sep { stroke: #e2e8f0; stroke-width: 1; }
    .brk { stroke: #94a3b8; stroke-width: 1.5; fill: none; }
    .dash { stroke: #94a3b8; stroke-width: 1.2; stroke-dasharray: 5 4; }
    .ar { stroke: #475569; stroke-width: 1.6; fill: none; marker-end: url(#a); }
  </style>
  <defs>
    <marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">
      <path d="M0,0 L10,5 L0,10 z" fill="#475569"/>
    </marker>
  </defs>"""

# storage kinds: class, chip prefix, legend label
KIND = {
    "fz": ("Fuses", "Fuses in the SoC"),
    "fl": ("Flash", "Flash chip"),
    "se": ("Secure RAM", "Secure RAM (secure world)"),
    "li": ("Linux RAM", "Linux RAM"),
    "dk": ("Disk", "Disk"),
    "of": ("Off-robot", "Off the robot, with Sam"),
}
LEGEND_X = [96, 240, 344, 534, 640, 706]


def legend(y):
    out = [f'  <text class="sd t" x="24" y="{y+12}">Stored in:</text>']
    for (k, (_, label)), x in zip(KIND.items(), LEGEND_X):
        out.append(f'  <rect class="{k}" x="{x}" y="{y}" width="16" height="16" rx="3"/>')
        out.append(f'  <text class="sd" x="{x+22}" y="{y+12}">{e(label)}</text>')
    return out


def chip(x, y, w, kind, text):
    prefix = KIND[kind][0]
    return [f'  <rect class="{kind}" x="{x}" y="{y}" width="{w}" height="19" rx="4"/>',
            f'  <text class="sd" x="{x+8}" y="{y+13.5}"><tspan class="t">{e(prefix)}</tspan>  {e(text)}</text>']


def jet_lines(x, y, lines, step=16):
    """lines: list of str; a leading '`' renders the line in mono; '*' renders bold."""
    out = []
    for i, ln in enumerate(lines):
        cls = "sd t" if ln.startswith("*") else "mono" if ln.startswith("`") else "s"
        out.append(f'  <text class="{cls}" x="{x}" y="{y + i*step}">{e(ln.lstrip("*`"))}</text>')
    return out


# ---------------------------------------------------------------- keys summary
def keys_summary():
    C1, C2, C3 = 24, 356, 660
    CW2 = 288
    groups = [
        ("Keys that check software: signatures", [
            ("Firmware key", "signs the first boot programs, the secure-", "world image and UEFI",
             [("fz", "hash of the public key"), ("of", "private key")],
             ["*PKC key", "hash in the PublicKeyHash fuse"]),
            ("Firmware encryption key", "optional: keeps the firmware unreadable", "in the flash chip",
             [("fz", "the secret key"), ("of", "a copy, to encrypt firmware")],
             ["*SBK", "fuse"]),
            ("Owner key", "approves changes to the update keys,", "and to itself",
             [("fl", "public key, a UEFI variable"), ("of", "private key")],
             ["*PK", "UEFI variable in QSPI"]),
            ("Update keys", "approve changes to the allowed and", "forbidden lists",
             [("fl", "public keys, UEFI variables"), ("of", "private keys")],
             ["*KEK", "UEFI variable in QSPI"]),
            ("Release keys", "sign the boot loader, kernel, initrd", "and command line",
             [("fl", "public keys, in the allowed list"), ("of", "private keys, build server")],
             ["*keys in db", "sign the .sig files, or a UKI"]),
            ("Forbidden list", "hashes and keys that no longer count", "",
             [("fl", "a UEFI variable")],
             ["*dbx", "UEFI variable in QSPI"]),
        ]),
        ("Keys that protect the disk: encryption", [
            ("Root key", "burned once; decrypts the key blob,", "and never leaves the secure world",
             [("fz", "256-bit AES key, secure world only")],
             ["*OEM_K1", "fuse (OemK1 in the fuse file)"]),
            ("Key blob", "many keys, encrypted with a key", "derived from the root key",
             [("fl", "encrypted"), ("se", "decrypted at boot")],
             ["*EKB", "`A_eks, B_eks; opened by", "`jetson_user_key_pta"]),
            ("Disk key", "one key from the key blob", "",
             [("se", "never leaves the secure world")],
             ["*sym2", "a key in the EKB"]),
            ("Disk passphrase", "derived from the disk key, the chip ID", "and the partition ID",
             [("se", "computed by the TA"), ("li", "briefly, in the initrd")],
             ["*luks-srv TA output", "fetched by nvluks-srv-app"]),
            ("Volume key", "encrypts the data on the disk", "",
             [("dk", "locked in the LUKS keyslots"), ("li", "in the kernel, while open")],
             ["*LUKS volume key", "cryptsetup luksOpen, dm-crypt"]),
        ]),
    ]
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} HEIGHT" width="{W}" height="HEIGHT">', STYLE,
           '  <rect class="bg" x="0.75" y="0.75" width="938.5" height="HEIGHT_BG" rx="12"/>',
           '  <text class="h" x="24" y="34">Every key: what it does, where it is stored, and its Jetson name</text>']
    out += legend(50)
    y = 98
    out += [f'  <text class="col" x="{C1}" y="{y}">KEY</text>',
            f'  <text class="col" x="{C2}" y="{y}">STORED</text>',
            f'  <text class="col" x="{C3}" y="{y}">ON THE JETSON</text>']
    y += 10
    RH = 50
    for title, rows in groups:
        out.append(f'  <rect class="band" x="16" y="{y}" width="{W-32}" height="24" rx="5"/>')
        out.append(f'  <text class="t m" x="{C1}" y="{y+17}">{e(title)}</text>')
        y += 28
        for i, (name, d1, d2, chips, jet) in enumerate(rows):
            if i:
                out.append(f'  <line class="sep" x1="{C1}" y1="{y}" x2="{W-24}" y2="{y}"/>')
            out.append(f'  <text class="t m" x="{C1}" y="{y+19}">{e(name)}</text>')
            out.append(f'  <text class="s" x="{C1}" y="{y+35}">{e(d1)}</text>')
            if d2:
                # second description line continues to the right of the first? keep below
                pass
            rh = RH + (14 if d2 else 0)
            n = len(chips)
            cy = y + (rh - (n * 19 + (n - 1) * 5)) / 2
            for k, txt in chips:
                out += chip(C2, cy, CW2, k, txt)
                cy += 24
            out += jet_lines(C3, y + (rh - (len(jet) - 1) * 15) / 2 + 4, jet, 15)
            if d2:
                out.append(f'  <text class="s" x="{C1}" y="{y+49}">{e(d2)}</text>')
            y += RH + (14 if d2 else 0)
        y += 8
    # footer
    y += 4
    out.append(f'  <text class="m" x="24" y="{y+14}">On the robot, secret keys are stored in the clear only in fuses. The flash chip and the disk</text>')
    out.append(f'  <text class="m" x="24" y="{y+32}">hold public keys or encrypted keys; decrypted keys exist only in memory, while they are used.</text>')
    out.append(f'  <text class="s" x="24" y="{y+52}">With a TPM in place of the TA, the disk passphrase is sealed in the TPM instead (on the Jetson: the fTPM).</text>')
    h = y + 70
    out.append('</svg>')
    s = "\n".join(out).replace("HEIGHT_BG", f"{h-1.5}").replace("HEIGHT", str(h))
    open(f"{OUT}/keys-summary.svg", "w").write(s + "\n")


# ---------------------------------------------------------------- boot sequence
def boot_sequence():
    C1, C1W = 60, 344
    C2, C2W = 418, 262
    C3, C3W = 692, 224
    rows = [
        # title, subtitle, lines (label, text), chips, jetson lines, world
        ("BootROM", "in mask ROM, the first code to run",
         [("checks:", "the first boot programs, with the firmware key"),
          ("then:", "decrypts them if encrypted, and starts them")],
         [("fz", "hash of the firmware key"), ("fz", "firmware encryption key, optional")],
         ["*BootROM", "checks MB1 against PublicKeyHash", "decrypts with the SBK, if burned"], "s"),
        ("First boot programs", "from the flash chip",
         [("checks:", "the secure-world image and UEFI (firmware key)"),
          ("then:", "set up the gates, load the secure-world image")],
         [("fz", "hash of the firmware key, as above")],
         ["*MB1, MB2", "in QSPI, signed with the PKC key", "load ATF + OP-TEE into TZDRAM"], "s"),
        ("Secure world", "ATF and OP-TEE, in secure memory",
         [("checks:", "nothing, the stage before checked it"),
          ("then:", "decrypts the key blob with a key derived"),
          ("", "from the root key; the keys stay inside")],
         [("fz", "root key, secure world only"), ("fl", "key blob, encrypted"),
          ("se", "decrypted keys, with the disk key")],
         ["*OP-TEE", "`jetson_user_key_pta opens", "the EKB with keys from OEM_K1", "disk key: sym2"], "s"),
        ("UEFI firmware", "from the flash chip",
         [("checks:", "the boot loader, against the allowed list"),
          ("then:", "starts it (with a TPM: records PCR 7)")],
         [("fl", "owner key, update keys"), ("fl", "allowed and forbidden lists")],
         ["*NVIDIA UEFI (EDK2)", "PK, KEK, db, dbx:", "UEFI variables in QSPI"], "n"),
        ("Boot loader", "from the disk",
         [("checks:", "kernel, initrd, command line (allowed list)"),
          ("then:", "starts the kernel with the initrd")],
         [("fl", "allowed list, the release keys"), ("dk", "signatures, or one signed UKI")],
         ["*L4TLauncher", ".sig files next to Image, initrd", "and extlinux.conf, in /boot"], "n"),
        ("initrd", "asks the TA for the disk passphrase",
         [("checks:", "nothing, the TA answers whoever asks"),
          ("", "(with a TPM: PCR 7 and PCR 15 must match)"),
          ("then:", "the TA derives the passphrase, hands it"),
          ("", "over, and stops answering")],
         [("se", "disk key, chip ID, partition ID"), ("li", "disk passphrase, briefly")],
         ["*nvluks-srv-app, luks-srv TA", "KDF over sym2, ECID and the", "partition UUID; then", "`nvluks-srv-app -n"], "n"),
        ("initrd", "opens the disk",
         [("checks:", "the passphrase, against a keyslot"),
          ("then:", "gives the volume key to dm-crypt, switches root")],
         [("dk", "volume key, locked in the keyslots"), ("li", "volume key, in the kernel")],
         ["*cryptsetup luksOpen", "`nvme0n1p2 → /dev/mapper/", "`crypt_root"], "n"),
        ("Running system", "from the decrypted root filesystem",
         [("", "dm-crypt decrypts every read, encrypts every write")],
         [("li", "volume key, until power-off")],
         ["*root filesystem", "`/dev/mapper/crypt_root"], "n"),
    ]
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} HEIGHT" width="{W}" height="HEIGHT">', STYLE,
           '  <rect class="bg" x="0.75" y="0.75" width="938.5" height="HEIGHT_BG" rx="12"/>',
           '  <text class="h" x="24" y="34">The boot, step by step: what runs, which keys it uses, and the Jetson names</text>']
    out += legend(50)
    y = 98
    out += [f'  <text class="col" x="{C1}" y="{y}">WHAT RUNS, IN BOOT ORDER</text>',
            f'  <text class="col" x="{C2}" y="{y}">KEYS AND WHERE THEY ARE STORED</text>',
            f'  <text class="col" x="{C3}" y="{y}">ON THE JETSON</text>']
    y = 112
    world_spans = {"s": [None, None], "n": [None, None]}
    prev_bottom = None
    prev_world = None
    for title, sub, lines, chips, jet, world in rows:
        nlines = 1 + len(lines)
        h = 14 + nlines * 16 + 6
        h = max(h, 14 + len(jet) * 15 + 4, 10 + len(chips) * 24)
        if prev_world and world != prev_world:
            # world switch
            y += 14
            out.append(f'  <line class="dash" x1="{C1-4}" y1="{y-7}" x2="{W-24}" y2="{y-7}"/>')
            out.append(f'  <text class="s" x="{C2}" y="{y-12}">the processor switches to the normal world</text>')
        if prev_bottom is not None:
            out.append(f'  <path class="ar" d="M{C1+24},{prev_bottom} V{y-1}"/>')
        if world_spans[world][0] is None:
            world_spans[world][0] = y
        world_spans[world][1] = y + h
        out.append(f'  <rect class="stage" x="{C1}" y="{y}" width="{C1W}" height="{h}" rx="6"/>')
        out.append(f'  <text class="t m" x="{C1+12}" y="{y+19}">{e(title)}<tspan class="s" font-weight="400">  {e(sub)}</tspan></text>')
        ty = y + 37
        for lab, txt in lines:
            if lab:
                out.append(f'  <text class="sd" x="{C1+12}" y="{ty}"><tspan class="t">{e(lab)}</tspan> {e(txt)}</text>')
            else:
                indent = 0 if len(lines) == 1 else 0
                out.append(f'  <text class="sd" x="{C1+12+indent}" y="{ty}">{e(txt)}</text>')
            ty += 16
        n = len(chips)
        cy = y + (h - (n * 19 + (n - 1) * 5)) / 2
        for k, txt in chips:
            out += chip(C2, cy, C2W, k, txt)
            cy += 24
        out.append(f'  <rect class="jet" x="{C3}" y="{y}" width="{C3W}" height="{h}" rx="6"/>')
        jy = y + (h - (len(jet) - 1) * 15) / 2 + 4
        out += jet_lines(C3 + 12, jy, jet, 15)
        prev_bottom = y + h
        prev_world = world
        y += h + 16
    # world brackets
    for w, label in (("s", "secure world"), ("n", "normal world")):
        a, b = world_spans[w]
        out.append(f'  <path class="brk" d="M48,{a} H42 V{b} H48"/>')
        mid = (a + b) / 2
        out.append(f'  <text class="vert" x="30" y="{mid}" text-anchor="middle" transform="rotate(-90 30 {mid})">{label}</text>')
    y += 0
    out.append(f'  <text class="m" x="24" y="{y+10}">Each stage checks the next one before starting it. Fuses hold the only secret keys stored in the clear;</text>')
    out.append(f'  <text class="m" x="24" y="{y+28}">decrypted keys exist only in memory, and only the passphrase and the volume key ever reach Linux.</text>')
    h = y + 46
    out.append('</svg>')
    s = "\n".join(out).replace("HEIGHT_BG", f"{h-1.5}").replace("HEIGHT", str(h))
    open(f"{OUT}/boot-sequence.svg", "w").write(s + "\n")


keys_summary()
boot_sequence()

"""Generate the end-to-end boot figures, one per step of the story, with a shared layout.

Usage: python3 -I gen_e2e.py OUT_DIR
"""
import sys
from pathlib import Path

W, H = 940, 400
STYLE = """
    text { font-family: Inter, "Segoe UI", Helvetica, Arial, sans-serif; font-size: 14px; fill: #1e293b; }
    .t { font-weight: 600; }
    .h { font-weight: 600; font-size: 15px; }
    .s { font-size: 12px; fill: #475569; }
    .c { text-anchor: middle; }
    .red { fill: #b42318; }
    .green { fill: #2f6b33; }
    rect { stroke-width: 1.5; }
    .bg { fill: #ffffff; stroke: #cbd5e1; }
    .hw { fill: #eef2f6; stroke: #64748b; }
    .fw { fill: #e8f0fe; stroke: #4a73b8; }
    .os { fill: #e8f5e9; stroke: #548c58; }
    .sec { fill: #f3e8ff; stroke: #9160b8; }
    .key { fill: #fff4e0; stroke: #c98a1b; }
    .w { fill: #ffffff; stroke: #64748b; }
    .bad { fill: #fdecea; stroke: #c0392b; }
    .ok { fill: #e8f5e9; stroke: #548c58; }
    .new { stroke: #c98a1b; stroke-width: 3; }
    .ar { stroke: #475569; stroke-width: 1.6; fill: none; marker-end: url(#a); }
    .lbl { font-size: 12px; fill: #334155; }
"""
DEFS = """
  <defs>
    <marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">
      <path d="M0,0 L10,5 L0,10 z" fill="#475569"/>
    </marker>
  </defs>"""

BADGE = {
    "no": ("#fdecea", "#c0392b", "✗"),
    "ok": ("#e8f5e9", "#548c58", "✓"),
    "m": ("#fff4e0", "#c98a1b", "M"),
}


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def figure(spec):
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
           f"  <style>{STYLE}  </style>", DEFS,
           f'  <rect class="bg" x="0.75" y="0.75" width="{W - 1.5}" height="{H - 1.5}" rx="12"/>',
           f'  <text class="h" x="24" y="34">{esc(spec["title"])}</text>']
    # legend
    lx = W - 24
    legend = spec.get("legend", [("ok", "signature checked"), ("no", "no check")])
    for kind, text in reversed(legend):
        tw = len(text) * 6.7
        tx = lx - tw
        out.append(f'  <text class="s" x="{tx:.0f}" y="34">{esc(text)}</text>')
        cx = tx - 13
        fill, stroke, glyph = BADGE[kind]
        out.append(f'  <circle cx="{cx:.0f}" cy="30" r="8" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>')
        out.append(f'  <text class="c t" x="{cx:.0f}" y="34" style="font-size:11px;fill:{stroke}">{glyph}</text>')
        lx = cx - 8 - 20

    # stage row
    stages = spec["stages"]
    n = len(stages)
    gap, first_w = 40, 70
    w = (W - 48 - first_w - gap * (n - 1)) / (n - 1)
    xs, widths = [], []
    x = 24
    for i in range(n):
        ww = first_w if i == 0 else w
        xs.append(x)
        widths.append(ww)
        x += ww + gap
    y0, hh = 56, 60
    centers = []
    for i, st in enumerate(stages):
        label, sub, cls = st[0], st[1], st[2]
        new = len(st) > 3 and st[3]
        cx = xs[i] + widths[i] / 2
        centers.append(cx)
        extra = " new" if new else ""
        out.append(f'  <rect class="{cls}{extra}" x="{xs[i]:.1f}" y="{y0}" width="{widths[i]:.1f}" height="{hh}" rx="6"/>')
        fs = 14 if n <= 5 or len(label) < 14 else 13
        if sub:
            out.append(f'  <text class="c t" x="{cx:.1f}" y="{y0 + 26}" style="font-size:{fs}px">{esc(label)}</text>')
            out.append(f'  <text class="c s" x="{cx:.1f}" y="{y0 + 45}">{esc(sub)}</text>')
        else:
            out.append(f'  <text class="c t" x="{cx:.1f}" y="{y0 + 35}" style="font-size:{fs}px">{esc(label)}</text>')
    # arrows with badges
    for i, kind in enumerate(spec["edges"]):
        x1, x2 = xs[i] + widths[i], xs[i + 1]
        ym = y0 + hh / 2
        out.append(f'  <path class="ar" d="M{x1:.1f},{ym} H{x2 - 2:.1f}"/>')
        if kind:
            fill, stroke, glyph = BADGE[kind]
            bx = (x1 + x2) / 2
            out.append(f'  <circle cx="{bx:.1f}" cy="{ym - 15}" r="9" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>')
            out.append(f'  <text class="c t" x="{bx:.1f}" y="{ym - 11}" style="font-size:11px;fill:{stroke}">{glyph}</text>')
    # notes under stages
    for i, (text, cls) in spec.get("stage_notes", {}).items():
        out.append(f'  <text class="c {cls}" x="{centers[i]:.1f}" y="{y0 + hh + 18}" style="font-size:12px">{esc(text)}</text>')

    # unlock lane
    ki = spec["kernel_index"]
    ri = n - 1
    ly = 172
    src = spec["source"]
    sx, sw = 24, centers[ki] - 150 - 24 - 60
    out.append(f'  <rect class="{src["cls"]}{" new" if src.get("new") else ""}" x="{sx}" y="{ly}" width="{sw:.1f}" height="72" rx="6"/>')
    out.append(f'  <text class="t" x="{sx + 14}" y="{ly + 24}">{esc(src["title"])}</text>')
    for j, line in enumerate(src["lines"]):
        cls = "s red" if line.startswith("!") else "s"
        out.append(f'  <text class="{cls}" x="{sx + 14}" y="{ly + 44 + 16 * j}">{esc(line.lstrip("!"))}</text>')
    cx0 = centers[ki] - 110
    out.append(f'  <rect class="w" x="{cx0:.1f}" y="{ly}" width="220" height="72" rx="6"/>')
    out.append(f'  <text class="c t" x="{centers[ki]:.1f}" y="{ly + 26}">cryptsetup luksOpen</text>')
    out.append(f'  <text class="c s" x="{centers[ki]:.1f}" y="{ly + 46}">run by the initrd</text>')
    out.append(f'  <text class="c s" x="{centers[ki]:.1f}" y="{ly + 62}">passphrase → keyslot → volume key</text>')
    out.append(f'  <path class="ar" d="M{sx + sw:.1f},{ly + 36} H{cx0 - 2:.1f}"/>')
    out.append(f'  <text class="lbl c" x="{(sx + sw + cx0) / 2:.1f}" y="{ly + 28}">passphrase</text>')
    # initrd -> cryptsetup, cryptsetup -> root
    out.append(f'  <path class="ar" d="M{centers[ki]:.1f},{y0 + hh} V{ly - 2}"/>')
    rx = centers[ri]
    out.append(f'  <path class="ar" d="M{cx0 + 220:.1f},{ly + 36} H{rx:.1f} V{y0 + hh + 2}"/>')
    out.append(f'  <text class="lbl" x="{rx + 8:.1f}" y="{ly - 10}">opens</text>')

    # scoreboard
    sy = 278
    out.append(f'  <text class="t" x="24" y="{sy}">With this design:</text>')
    chips = spec["score"]
    cw = (W - 48 - 3 * 12) / 4
    for j, (title, ok, status) in enumerate(chips):
        x = 24 + j * (cw + 12)
        cls = "ok" if ok else "bad"
        glyph = "✓" if ok else "✗"
        col = "green" if ok else "red"
        out.append(f'  <rect class="{cls}" x="{x:.1f}" y="{sy + 12}" width="{cw:.1f}" height="64" rx="6"/>')
        out.append(f'  <text class="t {col}" x="{x + 12:.1f}" y="{sy + 40}" style="font-size:18px">{glyph}</text>')
        out.append(f'  <text class="t" x="{x + 34:.1f}" y="{sy + 37}">{esc(title)}</text>')
        out.append(f'  <text class="s" x="{x + 34:.1f}" y="{sy + 57}">{esc(status)}</text>')
    if spec.get("footer"):
        out.append(f'  <text x="24" y="{H - 16}" style="font-size:13px">{esc(spec["footer"])}</text>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


BASE5 = lambda fw_note=None: [  # noqa: E731
    ("Power on", None, "hw"),
    ("Firmware", "in flash", "fw"),
    ("Boot loader", "on /boot", "os"),
    ("Kernel + initrd", "on /boot", "os"),
    ("Root filesystem", "LUKS, encrypted", "os"),
]

ATTACKS = ["Disk read on a laptop", "Automatic boot", "Edited /boot", "Replaced firmware"]

SPECS = {
    "e2e-1-encryption": dict(
        title="With disk encryption: the root filesystem is encrypted",
        stages=[("Power on", None, "hw"), ("Firmware", "in flash", "fw"), ("Boot loader", "on /boot", "os"),
                ("Kernel + initrd", "on /boot, plain", "os"), ("Root filesystem", "LUKS, encrypted", "os", True)],
        edges=["no", "no", "no", None], kernel_index=3,
        stage_notes={2: ("cannot be encrypted", "red"), 3: ("cannot be encrypted", "red")},
        source=dict(cls="w", title="A person", lines=["types the passphrase", "at every boot"]),
        score=[(ATTACKS[0], True, "stopped"), (ATTACKS[1], False, "needs a person"),
               (ATTACKS[2], False, "still works"), (ATTACKS[3], False, "still works")],
        footer="An edited initrd can also record the passphrase the person types.",
    ),
    "e2e-2-secure-world": dict(
        title="With the key in the secure world: the TA supplies the passphrase",
        stages=[("Power on", None, "hw"), ("Firmware", "in flash", "fw"), ("Boot loader", "on /boot", "os"),
                ("Kernel + initrd", "on /boot, plain", "os"), ("Root filesystem", "LUKS, encrypted", "os")],
        edges=["no", "no", "no", None], kernel_index=3,
        source=dict(cls="sec", new=True, title="luks-srv TA (secure world)",
                    lines=["derives it from a key the fuses protect", "!answers the first program that asks"]),
        score=[(ATTACKS[0], True, "stopped"), (ATTACKS[1], True, "works"),
               (ATTACKS[2], False, "still works"), (ATTACKS[3], False, "still works")],
        footer="Any initrd can ask the TA, including one the thief edited.",
    ),
    "e2e-3-signed-boot": dict(
        title="With signed boot software: the firmware checks what it loads",
        stages=[("Power on", None, "hw"), ("Firmware", "UEFI, in flash", "fw"), ("Boot loader", "signed", "os", True),
                ("Kernel + initrd", "signed (UKI)", "os", True), ("Root filesystem", "LUKS, encrypted", "os")],
        edges=["no", "ok", "ok", None], kernel_index=3,
        stage_notes={1: ("can be replaced", "red")},
        source=dict(cls="sec", title="luks-srv TA (secure world)",
                    lines=["derives it from a key the fuses protect", "answers the first program that asks"]),
        score=[(ATTACKS[0], True, "stopped"), (ATTACKS[1], True, "works"),
               (ATTACKS[2], True, "stopped: bad signature"), (ATTACKS[3], False, "still works")],
        footer="Firmware that checks nothing, loaded over USB recovery, skips every check.",
    ),
    "e2e-4-chain-of-trust": dict(
        title="With a chain of trust: the checks start in the SoC's ROM",
        stages=[("Power on", None, "hw"), ("BootROM", "in the SoC", "hw", True), ("Firmware", "signed", "fw", True),
                ("Boot loader", "signed", "os"), ("Kernel + initrd", "signed (UKI)", "os"),
                ("Root filesystem", "LUKS, encrypted", "os")],
        edges=[None, "ok", "ok", "ok", None], kernel_index=4,
        stage_notes={1: ("key hash in fuses", "s")},
        source=dict(cls="sec", title="luks-srv TA (secure world)",
                    lines=["derives it from a key the fuses protect", "!answers even if secure boot is off"]),
        score=[(ATTACKS[0], True, "stopped"), (ATTACKS[1], True, "works"),
               (ATTACKS[2], True, "stopped: bad signature"), (ATTACKS[3], True, "stopped: bad signature")],
        footer="Every program is checked, but the TA does not check that secure boot is still switched on.",
    ),
    "e2e-5-tpm": dict(
        title="With a TPM: the key is released only for the expected boot",
        legend=[("ok", "signature checked")],
        stages=[("Power on", None, "hw"), ("BootROM", "in the SoC", "hw"), ("Firmware", "signed", "fw"),
                ("Boot loader", "signed", "os"), ("Kernel + initrd", "signed (UKI)", "os"),
                ("Root filesystem", "LUKS, encrypted", "os")],
        edges=[None, "ok", "ok", "ok", None], kernel_index=4,
        stage_notes={2: ("records PCR 7", "s")},
        source=dict(cls="key", new=True, title="TPM (fTPM on the Jetson)",
                    lines=["unseals the key only if PCR 7 shows", "secure boot on, with Hari's keys"]),
        score=[(ATTACKS[0], True, "stopped"), (ATTACKS[1], True, "works"),
               (ATTACKS[2], True, "stopped: bad signature"), (ATTACKS[3], True, "stopped: bad signature")],
        footer="Secure boot switched off, or other keys installed: PCR 7 differs, and the TPM keeps the key.",
    ),
}

if __name__ == "__main__":
    out_dir = Path(sys.argv[1])
    for name, spec in SPECS.items():
        (out_dir / f"{name}.svg").write_text(figure(spec), encoding="utf-8")
        print(out_dir / f"{name}.svg")

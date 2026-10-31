#!/usr/bin/env python3
"""Generate Windows/App/CharsetTable.inc from OpenKey's _codeTable.

Source of truth: OpenKey's engine/Vietnamese.cpp `_codeTable[]`
  [0] = Unicode, [1] = TCVN3 (ABC), [2] = VNI Windows.
Every entry is cross-checked against Unikey's own tables in
fcitx5-unikey/unikey/data.cpp (SingleByteTables TCVN3, DoubleByteTables VNI-WIN):
for each Unicode char, the TCVN3 byte and VNI byte sequence must match exactly.

Usage:
  python3 Tools/gen_charset_table.py \
      --openkey /tmp/openkey/Sources/OpenKey/engine/Vietnamese.cpp \
      --unikey  /tmp/fcitx5-unikey/unikey/data.cpp \
      --out Windows/App/CharsetTable.inc
"""
import argparse
import re
import sys

# Standard Vietnamese char order used by Unikey's Single/DoubleByteTables
# (see fcitx5-unikey/unikey/data.cpp comments + ukengine writeOutput):
# per vowel group: BASE_UPPER, base_lower, then 5 tones x (UPPER, lower).
def _vowel(base_u, base_l, tones):
    seq = [base_u, base_l]
    for tu, tl in tones:
        seq += [tu, tl]
    return seq

_TONES_A = [("Á", "á"), ("À", "à"), ("Ả", "ả"), ("Ã", "ã"), ("Ạ", "ạ")]
STD_ORDER = []
STD_ORDER += _vowel("A", "a", _TONES_A)
STD_ORDER += _vowel("Â", "â", [("Ấ", "ấ"), ("Ầ", "ầ"), ("Ẩ", "ẩ"), ("Ẫ", "ẫ"), ("Ậ", "ậ")])
STD_ORDER += _vowel("Ă", "ă", [("Ắ", "ắ"), ("Ằ", "ằ"), ("Ẳ", "ẳ"), ("Ẵ", "ẵ"), ("Ặ", "ặ")])
STD_ORDER += ["B", "b", "C", "c", "D", "d", "Đ", "đ"]
STD_ORDER += _vowel("E", "e", [("É", "é"), ("È", "è"), ("Ẻ", "ẻ"), ("Ẽ", "ẽ"), ("Ẹ", "ẹ")])
STD_ORDER += _vowel("Ê", "ê", [("Ế", "ế"), ("Ề", "ề"), ("Ể", "ể"), ("Ễ", "ễ"), ("Ệ", "ệ")])
STD_ORDER += ["F", "f", "G", "g", "H", "h"]
STD_ORDER += _vowel("I", "i", [("Í", "í"), ("Ì", "ì"), ("Ỉ", "ỉ"), ("Ĩ", "ĩ"), ("Ị", "ị")])
STD_ORDER += ["J", "j", "K", "k", "L", "l", "M", "m", "N", "n"]
STD_ORDER += _vowel("O", "o", [("Ó", "ó"), ("Ò", "ò"), ("Ỏ", "ỏ"), ("Õ", "õ"), ("Ọ", "ọ")])
STD_ORDER += _vowel("Ô", "ô", [("Ố", "ố"), ("Ồ", "ồ"), ("Ổ", "ổ"), ("Ỗ", "ỗ"), ("Ộ", "ộ")])
STD_ORDER += _vowel("Ơ", "ơ", [("Ớ", "ớ"), ("Ờ", "ờ"), ("Ở", "ở"), ("Ỡ", "ỡ"), ("Ợ", "ợ")])
STD_ORDER += ["P", "p", "Q", "q", "R", "r", "S", "s", "T", "t"]
STD_ORDER += _vowel("U", "u", [("Ú", "ú"), ("Ù", "ù"), ("Ủ", "ủ"), ("Ũ", "ũ"), ("Ụ", "ụ")])
STD_ORDER += _vowel("Ư", "ư", [("Ứ", "ứ"), ("Ừ", "ừ"), ("Ử", "ử"), ("Ữ", "ữ"), ("Ự", "ự")])
STD_ORDER += ["V", "v", "W", "w", "X", "x"]
STD_ORDER += _vowel("Y", "y", [("Ý", "ý"), ("Ỳ", "ỳ"), ("Ỷ", "ỷ"), ("Ỹ", "ỹ"), ("Ỵ", "ỵ")])
STD_ORDER += ["Z", "z"]
assert len(STD_ORDER) == 186, len(STD_ORDER)  # 12 vowel groups x 12 + 42 consonants


def _strip_noise(src):
    # remove // and /* */ comments and string/char literals so brace matching is reliable
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    src = re.sub(r"//[^\n]*", "", src)
    src = re.sub(r"'(?:\\.|[^'\\])*'", "''", src)
    src = re.sub(r'"(?:\\.|[^"\\])*"', '""', src)
    return src


def parse_openkey_tables(path):
    src = _strip_noise(open(path, encoding="utf-8").read())
    m = re.search(r"map<Uint32, vector<Uint16>> _codeTable\[\] = \{", src)
    assert m, "cannot find _codeTable"
    # crude brace matching from the opening brace
    i = src.index("{", m.start())
    depth = 0
    tables = []
    start = None
    for j in range(i, len(src)):
        c = src[j]
        if c == "{":
            depth += 1
            if depth == 2:
                start = j  # start of one charset block
        elif c == "}":
            depth -= 1
            if depth == 1:
                tables.append(src[start:j + 1])
            if depth == 0:
                break
    assert len(tables) >= 3, f"expected >=3 charset blocks, got {len(tables)}"
    out = []
    for t in tables[:3]:
        rows = []
        for rm in re.finditer(r"\{\s*[A-Z_]+\s*(?:\|[A-Z_]+\s*)?,\s*\{([^}]*)\}\s*\}", t):
            vals = [int(x, 16) for x in re.findall(r"0[xX][0-9a-fA-F]+", rm.group(1))]
            rows.append(vals)
        out.append(rows)
    # row alignment across the 3 tables
    assert len(out[0]) == len(out[1]) == len(out[2]), (
        len(out[0]), len(out[1]), len(out[2]))
    for r in range(len(out[0])):
        assert len(out[0][r]) == len(out[1][r]) == len(out[2][r]), (r,)
    return out[0], out[1], out[2]


def parse_unikey_data(path):
    src = open(path, encoding="utf-8").read()

    def section(name):
        m = re.search(r"// " + re.escape(name) + r"\n\s*\{\{?", src)
        assert m, f"cannot find {name}"
        i = src.index("{", m.start())
        depth = 0
        for j in range(i, len(src)):
            if src[j] == "{":
                depth += 1
            elif src[j] == "}":
                depth -= 1
                if depth == 0:
                    return src[i:j + 1]
        raise AssertionError("unbalanced")

    def bytes_of(block):
        vals = []
        for tok in re.findall(r"'\\x([0-9a-fA-F]{2})'|'(.)'|0[xX]([0-9a-fA-F]+)", block):
            if tok[0]:
                vals.append(int(tok[0], 16))
            elif tok[1]:
                vals.append(ord(tok[1]))
            else:
                vals.append(int(tok[2], 16))
        return vals

    tcvn3 = bytes_of(section("TCVN3"))
    vni = bytes_of(section("VNI-WIN"))
    return tcvn3, vni


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--openkey", required=True)
    ap.add_argument("--unikey", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    uni_rows, tcvn_rows, vni_rows = parse_openkey_tables(args.openkey)

    # unicode -> (tcvn3 byte, vni bytes tuple)
    mapping = {}
    for r in range(len(uni_rows)):
        for k in range(len(uni_rows[r])):
            u = uni_rows[r][k]
            if u == 0:
                continue
            t = tcvn_rows[r][k]
            v = vni_rows[r][k]
            assert t <= 0xFF, (hex(u), hex(t))
            vni_bytes = (v & 0xFF, v >> 8) if v > 0xFF else (v & 0xFF,)
            if u in mapping:
                assert mapping[u] == (t, vni_bytes), (
                    f"conflict for U+{u:04X}: {mapping[u]} vs {(t, vni_bytes)}")
            else:
                mapping[u] = (t, vni_bytes)

    # ---- cross-check against Unikey's data.cpp ----
    tcvn3_u, vni_u = parse_unikey_data(args.unikey)
    n_vn = len(STD_ORDER)
    assert len(tcvn3_u) >= n_vn, (len(tcvn3_u), n_vn)
    assert len(vni_u) >= n_vn, (len(vni_u), n_vn)
    errors = []
    for i, ch in enumerate(STD_ORDER):
        u = ord(ch)
        if u not in mapping:
            # consonants / plain vowels: identity in both tables
            if tcvn3_u[i] != u:
                errors.append(f"TCVN3 identity mismatch at {ch} U+{u:04X}: table has {tcvn3_u[i]:#x}")
            if not (len(vni_u) > i and vni_u[i] == u):
                errors.append(f"VNI identity mismatch at {ch} U+{u:04X}: table has {vni_u[i]:#x}")
            continue
        t, vb = mapping[u]
        if tcvn3_u[i] != t:
            errors.append(f"TCVN3 mismatch {ch} U+{u:04X}: openkey {t:#x} vs unikey {tcvn3_u[i]:#x}")
        vu = vni_u[i]
        exp_vb = (vu & 0xFF, vu >> 8) if vu > 0xFF else (vu & 0xFF,)
        if vb != exp_vb:
            errors.append(f"VNI mismatch {ch} U+{u:04X}: openkey {vb} vs unikey {exp_vb}")
    if errors:
        print("CROSS-CHECK FAILED:")
        for e in errors:
            print("  " + e)
        sys.exit(1)
    print(f"cross-check OK: {len(mapping)} mapped chars verified against Unikey's data.cpp")

    # ---- emit CharsetTable.inc ----
    entries = sorted(mapping.items())
    lines = []
    lines.append("// Generated by Tools/gen_charset_table.py — DO NOT EDIT.")
    lines.append("// Unicode -> TCVN3 (ABC) / VNI Windows, from OpenKey's _codeTable,")
    lines.append("// cross-checked entry-by-entry against Unikey's data.cpp (fcitx5-unikey).")
    lines.append("// Sorted by Unicode code point for binary search.")
    lines.append("static const CharsetEntry kCharsetTable[] = {")
    for u, (t, vb) in entries:
        ch = chr(u)
        vni_init = "{" + ", ".join(f"0x{b:02X}" for b in vb) + "}"
        lines.append(f"    {{0x{u:04X}, 0x{t:02X}, {vni_init}, {len(vb)}}},  // {ch}")
    lines.append("};")
    lines.append(f"static const int kCharsetTableSize = {len(entries)};")
    open(args.out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(f"wrote {args.out} ({len(entries)} entries)")


if __name__ == "__main__":
    main()

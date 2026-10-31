// Output charset conversion: Unicode -> TCVN3 (ABC) / VNI Windows.
// The mapping table is generated (Tools/gen_charset_table.py) from OpenKey's
// _codeTable and cross-checked entry-by-entry against Unikey's own tables
// (SingleByteTables/DoubleByteTables in fcitx5-unikey/unikey/data.cpp).
#include "Charset.h"

namespace vikey { namespace charset {

struct CharsetEntry {
    wchar_t unicode;
    unsigned char tcvn3;
    unsigned char vni[2];
    unsigned char vniLen;   // 1 or 2
};

#include "CharsetTable.inc"

static const CharsetEntry* find(wchar_t ch) {
    int lo = 0, hi = kCharsetTableSize - 1;
    while (lo <= hi) {
        int mid = (lo + hi) / 2;
        wchar_t u = kCharsetTable[mid].unicode;
        if (u == ch) return &kCharsetTable[mid];
        if (u < ch) lo = mid + 1; else hi = mid - 1;
    }
    return nullptr;
}

int convert(wchar_t ch, Charset cs, wchar_t out[2]) {
    if (cs == Charset::Unicode) { out[0] = ch; return 1; }
    const CharsetEntry* e = find(ch);
    if (!e) { out[0] = ch; return 1; }   // ASCII, emoji, ...: unchanged
    if (cs == Charset::Tcvn3) { out[0] = (wchar_t)e->tcvn3; return 1; }
    out[0] = (wchar_t)e->vni[0];
    if (e->vniLen > 1) { out[1] = (wchar_t)e->vni[1]; return 2; }
    return 1;
}

}} // namespace

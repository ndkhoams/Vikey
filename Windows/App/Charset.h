// Output charset for the characters Vikey types: Unicode (the default), TCVN3 (ABC)
// or VNI Windows, like Unikey's "Bảng mã". The engine always composes Unicode;
// this module converts each composed character to the target encoding just before
// it is sent to the focused app (Core.cpp).
//
// TCVN3: every Vietnamese character is one byte (Unikey's SingleByteTables).
// VNI Windows: one byte, or two (base character, then the mark) for vowels with
// a hat/breve/horn or a tone (Unikey's DoubleByteTables).
#pragma once

namespace vikey { namespace charset {

enum class Charset : int {
    Unicode = 0,
    Tcvn3 = 1,
    Vni = 2,
};

/// Converts one composed character to the target charset. Writes 1 or 2 UTF-16
/// units into out (each unit is sent with KEYEVENTF_UNICODE) and returns how
/// many were written. Characters with no mapping (ASCII, emoji, ...) pass
/// through unchanged as a single unit.
int convert(wchar_t ch, Charset cs, wchar_t out[2]);

/// How many output units convert() would produce (1 or 2), without converting.
inline int unitCount(wchar_t ch, Charset cs) {
    wchar_t tmp[2];
    return convert(ch, cs, tmp);
}

}} // namespace

#!/usr/bin/env python3
# vim: set sts=4 sw=4 et :
#
# sh2seedgrinder.py
# Copyright (c) GreaseMonkey, 2019
#
# This software is provided 'as-is', without any express or implied
# warranty. In no event will the authors be held liable for any damages
# arising from the use of this software.
#
# Permission is granted to anyone to use this software for any purpose,
# including commercial applications, and to alter it and redistribute it
# freely, subject to the following restrictions:
#
#     1. The origin of this software must not be misrepresented; you
#        must not claim that you wrote the original software. If you use
#        this software in a product, an acknowledgment in the product
#        documentation would be appreciated but is not required.
#
#     2. Altered source versions must be plainly marked as such, and
#        must not be misrepresented as being the original software.
#
#     3. This notice may not be removed or altered from any source
#        distribution.
#

"""Grinds the entire 2^31 seed space for Silent Hill 2 and spit out the results.
Bail out if more than 100 results are found.

You will probably want at least Python 3.6.
Python 3.7 should be fine.
Run this in the command line! It comes with its own help and some sanity checking.

Using Python for something that's supposed to be fast was probably a mistake.
numba is pretty fast, but also pretty crashy.

Also it's slower than I'd like it to be at this point.

Oh yeah, as expected, big shoutouts to sh2_luck for doing this stuff and making a table and actually making SH2 RNG manip viable for runs. sh2_luck was also a big help with answering questions when I attempted to reverse-engineer the RNG myself after their discovery, and that made it possible for me to replicate their work.
"""
BASE_SEED = 0x6A4F8C55

import argparse

# GOTTA GO FAST
from numba import jit
from numba.types import uint32
import numpy

briefcase_words = [
    "open", "damn", "hell", "town",
    "dark", "mama", "down", "love",
    "lock", "mist", "luck", "lose",
    "dose", "over", "dust", "time",
    "help", "kill", "null", "cock",
]

def spew_result(r, seed, m_clock_angle, m_code_blood, m_code_carbon, m_code_spin, m_bug_code, m_arsonist, m_briefcase):
    result = "%10u,0x%08X,%02d:%02d,%04d,%04d,%04d,%03d,%1d,%4s" % (
        r,
        seed,
        m_clock_angle//60,
        m_clock_angle%60,
        m_code_blood,
        m_code_carbon,
        m_code_spin,
        m_bug_code,
        m_arsonist,
        briefcase_words[m_briefcase],
    )
    print(result)

@jit(
    nopython=True,
    nogil=True,
    locals={
        "R": uint32[:],
        "results": uint32[:, ::1],
        "matches": uint32[:],
        "rslot": uint32,
        "r": uint32,
        "rreal": uint32,
        "m_clock_angle": uint32,
        "m_code_carbon": uint32,
        "m_code_blood": uint32,
        "m_code_spin": uint32,
        "m_code_carbon": uint32,
        "code1digit": uint32,
        "code2digit": uint32,
        "m_code_blood": uint32,
        "m_code_spin": uint32,
        "digit0": uint32,
        "digit1": uint32,
        "digit2": uint32,
        "orig_digit2": uint32,
        "m_bug_code": uint32,
        "arsonist_shuffle": uint32[:],
        "m_arsonist": uint32,
        "i": uint32,
        "iVar5": uint32,
        "m_arsonist": uint32,
        "m_briefcase": uint32,
        "seed": uint32,
    },
)
def calc_all_from_seed(R, arsonist_shuffle, matches, results, rslot, rreal) -> bool:
    r = rreal & 0x3F
    m_clock_angle = (R[(r+1)] % 660)
    if m_clock_angle > 520:
        m_clock_angle = m_clock_angle + 60

    if True:
        m_code_carbon = (0
            + ((R[(r+ 7)] % 9) + 1) * 1000
            + ((R[(r+10)] % 9) + 1) * 100
            + ((R[(r+13)] % 9) + 1) * 10
            + ((R[(r+16)] % 9) + 1)
        )
        m_code_blood = 0
        m_code_spin = 0
        for i in range(4):
            code1digit = R[(r+8+i*3)] % 9
            code2digit = ((R[(r+9+i*3)] % 8) + 1 + code1digit) % 9
            #m_code_blood += (code1digit+1) * (10**(3-i))
            #m_code_spin += (code2digit+1) * (10**(3-i))
            m_code_blood = (code1digit+1) + m_code_blood * 10
            m_code_spin = (code2digit+1) + m_code_spin * 10

    else:
        m_code_carbon = 0
        m_code_blood = 0
        m_code_spin = 0
        for i in range(4):
            m_code_carbon = ((R[(r+7+i*3)] % 9) + 1) + m_code_carbon * 10
            #m_code_carbon += ((R[(r+7+i*3)] % 9) + 1) * (10**(3-i))

            code1digit = R[(r+8+i*3)] % 9
            code2digit = ((R[(r+9+i*3)] % 8) + 1 + code1digit) % 9
            #m_code_blood += (code1digit+1) * (10**(3-i))
            #m_code_spin += (code2digit+1) * (10**(3-i))
            m_code_blood = (code1digit+1) + m_code_blood * 10
            m_code_spin = (code2digit+1) + m_code_spin * 10

    digit0 = R[(r+19)] % 9
    digit1 = R[(r+20)] % 8
    digit2 = R[(r+21)] % 7
    orig_digit2 = digit2
    if digit0 <= digit1: digit1 += 1
    if digit0 <= orig_digit2: digit2 += 1
    if digit1 <= orig_digit2: digit2 += 1

    m_bug_code = (0
        + 100*(digit0+1)
        + 10 *(digit1+1)
        + 1  *(digit2+1)
    )

    m_arsonist = 999
    for i in range(6):
        arsonist_shuffle[i] = i

    for i in range(6):
        iVar5 = i + (R[(r+22+i)] % (6-i))
        if arsonist_shuffle[iVar5] == 5:
            m_arsonist = (5-i)+1
        arsonist_shuffle[iVar5] = arsonist_shuffle[i]

    m_briefcase = R[(r+30)] % 19

    results[rslot][0] = m_clock_angle
    results[rslot][1] = m_code_blood
    results[rslot][2] = m_code_carbon
    results[rslot][3] = m_code_spin
    results[rslot][4] = m_bug_code
    results[rslot][5] = m_arsonist
    results[rslot][6] = m_briefcase
    for i in range(7):
        if matches[i] < 0x10000 and results[rslot][i] != matches[i]:
            return False

    results[rslot][7] = rreal
    results[rslot][8] = R[(r+0)]
    return True


@jit(
    nopython=True,
    locals={
        "R": uint32[:],
        "arsonist_shuffle": uint32[:],
        "results": uint32[:, ::1],
        "matches": uint32[:],
        "seedoffs": uint32,
        "seedstep": uint32,
        "seed": uint32,
        "i": uint32,
        "j": uint32,
        "r": uint32,
        "rstep": uint32,
    },
)
def grind_seeds(matches, results, seedoffs, seedstep) -> int:
    R = numpy.full(0x80, uint32(0))
    arsonist_shuffle = numpy.full(6, uint32(0))
    rslot = 0

    seed = BASE_SEED
    for i in range(0x40):
        R[i] = seed
        R[i+0x40] = seed
        seed = ((seed * 1103515245) + 12345) & 0x7FFFFFFF

    for j in range(seedoffs):
        R[(j+0x40)&0x7F] = seed
        R[(j+0x80)&0x7F] = seed
        seed = ((seed * 1103515245) + 12345) & 0x7FFFFFFF

    for r in range(seedoffs, 1<<31, seedstep):
        if calc_all_from_seed(R, arsonist_shuffle, matches, results, rslot, r):
            rslot += 1

        for j in range(seedstep):
            R[(r+j+0x40)&0x7F] = seed
            R[(r+j+0x80)&0x7F] = seed
            seed = ((seed * 1103515245) + 12345) & 0x7FFFFFFF

        if (r & 0xFFFFF) == 0: print(r*100.0/(1<<31))

        if rslot >= 100:
            return rslot

    return rslot


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--clock",
        type=str,
        default=None,
        help="Force a clock in HH:MM format.",
    )

    parser.add_argument(
        "--blood",
        type=int,
        default=None,
        help="Force a 4-digit blood combination.",
    )

    parser.add_argument(
        "--carbon",
        type=int,
        default=None,
        help="Force a 4-digit carbon combination.",
    )

    parser.add_argument(
        "--spin",
        type=int,
        default=None,
        help="Force a 4-digit spin combination.",
    )

    parser.add_argument(
        "--bug",
        type=int,
        default=None,
        help="Force a 3-digit bug room combination.",
    )

    parser.add_argument(
        "--arsonist",
        type=int,
        default=None,
        help="Force an arsonist location from 1 to 6.",
    )

    parser.add_argument(
        "--case",
        type=lambda x : briefcase_words.index(x),
        default=None,
        help="Force a 4-letter briefcase word.",
    )

    args = parser.parse_args()

    matches = numpy.full(9, uint32(0x10000))

    has_constraint = False

    clock_str = args.clock
    clock = None
    if clock_str is not None:
        clock_h_str, _, clock_m_str, = clock_str.partition(":")
        clock_h = int(clock_h_str)
        clock_m = int(clock_m_str)
        assert 0 <= clock_h < 12
        assert 0 <= clock_m < 60
        clock = 60*clock_h+clock_m
        matches[0] = clock
        has_constraint = True

    blood = args.blood
    if blood is not None:
        assert 1111 <= blood <= 9999
        assert "0" not in str(blood)
        matches[1] = blood
        has_constraint = True

    carbon = args.carbon
    if carbon is not None:
        assert 1111 <= carbon <= 9999
        assert "0" not in str(carbon)
        matches[2] = carbon
        has_constraint = True

    spin = args.spin
    if spin is not None:
        assert 1111 <= spin <= 9999
        assert "0" not in str(spin)
        matches[3] = spin
        has_constraint = True

    bug = args.bug
    if bug is not None:
        assert 111 <= bug <= 999
        assert "0" not in str(bug)
        assert sorted(set(list(bug))) == list(bug)
        matches[4] = bug
        has_constraint = True

    arsonist = args.arsonist
    if arsonist is not None:
        assert 1 <= arsonist <= 6
        matches[5] = arsonist
        has_constraint = True

    case = args.case
    if case is not None:
        assert isinstance(case, int), f"programmer error w/ briefcase index being {case!r}"
        matches[6] = case
        has_constraint = True

    if not has_constraint:
        print("Please provide at least one constraint.")
        print("")
        parser.print_help()
        parser.exit(1)

    seedstep = 1
    seedoffs = 0
    # seedstep optimisation:
    # Look at the bottom bits of various mod 2^N seed sources.
    # If they're set, we can find our starting point.
    # TODO: Most of these.
    if clock is not None:
        clockseedoffs = (clock+2)&0x3
        assert ((seedoffs^clockseedoffs)&(seedstep-1)) == 0, "these seeds can't work"
        seedstep = 4
        seedoffs = clockseedoffs

    results = numpy.full((100, 9), uint32(0))
    result_count = grind_seeds(matches, results, seedoffs, seedstep)
    for rslot in range(result_count-1,-1,-1):
        m_clock_angle = results[rslot][0]
        m_code_blood = results[rslot][1]
        m_code_carbon = results[rslot][2]
        m_code_spin = results[rslot][3]
        m_bug_code = results[rslot][4]
        m_arsonist = results[rslot][5]
        m_briefcase = results[rslot][6]
        r = results[rslot][7]
        tseed = results[rslot][8]
        result = f"{r:10d},0x{tseed:08X},{m_clock_angle//60:02d}:{m_clock_angle%60:02d},{m_code_blood:04d},{m_code_carbon:04d},{m_code_spin:04d},{m_bug_code:03d},{m_arsonist:1d},{briefcase_words[m_briefcase]}"
        print(result)
    if result_count >= 100:
        print(f"{result_count:10d}+ results found")
    else:
        print(f"{result_count:11d} results found")

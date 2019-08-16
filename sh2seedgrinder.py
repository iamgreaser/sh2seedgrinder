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

UPDATE: numba is now gone.

Oh yeah, as expected, big shoutouts to sh2_luck for doing this stuff and making a table and actually making SH2 RNG manip viable for runs. sh2_luck was also a big help with answering questions when I attempted to reverse-engineer the RNG myself after their discovery, and that made it possible for me to replicate their work.
"""

BASE_SEED = 0x6A4F8C55
PARALLEL_LENGTH = 2048
#PARALLEL_LENGTH = 2

import argparse
from typing import List
from typing import Sequence
from typing import Tuple

# GOTTA GO FAST
# WITHOUT BEING A BROKEN PILE OF GARBAGE THIS TIME SO GOODBYE NUMBA
import numpy
from numpy import uint32 as BASE_TYPE
#from numpy import int64 as BASE_TYPE

briefcase_words = [
    "open", "damn", "hell", "town",
    "dark", "mama", "down", "love",
    "lock", "mist", "luck", "lose",
    "dose", "over", "dust", "time",
    "help", "kill", "null", "cock",
]

SEED_MUL = BASE_TYPE(1103515245)
SEED_ADD = BASE_TYPE(12345)
SEED_ANDMASK = BASE_TYPE(0x7FFFFFFF)
SEED_MOD = BASE_TYPE(0x80000000)

def rand_once(seed: int) -> int:
    return ((seed * SEED_MUL) + SEED_ADD) & SEED_ANDMASK


def rand_nlow_coeffs(n: int) -> Tuple[int, int]:
    a = 1
    c = 0
    for i in range(n):
        c = (c + a) & SEED_ANDMASK
        a = (a * SEED_MUL) & SEED_ANDMASK
    c = (c * SEED_ADD) & SEED_ANDMASK
    return (a, c,)


def rand_nlow_coeffs_accumulated(n: int) -> Tuple[Sequence[int], Sequence[int]]:
    a = 1
    c = 0
    La: List[int] = []
    Lc: List[int] = []
    for i in range(n):
        La.append(BASE_TYPE(a))
        Lc.append(BASE_TYPE(c))
        c = (c + a * SEED_ADD) & SEED_ANDMASK
        a = (a * SEED_MUL) & SEED_ANDMASK
    return (La, Lc,)


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


def calc_all_from_seed(*, R, zero, match_mask, match_value, results, selection, rreal):
    m_clock_angle = R[1]
    m_clock_angle += (m_clock_angle > BASE_TYPE(520)) * BASE_TYPE(60)

    m_code_carbon = (
          R[ 7] * BASE_TYPE(1000)
        + R[10] * BASE_TYPE(100)
        + R[13] * BASE_TYPE(10)
        + R[16]
        + BASE_TYPE(1111)
    )
    code1digit0 =   R[ 8]
    code2digit0 = ((R[ 9]) + BASE_TYPE(1) + code1digit0) % BASE_TYPE(9)
    code1digit1 =   R[11]
    code2digit1 = ((R[12]) + BASE_TYPE(1) + code1digit1) % BASE_TYPE(9)
    code1digit2 =   R[14]
    code2digit2 = ((R[15]) + BASE_TYPE(1) + code1digit2) % BASE_TYPE(9)
    code1digit3 =   R[17]
    code2digit3 = ((R[18]) + BASE_TYPE(1) + code1digit3) % BASE_TYPE(9)
    m_code_blood = (
          code1digit0 * BASE_TYPE(1000)
        + code1digit1 * BASE_TYPE(100)
        + code1digit2 * BASE_TYPE(10)
        + code1digit3
        + BASE_TYPE(1111)
    )
    m_code_spin = (
          code2digit0 * BASE_TYPE(1000)
        + code2digit1 * BASE_TYPE(100)
        + code2digit2 * BASE_TYPE(10)
        + code2digit3
        + BASE_TYPE(1111)
    )

    digit0 = R[(19)]
    digit1 = R[(20)]
    digit2 = R[(21)]
    orig_digit2 = digit2
    digit1 += (digit0 <= digit1)
    digit2 += (digit0 <= orig_digit2)
    digit2 += (digit1 <= orig_digit2)

    # FIXME: I recall a seed where this reported 594 but the code was 495.
    # It matches the sheet, but this may have been something that was done backwards --GM
    m_bug_code = (
          BASE_TYPE(100)*digit0
        + BASE_TYPE(10 )*digit1
        + BASE_TYPE(1  )*digit2
        + BASE_TYPE(111)
    )

    m_arsonist = zero.copy()

    iVar5 = BASE_TYPE(0) + R[22]
    m_arsonist += BASE_TYPE(6)*(iVar5 == BASE_TYPE(5))*(m_arsonist == BASE_TYPE(0))
    iVar5 = BASE_TYPE(1) + R[23]
    m_arsonist += BASE_TYPE(5)*(iVar5 == BASE_TYPE(5))*(m_arsonist == BASE_TYPE(0))
    iVar5 = BASE_TYPE(2) + R[24]
    m_arsonist += BASE_TYPE(4)*(iVar5 == BASE_TYPE(5))*(m_arsonist == BASE_TYPE(0))
    iVar5 = BASE_TYPE(3) + R[25]
    m_arsonist += BASE_TYPE(3)*(iVar5 == BASE_TYPE(5))*(m_arsonist == BASE_TYPE(0))
    iVar5 = BASE_TYPE(4) + R[26]
    m_arsonist += BASE_TYPE(2)*(iVar5 == BASE_TYPE(5))*(m_arsonist == BASE_TYPE(0))
    iVar5 = BASE_TYPE(5) + R[27]
    m_arsonist += BASE_TYPE(1)*(iVar5 == BASE_TYPE(5))*(m_arsonist == BASE_TYPE(0))

    m_briefcase = R[(30)]

    results[0] = m_clock_angle
    results[1] = m_code_blood
    results[2] = m_code_carbon
    results[3] = m_code_spin
    results[4] = m_bug_code
    results[5] = m_arsonist
    results[6] = m_briefcase
    results[7] = rreal
    results[8] = R[0]
    selection = ((results*match_mask==match_value*match_mask).sum(axis=0) == 9)

    return (selection, results)


SEED_MUL_ARRAY = numpy.full(32, 0, dtype=BASE_TYPE)
SEED_ADD_ARRAY = numpy.full(32, 0, dtype=BASE_TYPE)
for i in range(32):
    a, c, = rand_nlow_coeffs(i)
    SEED_MUL_ARRAY[i] = a
    SEED_ADD_ARRAY[i] = c

MOD_ARRAY = numpy.array([
    0x80000000,
    # 1
    660,
    0x80000000,
    0x80000000,
    0x80000000,
    0x80000000,
    0x80000000,
    # 7
    9, 9, 8,
    9, 9, 8,
    9, 9, 8,
    9, 9, 8,
    # 19
    9, 8, 7,
    # 22
    6, 5, 4, 3, 2, 1,
    # 28
    0x80000000,
    0x80000000,
    # 30
    19,
    # 31
    0x80000000,
], dtype=BASE_TYPE)

MOD_ARRAY = (numpy.full((PARALLEL_LENGTH, 32,), 1, dtype=BASE_TYPE) * MOD_ARRAY).transpose()

def grind_seeds(*, matches, seedoffs, seedstep) -> int:

    seed = BASE_SEED
    for j in range(seedoffs):
        seed = ((seed * 1103515245) + 12345) & 0x7FFFFFFF

    rslot = 0
    results = numpy.full(9, 0, dtype=BASE_TYPE)
    selection = False
    zero = 0
    match_mask = numpy.array([int(v < 0x10000) for v in matches], dtype=BASE_TYPE)
    match_value = numpy.array(matches, dtype=BASE_TYPE)

    out_results = []

    R = numpy.full(32, seed, dtype=BASE_TYPE)
    R *= SEED_MUL_ARRAY
    R &= 0x7FFFFFFF
    R += SEED_ADD_ARRAY
    R &= 0x7FFFFFFF

    # Arrayify it
    seedstep_a, seedstep_c, = rand_nlow_coeffs(seedstep * PARALLEL_LENGTH)
    seedstep_parallel = seedstep * PARALLEL_LENGTH
    La, Lc, = rand_nlow_coeffs_accumulated(seedstep_parallel)
    PARALLEL_A = numpy.array(La[::seedstep], dtype=BASE_TYPE)
    PARALLEL_C = numpy.array(Lc[::seedstep], dtype=BASE_TYPE)

    R = (numpy.full((PARALLEL_LENGTH, 32,), 1, dtype=BASE_TYPE) * R).transpose()
    R *= PARALLEL_A
    R &= SEED_ANDMASK
    R += PARALLEL_C
    R &= SEED_ANDMASK
    results = (numpy.full((PARALLEL_LENGTH, 9,), 1, dtype=BASE_TYPE) * numpy.full(9, 0, dtype=BASE_TYPE)).transpose()
    selection = numpy.full(PARALLEL_LENGTH, selection, dtype=BASE_TYPE)
    zero = numpy.full(PARALLEL_LENGTH, zero, dtype=BASE_TYPE)
    match_mask = (numpy.full((PARALLEL_LENGTH, len(matches),), 1, dtype=BASE_TYPE) * match_mask).transpose()
    match_value = (numpy.full((PARALLEL_LENGTH, len(matches),), 1, dtype=BASE_TYPE) * match_value).transpose()

    for r in range(seedoffs, 1<<31, seedstep_parallel):
        rreal = r + numpy.arange(PARALLEL_LENGTH, dtype=BASE_TYPE)*seedstep
        #R = (seed * SEED_MUL_ARRAY + SEED_ADD_ARRAY) & 0x7FFFFFFF
        #R = (seed * SEED_MUL_ARRAY + SEED_ADD_ARRAY) & 0x7FFFFFFF
        R2 = R % MOD_ARRAY
        #results *= 0
        new_selection, new_results = calc_all_from_seed(
            R=R2,
            zero=zero,
            match_mask=match_mask,
            match_value=match_value,
            results=results,
            selection=selection,
            rreal=rreal,
        )

        for ns, nr in zip(new_selection, new_results.transpose()):
            if ns:
                out_results.append(nr.tolist())
                rslot += 1
        #rslot += did_calc
        #print(new_results)

        R *= BASE_TYPE(seedstep_a)
        R &= SEED_ANDMASK
        R += BASE_TYPE(seedstep_c)
        R &= SEED_ANDMASK
        #seed = R[0]

        if ((r-seedoffs+seedstep_parallel) & 0xFFFFF) == 0: print((r-seedoffs+seedstep_parallel)*100.0/(1<<31))

        if rslot >= 100:
            return out_results

    return out_results


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

    parser.add_argument(
        "--force",
        action="store_true",
        help="Generate something even if no constraints are provided.",
    )

    args = parser.parse_args()

    matches = numpy.full(9, 0x10000, dtype=BASE_TYPE)

    has_constraint = False

    if args.force:
        has_constraint = True

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

    results = grind_seeds(
        matches=matches,
        seedoffs=seedoffs,
        seedstep=seedstep,
    )
    results = results[::-1]
    result_count = len(results)

    for rslot in range(len(results)):
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

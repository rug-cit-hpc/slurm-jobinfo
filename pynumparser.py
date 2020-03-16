#!/usr/bin/python
#
# Works with either Python v2.7+ or v3.3+
#
"""
This module provides two classes for use in parsing string form of numbers and
number sequences: NumberSequence and Number.

1. pynumparser.NumberSequence

   * Simple parsing for intuitive representation of number sequences.
   * Optional lower and/or upper limits can be enforced.
   * Handles integer or floating point numbers.
   * Subsequences can have step values other than one (1).
   * Designed to work well with an argparse.ArgumentParser, including well
     formed errors when syntax or limits are violated.
   * Provides a class method to convert number sequences into the string form:

   * Parsing Examples:
       "5"          ==> (5,)
       "1,3,8"      ==> (1, 3, 8)
       "8-10,30"    ==> (8, 9, 10, 30)
       "5-30/5,100" ==> (5, 10, 15, 20, 25, 30, 100)
       "8,10+3"     ==> (8, 10, 11, 12, 13)

   * Encoding Example:
       (5, 10, 15, 20, 25, 30, 100, 101, 102, 110) ==> "5-30/5,100-102,110"

2. pynumparser.Number

   * Simple way to impose limits on numbers from command line or config files.
   * Either or both lower and upper limits can be provided.
   * Handles integer and floating point numbers.
   * Designed to work well with an argparse.ArgumentParser, including well
     formed errors when limits are violated.

Example Usage:

    #!/usr/bin/env python
    import argparse
    import pynumrange

    # Use in an argparser to parse a sequence or a limited number:
    parser = argparse.ArgumentParser(description="pynumrange example")
    parser.add_argument('-n', '--numbers', default=[],
                        help="A sequence of numbers from 0..100",
                        type=pynumrange.NumberSequence(int, limits=(0, 100))
    parser.add_argument('-i', '--int', default=[], action='append',
                        help="A number in the range 1..10; multiple use okay",
                        type=pynumrange.Number(int, limits=(1, 10))
    parser.add_argument('direct', nargs='*')
    opts = parser.parse_args()
    print("ArgumentParser: numbers = %s" % opts.numbers)

    ## Or just create a parser and call it directly:
    num_parser = pynumrange.NumberSequence(float, limits=(-1000, +1000))
    for number in opts.direct:
        num_range = num_parser(number)
        print('Direct from ("%s"): %s' % (number, num_range))
"""

import math
import re
version = '1.4.1'

description = ('A library to parse arguments of numbers and number ' +
               'sequences, usable directly or with argparse. Allows' +
               ' concise representation of contiguous or non-contiguous' +
               ' sequences. Example: 1,5-10,40-50/5,200+100/25')

_SEQPATT = re.compile('^(.*[^-+e])([-+])([-+]?[.0-9][^-+]*([Ee][-+]?[0-9]+)?)$')


class NumberSequence(object):
    """This class parses concise numeric patterns into a numeric
    sequence, intended to be used directly, or with
    argparse.ArgumentParser. Numeric patterns are of the form:

       SEQUENCE :=  SUBSEQ [ ',' SEQUENCE ]
       SUBSEQ   :=  LOWER [ '-' UPPER [ '/' STRIDE ]]
       SUBSEQ   :=  LOWER [ '+' INCREMENT [ '/' STRIDE ]]

    Where all terminals (LOWER, UPPER, STRIDE) must be valid numbers.
    Example:   "1,5-7,20-30/5" would return: (1, 5, 6, 7, 20, 25, 30)
    Example:   "10-40/17,1+2"  would return: (10, 27, 34, 1, 2, 3)

    Instances can also efficiently test for membership in a sequence, eg:

       VALID_INPUTS = "0,10-20"
       parser = pynumparser.NumberSequence(int)

       if parser.contains(VALID_INPUTS, num):
           handle_user_input(num)"""

    def __init__(self, numtype=int, limits=None, generator=False):
        self.numtype = numtype
        self.generator = generator
        if numtype not in (int, float):
            raise ValueError("NumberSequence: Invalid numeric type: " +
                             str(numtype))
        self.lowest, self.highest = limits or (None, None)
        self.error = None

    def __repr__(self):
        text = self.numtype.__name__.capitalize() + "Sequence"
        if None not in (self.lowest, self.highest):
            text += " (from %s to %s)" % (self.lowest, self.highest)
        elif self.lowest is not None:
            text += " (at least %s)" % self.lowest
        elif self.highest is not None:
            text += " (not over %s)" % self.highest
        if self.error:
            text += ', ERROR: "%s"' % self.error
        return text

    @classmethod
    def _range(cls, lower, upper, delta):
        while lower <= upper:
            yield lower
            lower += delta

    def _error(self, tag, fmt, *args):
        self.error = tag
        raise ValueError("NumberSequence: " + (tag and tag + " ") +
                         (fmt.format(args) if args else fmt))

    def _subsequences(self, text):
        for nss, subseq in enumerate(text.split(',')):
            if not subseq:
                self._error("Empty subsequence",
                            "Subsequence #{} is empty", nss)
            tag = "Subsequence \"{}\": ".format(subseq)
            if '/' in subseq:
                if '-' not in subseq[1:] and '+' not in subseq[1:]:
                    self._error("Missing UPPER",
                                tag + "STEP w/o UPPER (\"{}\")", subseq)
                lowup, step = subseq.split('/')
                try:
                    step = self.numtype(step)
                except Exception:
                    self._error("Invalid STEP",
                                tag + "Invalid STEP(\"{}\")", step)
                if step <= 0:
                    self._error("STEP must be positive", tag +
                                "STEP must be positive (\"{}\")".format(step))
            else:
                lowup, step = subseq, 1

            # We handle all of: "-5", "2", "-3-5", "-3--1", "3-21",
            # and "1e-5-1.001e-5/1e-8", "-20+10", "-2e+2+1e02"
            seq = _SEQPATT.match(lowup)
            if seq:
                lower, sep, upper = seq.group(1, 2, 3)
                try:
                    lower = self.numtype(lower)
                except ValueError:
                    self._error("Invalid LOWER", tag +
                                "LOWER({}) is invalid".format(lower))
                try:
                    upper = self.numtype(upper)
                except ValueError:
                    self._error("Invalid UPPER", tag +
                                "UPPER({}) is invalid".format(upper))
                if sep == '+':
                    upper += lower
                if upper < lower:
                    self._error("UPPER<LOWER", tag +
                                "UPPER({}) is less than LOWER({})".format(
                                    upper, lower))
            else:
                try:
                    lower = upper = self.numtype(lowup)
                except ValueError:
                    self._error("Parse Error", "invalid {} value: '{}'".format(
                        self.numtype.__name__, lowup))
            if any(map(math.isinf, (lower, upper, step))):
                self._error("Infinite Value", tag +
                            "Numeric values cannot be infinite ({})".format(
                                subseq))
            if self.lowest is not None and lower < self.lowest:
                self._error("LOWER too small", tag +
                            "LOWER({}) cannot be less than ({})".format(
                                lower, self.lowest))
            if self.highest is not None and upper > self.highest:
                self._error("UPPER too large", tag +
                            "UPPER({}) cannot be greater than ({})".format(
                                upper, self.highest))

            yield (tag, nss, subseq, lower, upper, step)

    def xparse(self, text):
        """This is a generator for the numbers that 'parse()' returns.
        Use this (rather than 'parse()') in the same way you would use
        'xrange()' in lieu of 'range()'."""
        self.error = None
        for nss, tag, subseq, lower, upper, step in self._subsequences(text):
            for num in self._range(lower, upper, step):
                yield num

    def contains(self, text, number):
        """Returns true if the given NUMBER is contained in this range."""
        if isinstance(number, (tuple, list)):
            return tuple(self.contains(text, num) for num in number)
        try:
            number = self.numtype(number)
        except (TypeError, ValueError):
            return False
        for nss, tag, subseq, lower, upper, step in self._subsequences(text):
            if number in (lower, upper):
                return True
            if lower < number and number < upper:
                if (number - lower) % step == 0:
                    return True
                elif self.numtype == float:
                    # We compare to within 10 PPM (0.001%); arbitrary but good.
                    epsilon = step / 1e5
                    if (abs(number - lower + epsilon) % step) < 2 * epsilon:
                        return True
        return False

    def parse(self, text):
        """This returns a tuple of numbers."""
        return tuple(self.xparse(text))

    def __call__(self, text):
        if self.generator:
            return self.xparse(text)
        return self.parse(text)

    @classmethod
    def encode(cls, sequence):
        """Convert a list/tuple of numbers into a string form. This uses the
        "str(n)" operator for each piece, there is no explicit formatting.

        @param sequence the tuple or list of numbers to be combined.
        @returns a str form for the sequence."""

        if not sequence:
            return ""

        # Return the delta that occurs most often in the given SEQ.
        def delta(seq, start=1, width=4):
            seq = seq[start:start + width]
            if len(seq) < 2:
                return 1
            # First order delta.
            _seq = [seq[i + 1] - seq[i] for i in range(len(seq) - 1)]
            # Count and sorted.
            pairs = [(_seq.count(i), i) for i in set(_seq)]
            pairs.append((2, 1))   # favor '1'
            return sorted(pairs, reverse=True)[0][1]

        # Start with the first number, and iterate looking ahead for longer
        # runs of the same step value.
        result = []
        base = sequence[0]
        last = base
        term = str(base)
        ndel = delta(sequence, 0)
        for i, num in enumerate(sequence[1:]):
            if num == (last + ndel):
                last += ndel
                continue
            # Use "4,5" not "4-5"
            if last == (base + ndel):
                result.append(term)
                term = str(last)

            # With a "-" and maybe a "/".
            elif last > base:
                term += "-" + str(last)
                if ndel != 1:
                    term += "/" + str(ndel)
            result.append(term)
            ndel = delta(sequence, i + 2)
            base = num
            last = base
            term = str(base)
        if last > base:
            term += "-" + str(last)
            if ndel != 1:
                term += "/" + str(ndel)
        result.append(term)
        return ",".join(result)


class Number(object):
    """This class can be used directly or with argparse.ArgumentParser,
    to parse numbers and enforce lower and/or upper limits on their values.

    Example:
      * Number(limits=(0,100))
           Would return an int value, which must be from 0 to 100, inclusive.
      * Number(limits=(5,None))
           Would return an int value, which must be no less than 5.
      * Number(numtype=float, limits=(-1000, 1000))
           Would return a float value, from -1000 to 1000 inclusive.
    """
    def __init__(self, numtype=int, limits=None):
        if numtype not in (int, float):
            raise ValueError("Number: Invalid numeric type: " +
                             str(numtype))
        self.lowest, self.highest = limits or (None, None)
        self.numtype = numtype
        self.typename = {int: 'Integer', float: 'Float'}.get(self.numtype)
        self.error = None

    def __repr__(self):
        text = self.typename
        if None not in (self.lowest, self.highest):
            text += " (from %s to %s)" % (self.lowest, self.highest)
        elif self.lowest is not None:
            text += " (at least %s)" % self.lowest
        elif self.highest is not None:
            text += " (not over %s)" % self.highest
        if self.error:
            text += ', ERROR: "%s"' % self.error
        return text

    def _error(self, tag, fmt, *args):
        self.error = tag
        raise ValueError("{}: {}{}".format(self.typename, (tag and tag + " "),
                                           fmt.format(args) if args else fmt))

    def parse(self, text):
        """This returns a tuple of numbers."""
        self.error = None
        try:
            value = self.numtype(text)
        except ValueError:
            self._error("Parse Error",
                        "invalid {} value: '{}'".format(self.typename, text))
        self._isvalid(value, error=True)
        return value

    def contains(self, number):
        """Returns true if the given NUMBER is valid and within the limits."""
        if isinstance(number, (tuple, list)):
            return tuple(self.contains(num) for num in number)
        # We explicitly allow testing if a float range contains an integer:
        if self.numtype is float and isinstance(number, int):
            number = float(number)
        return self._isvalid(number, error=False)

    def _isvalid(self, number, error):
        # Raise the error, or just return False.
        call = self._error if error else lambda *args: False
        if not isinstance(number, self.numtype):
            return call("Invalid Type",
                        "Invalid {} value ({})".format(
                            self.typename.lower(), number))
        elif math.isinf(number):
            return call("Infinite Value",
                        "Numeric values cannot be infinite ({})".format(number))
        elif self.lowest is not None and number < self.lowest:
            return call("Too Low",
                        "Value ({}) must not be less than {}".format(
                            number, self.lowest))
        elif self.highest is not None and number > self.highest:
            return call("Too High",
                        "Value ({}) must not be higher than {}".format(
                            number, self.highest))
        return True

    def __call__(self, text):
        return self.parse(text)

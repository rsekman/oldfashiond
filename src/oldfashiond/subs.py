from collections import OrderedDict
from enum import Enum

SubFormat = Enum("SubFormat", "ASS SRT")


def determine_sub_format(fname):
    """
    Returns a SubFormat corresponding to the type of the subtitle file fname.
    Raises ValueError if it is not a supported format, or the required
    dependency is not present.
    """

    def is_srt(f):
        try:
            from srt import parse, SRTParseError

            parse(f, ignore_errors=False)
        except (ImportError, SRTParseError):
            return False
        else:
            return True

    def is_ass(f):
        try:
            from ass import parse

            parse(f)
        except (ImportError, ValueError):
            return False
        else:
            return True

    fmt_tests = OrderedDict([(SubFormat.ASS, is_ass), (SubFormat.SRT, is_srt)])
    with open(fname, encoding="utf-8-sig") as f:
        for (fmt, test) in fmt_tests.items():
            if test(f):
                return fmt
            f.seek(0)

    raise ValueError(f"{fname} is not a supported subtitle file.")


def get_nth_sub_line(fname, n):
    """
    Returns a tuple (start, end) of the start and end times of the n:th line in
    the subtitle file fname. Both times are datetime.timedelta objects.
    Attempts to parse the file first as SRT, then as ASS. Raises IndexError if
    n is out of bounds and ValueError if the file is not valid SRT or ASS.
    """
    with open(fname, encoding="utf_8_sig") as f:
        # Try to read as SRT
        try:
            from srt import parse, SRTParseError

            for line in parse(f, ignore_errors=False):
                if line.index == n:
                    return (line.start, line.end)
            raise IndexError(f"Could not find line {n} in {fname}.")

        except (ImportError, SRTParseError):
            pass
        f.seek(0)
        try:
            from ass import parse

            sub = parse(f)
            # avoid off-by-one error: Aegiusub is 1-indexed
            line = sub.events[n - 1]
            return (line.start, line.end)
        except IndexError:
            raise IndexError("Could not find line {n} in {fname}.")
        except (ImportError, ValueError):
            pass
        raise ValueError(f"{fname} is not a supported subtitle file.")

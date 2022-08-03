#!/usr/bin/python

import argparse, subprocess, pathlib, tempfile, sys
from enum import Enum
from collections import OrderedDict
from datetime import datetime, timedelta

try:
    import humanfriendly

    def format_mtime(mtime):
        now = datetime.now()
        mtime = datetime.fromtimestamp(mtime)
        return humanfriendly.format_timespan(now - mtime) + " ago"

except ModuleNotFoundError:

    def format_mtime(mtime):
        # Format datetime according to current locale
        return datetime.fromtimestamp(mtime).strftime("%c%")


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
        except (ImportError, ValueError) as e:
            print(e)
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
        except (ImportError, ValueError) as e:
            pass
        raise ValueError(f"{fname} is not a supported subtitle file.")


gifmake_args = argparse.ArgumentParser()
time_group = gifmake_args.add_argument_group("Timing options")
start_group = time_group.add_mutually_exclusive_group(required=True)
start_group.add_argument("-ss", help="Start reading at %(metavar)s.", metavar="SS")
sub_dep_doc = """
    This requires parsing the subtitle file and depends on the srt and ass libraries for SRT and ASS files, respectively.
    To find the index of a line in an SRT file, run fgrep --before-context 3
    "search string" subs.srt. To find the index of a line in an ASS file, open
    it in Aegisub.
"""
start_group.add_argument(
    "--sub-line-start",
    help=f"Start reading at the beginning of the N:th line of the subtitle file. {sub_dep_doc}",
    type=int,
    default=None,
    metavar="N",
)
stop_group = time_group.add_mutually_exclusive_group(required=True)
stop_group.add_argument(
    "-to",
    help="Read up to %(metavar)s. Mutually exclusive with -t and --sub-line-end.",
    metavar="TO",
)
stop_group.add_argument(
    "-t",
    help="Read for %(metavar)s. Mutually exclusive with -to and --sub-line-end.",
    metavar="T",
)
stop_group.add_argument(
    "--sub-line-end",
    help=f"Stop reading from at the end of the N:th subtitle line. Mutually exclusive with -t and -to. {sub_dep_doc}",
    default=None,
    type=int,
    metavar="N",
)
sub_group = gifmake_args.add_argument_group(
    "Subtitle options",
    """
    Options for hardsubbing the gif.
    Hardsubbing uses the subtitles and ass filters and requires an ffmpeg compiled with --enable-libass.
    """,
)
sub_group.add_argument(
    "--sub-file",
    help="""Load subtitles from %(metavar)s.
    """,
    default=None,
    metavar="SUBFILE",
)
sub_group.add_argument(
    "--no-sub",
    help="Do NOT hardsub the gif even though --sub-file was passed. The use case for this is to use a subtitle file purely for timing with --sub-line-start and --sub-line-end",
    action="store_true",
)
sub_group.add_argument(
    "--sub-style",
    help="Use the %(metavar)s ASS style for SRT subtitles. Has no effect for ASS subtitles. Default: %(default)s.",
    default="Fontsize=24,Outline=2",
    metavar="STYLE",
)
sub_group.add_argument(
    "--sub-lead-in",
    help="""
    Allow for %(metavar)s ms of lead-in. Increase this if there are extraneous
    frames at the beginning of the gif.
    Default: %(default)s.
    """,
    default=80,
    type=int,
    metavar="T",
)
filter_group = gifmake_args.add_mutually_exclusive_group()
filter_group.add_argument(
    "--width",
    "-w",
    help="Scale to %(metavar)s px wide. Implied if -f is not set. Default: %(default)s.",
    default=320,
    metavar="W",
)
vf_out = "[vf_out]"
filter_group.add_argument(
    "--filters",
    "-f",
    help=f"An ffmpeg filter graph.  Mutually exclusive with -w. The filtergraph should output to the link {vf_out}; this is appended if not already present.",
)
gifmake_args.add_argument(
    "--rate", "-r", help="Output frame rate. Default: %(default)s.", default=15
)
gifmake_args.add_argument("--palette-filters", "-pf", help="Palette filters.")
gifmake_args.add_argument(
    "--new-palette",
    "-pn",
    help="Force regeneration of the palette.",
    action="store_true",
)
log_group = gifmake_args.add_argument_group("Logging options")
log_group.add_argument(
    "-v",
    "--verbose",
    help="Verbose mode. Prints extra information. Not mutually exclusive with -q, which suppresses ffmpeg output.",
    action="store_true",
)
log_group.add_argument(
    "-q",
    "--quiet",
    help="Quiet mode. Passes -hide_banner -loglevel warning to ffmpeg. Not mutually exclusive with -v.",
    action="store_true",
)
gifmake_args.add_argument("input")
gifmake_args.add_argument("output")

args = gifmake_args.parse_args()

if (args.sub_line_start or args.sub_line_end) and not args.sub_file:
    sys.exit("error: passing --sub-line-start or --sub-line-end requires --sub-file")

if args.verbose:
    logger = print
else:
    logger = lambda x: None

palette_path = pathlib.Path(tempfile.gettempdir()) / pathlib.Path(
    args.input
).with_suffix(".palette.png")

ffmpeg_args = []
ffmpeg_args += ["-stats"]
if args.quiet:
    ffmpeg_args += ["-hide_banner", "-loglevel", "warning"]

if args.ss:
    start_time = args.ss
elif args.sub_line_start:
    times = get_nth_sub_line(args.sub_file, args.sub_line_start)
    lead_in = timedelta(microseconds=args.sub_lead_in * 1e3)
    start_time = str(times[0] + lead_in)

ffmpeg_args += ["-ss", start_time, "-copyts"]
if args.to:
    ffmpeg_args += ["-to", args.to]
elif args.t:
    ffmpeg_args += ["-t", args.t]
elif args.sub_line_end:
    times = get_nth_sub_line(args.sub_file, args.sub_line_end)
    ffmpeg_args += ["-to", str(times[1])]
ffmpeg_args += ["-i", args.input]

# -r needs to be an output argument to not mess up seeking!
ffmpeg_output_args = ["-r", str(args.rate)]
if args.sub_file is not None:
    # to sync subtitles we have to -copyts and seek twice, see
    # https://trac.ffmpeg.org/wiki/HowToBurnSubtitlesIntoVideo
    ffmpeg_output_args += ["-ss", start_time]

if args.width:
    args.filters = "[0:v] scale=%s:-1:flags=lanczos" % args.width

if args.palette_filters:
    palette_filtergraph = "%s, palettegen" % args.palette_filters
else:
    palette_filtergraph = "%s, palettegen" % args.filters

if args.sub_file is not None:
    sub_fmt = determine_sub_format(args.sub_file)
    if sub_fmt == SubFormat.SRT:
        sub_filter = f"subtitles={args.sub_file}:force_style='{args.sub_style}'"
    elif sub_fmt == SubFormat.ASS:
        sub_filter = f"ass={args.sub_file}"
else:
    sub_filter = "copy"

if not args.filters.endswith(vf_out):
    args.filters += vf_out

gif_filters = [
    f"{args.filters}",
    f"{vf_out} {sub_filter} [sub_out]",
    "[sub_out][1:v] paletteuse",
]
gif_filtergraph = "; ".join(gif_filters)

palette_cmd = (
    ["ffmpeg"] + ffmpeg_args + ["-lavfi", palette_filtergraph, "-y", str(palette_path)]
)
if not palette_path.exists() or args.new_palette:
    logger("Generating palette at %s" % palette_path)
    logger(subprocess.list2cmdline(palette_cmd))
    palette_gen_status = subprocess.call(palette_cmd)
    if not palette_gen_status:
        logger("Successfully generated palette.")
    else:
        sys.exit("Palette generation failed.")
else:
    logger(
        "Reusing palette from %s, last modified %s."
        % (palette_path, format_mtime(palette_path.stat().st_mtime))
    )

logger("Encoding gif to %s" % args.output)
encode_cmd = (
    ["ffmpeg"]
    + ffmpeg_args
    + ["-i", str(palette_path)]
    + ffmpeg_output_args
    + ["-lavfi", gif_filtergraph]
    + ["-y", args.output]
)
logger(subprocess.list2cmdline(encode_cmd))
encode_status = subprocess.call(encode_cmd)
if not encode_status:
    logger("Encode successful.")

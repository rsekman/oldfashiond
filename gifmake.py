#!/usr/bin/python

import argparse, subprocess, pathlib, tempfile, sys
from datetime import datetime

try:
    import humanfriendly

    def format_mtime(mtime):
        now = datetime.now()
        mtime = datetime.fromtimestamp(mtime)
        return humanfriendly.format_timespan(now - mtime) + " ago"


except ModuleNotFoundError:

    def format_mtime(mtime):
        # Format datetime according to current locale
        return datetime.fromtimestamp().strftime("%c%")


gifmake_args = argparse.ArgumentParser()
gifmake_args.add_argument("-ss", help="Start timestamp.", required=True)
stop_group = gifmake_args.add_mutually_exclusive_group(required=True)
stop_group.add_argument("-to", help="Read up to this timestamp.")
stop_group.add_argument("-t", help="Read for this duration.")
filter_group = gifmake_args.add_mutually_exclusive_group()
filter_group.add_argument(
    "--width",
    "-w",
    help="Scale to %(metavar)s px wide. Implied if -f is not set, with default %(default)s.",
    default=320,
    metavar="W",
)
filter_group.add_argument("--filters", "-f", help="An ffmpeg filter graph.")
gifmake_args.add_argument(
    "--rate", "-r", help="Frame rate (default: %(default)s).", default=15
)
gifmake_args.add_argument("--palette-filters", "-pf", help="Palette filters.")
gifmake_args.add_argument(
    "--new-palette",
    "-pn",
    help="Force regeneration of the palette.",
    action="store_true",
)
gifmake_args.add_argument(
    "-v",
    "--verbose",
    help="Verbose mode. Prints extra information. Not mutually exclusive with -q, which suppresses ffmpeg output.",
    action="store_true",
)
gifmake_args.add_argument(
    "-q",
    "--quiet",
    help="Quiet mode. Passes -hide_banner -loglevel warning to ffmpeg. Not mutually exclusive with -v.",
    action="store_true",
)
gifmake_args.add_argument("input")
gifmake_args.add_argument("output")

args = gifmake_args.parse_args()
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
ffmpeg_args += ["-ss", args.ss, "-r", str(args.rate)]
if args.to:
    ffmpeg_args += ["-to", args.to]
else:
    ffmpeg_args += ["-t", args.t]
ffmpeg_args += ["-i", args.input]

if args.width:
    args.filters = "scale=%s:-1:flags=lanczos" % args.width

if args.palette_filters:
    palette_filtergraph = "%s, palettegen" % args.palette_filters
else:
    palette_filtergraph = "%s, palettegen" % args.filters
gif_filtergraph = "%s [x]; [x][1:v] paletteuse" % args.filters

if not palette_path.exists() or args.new_palette:
    logger("Generating palette at %s" % palette_path)
    palette_gen_status = subprocess.call(
        ["ffmpeg"]
        + ffmpeg_args
        + ["-lavfi", palette_filtergraph, "-y", str(palette_path)]
    )
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
encode_status = subprocess.call(
    ["ffmpeg"]
    + ffmpeg_args
    + ["-i", str(palette_path)]
    + ["-lavfi", gif_filtergraph, "-y", args.output]
)
if not encode_status:
    logger("Encode successful.")

#!/usr/bin/python

import sys
import subprocess

from datetime import datetime, timedelta
from os import close, unlink
from pathlib import Path
from tempfile import mkstemp, gettempdir

if __name__ != "__main__":
    sys.exit()


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


from .args import argparser, vf_out
from .subs import SubFormat, determine_sub_format, get_nth_sub_line

args = argparser.parse_args()

if (args.sub_line_start or args.sub_line_end) and not args.sub_file:
    sys.exit("error: passing --sub-line-start or --sub-line-end requires --sub-file")

if args.verbose:

    def logger(msg):
        print(msg)

else:

    def logger(msg):
        pass


palette_path = Path(gettempdir()) / Path(args.input).with_suffix(".palette.png").name

ffmpeg_args = []
ffmpeg_args += ["-stats"]
quiet_args = ["-hide_banner", "-loglevel", "warning"]
if args.quiet:
    ffmpeg_args += quiet_args

if args.ss:
    start_time = args.ss
elif args.sub_line_start:
    times = get_nth_sub_line(args.sub_file, args.sub_line_start)
    lead_in = timedelta(microseconds=args.sub_lead_in * 1e3)
    start_time = str(times[0] + lead_in)

ffmpeg_args += ["-ss", start_time, "-copyts"]
if args.to:
    stop_args = ["-to", args.to]
elif args.t:
    stop_args = ["-t", args.t]
elif args.sub_line_end:
    times = get_nth_sub_line(args.sub_file, args.sub_line_end)
    stop_args = ["-to", str(times[1])]
ffmpeg_args += stop_args
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
elif args.sub_index is not None:
    # Naively using filename='{args.input}':si={args.sub_index} in the
    # filtergraph can be extremely slow as this makes ffmpeg demux the entire
    # input file, when we only need a small portion of it.
    (sub_tmp_f, sub_tmp_fname) = mkstemp(suffix=".mkv")
    close(sub_tmp_f)
    demux_cmd = ["ffmpeg", "-stats"]
    if args.quiet:
        demux_cmd += quiet_args
    demux_cmd += ["-ss", start_time, "-i", args.input]
    demux_cmd += stop_args
    demux_cmd += [
        "-map",
        f"0:{args.sub_index}",
        "-map",
        "0:t",
        "-c",
        "copy",
        "-y",
        sub_tmp_fname,
    ]
    sub_filter = f"subtitles={sub_tmp_fname}:si=0"
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

if args.sub_index is not None:
    logger("Demuxing subtitles")
    logger(subprocess.list2cmdline(demux_cmd))
    subprocess.call(demux_cmd)

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
if args.sub_index is not None:
    logger("Deleting demuxed subtitles.")
    try:
        unlink(sub_tmp_fname)
    except Exception:
        pass
if not encode_status:
    logger("Encode successful.")

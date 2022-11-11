from argparse import ArgumentParser

argparser = ArgumentParser()
time_group = argparser.add_argument_group(
    "Timing options",
    """
    oldfashiond accepts -ss, -t, -to with the same semantics as ffmpeg.  It can
    also determine these from a range of lines in a subtitle file.  This
    requires parsing the subtitle file and depends on the srt and ass libraries
    for SRT and ASS files, respectively.  To find the index of a line in an SRT
    file, run fgrep --before-context 3 "search string" subs.srt. To find the
    index of a line in an ASS file, open it in Aegisub.
""",
)
start_group = time_group.add_mutually_exclusive_group(required=True)
start_group.add_argument("-ss", help="Start reading at %(metavar)s.", metavar="SS")
start_group.add_argument(
    "--sub-line-start",
    help="Start reading at the beginning of the N:th line of the subtitle file.",
    type=int,
    default=None,
    metavar="N",
)
stop_group = time_group.add_mutually_exclusive_group(required=True)
stop_group.add_argument(
    "-to",
    help="Read up to %(metavar)s.",
    metavar="TO",
)
stop_group.add_argument(
    "-t",
    help="Read for %(metavar)s ",
    metavar="T",
)
stop_group.add_argument(
    "--sub-line-end",
    help="Stop reading from at the end of the N:th subtitle line.",
    default=None,
    type=int,
    metavar="N",
)
sub_group = argparser.add_argument_group(
    "Subtitle options",
    """
    Options for hardsubbing the gif.
    Hardsubbing uses the subtitles and ass filters and requires an ffmpeg
    compiled with --enable-libass.
    """,
)
sub_source_group = sub_group.add_mutually_exclusive_group()
sub_source_group.add_argument(
    "--sub-file",
    help="""Load subtitles from %(metavar)s.
    """,
    default=None,
    metavar="SUBFILE",
)
sub_source_group.add_argument(
    "--sub-index",
    help="""
    Hardsub the gif using the embedded subtitles with index %(metavar)s.
    Not compatible with subtitle line-based seeking; -ss and (-t | -to) must be
    used.
    (
        To regain this functionality, demux embedded subtitles:
        ffmpeg -ss BEGIN -i INPUT -to END -copyts -map 0:N subs.srt.
        Passing -ss and -to saves time by not demuxing the entire file, which
        could mean reading several GiB from disk.
    )
    """,
    default=None,
    metavar="INDEX",
)
sub_group.add_argument(
    "--no-sub",
    help="""
    Do NOT hardsub the gif even though --sub-file was passed. The use case for
    this is to use a subtitle file purely for timing with --sub-line-start and
    --sub-line-end
    """,
    action="store_true",
)
sub_group.add_argument(
    "--sub-style",
    help="""
    Use the %(metavar)s ASS style for SRT subtitles. Has no effect for ASS
    subtitles. Default: %(default)s.
    """,
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
filter_group = argparser.add_argument_group()
filter_group.add_argument(
    "--width",
    "-w",
    help="""
    Scale to %(metavar)s px wide. Default: %(default)s.
    Pass any non-positive value to skip scaling.
    """,
    default=320,
    type=int,
    metavar="W",
)
vf_out = "[vf_out]"
filter_group.add_argument(
    "--filters",
    "-f",
    help=f"""
    An ffmpeg filter graph. The filtergraph should
    output to the link {vf_out}; this is appended if not already present.
    """,
    default=f"copy"
)
argparser.add_argument(
    "--rate", "-r", help="Output frame rate. Default: %(default)s.", default=15
)
argparser.add_argument("--palette-filters", "-pf", help="Palette filters.")
argparser.add_argument(
    "--new-palette",
    "-pn",
    help="Force regeneration of the palette.",
    action="store_true",
)
log_group = argparser.add_argument_group("Logging options")
log_group.add_argument(
    "-v",
    "--verbose",
    help="""
    Verbose mode. Prints extra information. Not mutually exclusive with -q,
    which suppresses ffmpeg output.
    """,
    action="store_true",
)
log_group.add_argument(
    "-q",
    "--quiet",
    help="""
    Quiet mode. Passes -hide_banner -loglevel warning to ffmpeg. Not mutually
    exclusive with -v.
    """,
    action="store_true",
)
argparser.add_argument("input")
argparser.add_argument("output")

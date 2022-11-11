oldfashiond
===================

Make gifs from any video format `ffmpeg` can handle using two-pass encoding.

Essentially a convenience wrapper around the following calls,

    ffmpeg -i $input -vf "$filters,palettegen" -y $palette
    ffmpeg -i $input -i $palette -lavfi "$filters [x]; [x][1:v] paletteuse" -y $output

with support for common arguments. Run with `-h` for details.

## Filter sequence ##

`oldfashiond` runs three filter stages in the following order
    1. user-defined filters: an arbitrary `ffmpeg` filtergraph passed with `--filters`
    2. scaling: to the width passed with `--width`
        Skipped (replaced with the identify filter) if the value is non-positive.
    3. subtitles: as appropriate for any subtitle options passed

1 and 3 are the identity filter (`copy`) if the corresponding options are not
present.

## Name ##

Gifs are an old-fashioned format and go on tumblr, an old-fashioned website; and Old fashion**e**d, the cocktail, is served in a tumbl**e**r.

## Dependencies: ##
 * Python 3
 * `ffmpeg` with support for the `palettegen` and `paletteuse` filters (>= 2.6)

### Optional dependencies ###
  * `humanfriendly`: for some nicer log messages
  * an `ffmpeg` compiled with `--enable-libass`: to hardsub gifs
  * `ass` or `srt`: to automatically determine start and stop times from an ASS or SRT subtitle file, respectively

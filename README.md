oldfashiond
===================

Make gifs from any video format `ffmpeg` can handle using two-pass encoding.

Essentially a convenience wrapper around the following calls,

    ffmpeg -i $input -vf "$filters,palettegen" -y $palette
    ffmpeg -i $input -i $palette -lavfi "$filters [x]; [x][1:v] paletteuse" -y $output

with support for common arguments. Run with `-h` for details.

## Name ##

Gifs are an old-fashioned format and go on tumblr, an old-fashioned website; and Old fashion**e**d, the cocktail, is served in a tumbl**e**r.

## Dependencies: ##
 * Python 3
 * `ffmpeg` with support for the `palettegen` and `paletteuse` filters (>= 2.6)

### Optional dependencies ###
  * `humanfriendly`: for some nicer log messages
  * an `ffmpeg` compiled with `--enable-libass`: to hardsub gifs
  * `ass` or `srt`: to automatically determine start and stop times from an ASS or SRT subtitle file, respectively

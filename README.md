gifmake.py
===================

Make gifs from any video format `ffmpeg` can handle using two-pass encoding.

Essentially a convenience wrapper around the following syscalls,

    ffmpeg -i $input -vf "$filters,palettegen" -y $palette
    ffmpeg -i $input -i $palette -lavfi "$filters [x]; [x][1:v] paletteuse" -y $output

with support for common arguments. Run with `-h` for details.

## Dependencies: ##
 * Python 3
 * `ffmpeg` with support for the `palettegen` and `paletteuse` filters (>= 2.6)

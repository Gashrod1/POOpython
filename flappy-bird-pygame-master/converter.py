MS_PER_SEC = 1000.0


def frames_to_msec(frames, fps) -> float:
    """Convert frames to milliseconds at the specified framerate.

    Arguments:
    frames: How many frames to convert to milliseconds.
    fps: The framerate to use for conversion.  Default: FPS.
    """
    return MS_PER_SEC * frames / fps


def msec_to_frames(milliseconds, fps) -> float:
    """Convert milliseconds to frames at the specified framerate.

    Arguments:
    milliseconds: How many milliseconds to convert to frames.
    fps: The framerate to use for conversion.  Default: FPS.
    """
    return fps * milliseconds / MS_PER_SEC

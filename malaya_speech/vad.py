from malaya_speech.utils.astype import to_byte, to_ndarray
from malaya_speech.model.interface import FRAME
import numpy as np
from herpetologist import check_type
from typing import List, Tuple


class VAD:
    __name__ = 'vad'


class WEBRTC(VAD):
    def __init__(self, vad, sample_rate = 16000, minimum_amplitude: int = 100):
        self.vad = vad
        self.sample_rate = sample_rate
        self.minimum_amplitude = minimum_amplitude

        self.minimum_sample = 30
        self.maximum_sample = 30

    def is_speech(self, frame):

        if isinstance(frame, FRAME):
            frame = frame.array

        frame = to_byte(frame)

        minimum = np.mean(np.abs(to_ndarray(frame)))

        return (
            self.vad.is_speech(frame, self.sample_rate)
            and minimum >= self.minimum_amplitude
        )

    def __call__(self, frame):
        return self.is_speech(frame)


@check_type
def webrtc(
    aggressiveness: int = 3, sample_rate = 16000, minimum_amplitude: int = 100
):
    try:
        import webrtcvad
    except:
        raise ValueError(
            'webrtcvad not installed. Please install it by `pip install webrtcvad` and try again.'
        )

    vad = webrtcvad.Vad(aggressiveness)
    return WEBRTC(vad, sample_rate, minimum_amplitude)


def group_vad(frames: List[Tuple[FRAME, bool]]):
    results, result, last = [], [], None

    for frame in frames:
        if last is None:
            last = frame[1]
            result.append(frame[0])
        elif last == frame[1]:
            result.append(frame[0])
        else:
            a, duration = [], 0
            for r in result:
                a.extend(r.array)
                duration += r.duration
            results.append((FRAME(a, result[0].timestamp, duration), last))
            result = [frame[0]]
            last = frame[1]

    if len(result):
        a, duration = [], 0
        for r in result:
            a.extend(r.array)
            duration += r.duration
        results.append((FRAME(a, result[0].timestamp, duration), last))
    return results

from itertools import cycle
from pysndfx import AudioEffectsChain
from scipy.special import expit
from glob import glob
import random
import pickle


def get_files(files):
    files = list(set(files))
    random.shuffle(files)
    return cycle(files)


def get_ambient(file):
    with open(file, 'rb') as fopen:
        ambient = pickle.load(fopen)
    return ambient


def sox_reverb(
    y, reverberance = 1, hf_damping = 1, room_scale = 1, stereo_depth = 1
):
    apply_audio_effects = AudioEffectsChain().reverb(
        reverberance = reverberance,
        hf_damping = hf_damping,
        room_scale = room_scale,
        stereo_depth = stereo_depth,
        pre_delay = 20,
        wet_gain = 0,
        wet_only = False,
    )
    y_enhanced = apply_audio_effects(y)

    return y_enhanced


def sox_augment_low(
    y,
    min_bass_gain = 5,
    reverberance = 1,
    hf_damping = 1,
    room_scale = 1,
    stereo_depth = 1,
    negate = 1,
):
    if negate:
        min_bass_gain = -min_bass_gain
    apply_audio_effects = (
        AudioEffectsChain()
        .lowshelf(gain = min_bass_gain, frequency = 300, slope = 0.1)
        .reverb(
            reverberance = reverberance,
            hf_damping = hf_damping,
            room_scale = room_scale,
            stereo_depth = stereo_depth,
            pre_delay = 20,
            wet_gain = 0,
            wet_only = False,
        )
    )
    y_enhanced = apply_audio_effects(y)

    return y_enhanced


def sox_augment_high(
    y,
    min_bass_gain = 5,
    reverberance = 1,
    hf_damping = 1,
    room_scale = 1,
    stereo_depth = 1,
    negate = 1,
):
    if negate:
        min_bass_gain = -min_bass_gain
    apply_audio_effects = (
        AudioEffectsChain()
        .highshelf(
            gain = -min_bass_gain * (1 - expit(np.max(y))),
            frequency = 300,
            slope = 0.1,
        )
        .reverb(
            reverberance = reverberance,
            hf_damping = hf_damping,
            room_scale = room_scale,
            stereo_depth = stereo_depth,
            pre_delay = 20,
            wet_gain = 0,
            wet_only = False,
        )
    )
    y_enhanced = apply_audio_effects(y)

    return y_enhanced


def sox_augment_combine(
    y,
    min_bass_gain_low = 5,
    min_bass_gain_high = 5,
    reverberance = 1,
    hf_damping = 1,
    room_scale = 1,
    stereo_depth = 1,
):

    apply_audio_effects = (
        AudioEffectsChain()
        .lowshelf(gain = min_bass_gain_low, frequency = 300, slope = 0.1)
        .highshelf(gain = -min_bass_gain_high, frequency = 300, slope = 0.1)
        .reverb(
            reverberance = reverberance,
            hf_damping = hf_damping,
            room_scale = room_scale,
            stereo_depth = stereo_depth,
            pre_delay = 20,
            wet_gain = 0,
            wet_only = False,
        )
    )
    y_enhanced = apply_audio_effects(y)

    return y_enhanced


def fftnoise(f):
    f = np.array(f, dtype = 'complex')
    Np = (len(f) - 1) // 2
    phases = np.random.rand(Np) * 2 * np.pi
    phases = np.cos(phases) + 1j * np.sin(phases)
    f[1 : Np + 1] *= phases
    f[-1 : -1 - Np : -1] = np.conj(f[1 : Np + 1])
    return np.fft.ifft(f).real


def add_band_limited_noise(
    sample, min_freq = 200, max_freq = 24000, samplerate = 16000
):
    freqs = np.abs(np.fft.fftfreq(len(sample), 1 / samplerate))
    f = np.zeros(len(sample))
    idx = np.where(np.logical_and(freqs >= min_freq, freqs <= max_freq))[0]
    f[idx] = 1
    return sample + fftnoise(f)


def add_uniform_noise(sample, power = 0.01):
    y_noise = sample.copy()
    noise_amp = power * np.random.uniform() * np.amax(y_noise)
    return y_noise.astype('float64') + noise_amp * np.random.normal(
        size = y_noise.shape[0]
    )


def random_sampling(sample, sr, length = 500):
    sr = int(sr / 1000)
    up = len(sample) - (sr * length)
    if up < 1:
        r = 0
    else:
        r = np.random.randint(0, up)
    return sample[r : r + sr * length]


def add_noise(sample, noise, random_sample = True, factor = 0.1):
    y_noise = sample.copy()
    if len(y_noise) > len(noise):
        noise = np.tile(noise, int(np.ceil(len(y_noise) / len(noise))))
    else:
        if random_sample:
            noise = noise[np.random.randint(0, len(noise) - len(y_noise) + 1) :]
    return y_noise + noise[: len(y_noise)] * factor


def read_flac(file):
    data, old_samplerate = sf.read(file)
    if len(data.shape) == 2:
        data = data[:, 0]
    return data, old_samplerate


def read_wav(file):
    y, sr = librosa.load(file, sr = 22050)
    return y, sr


def read_file(file):
    if '.flac' in file:
        y, sr = read_flac(file)
    if '.wav' in file:
        y, sr = read_wav(file)
    return y, sr


def combine_speakers(files, n = 5):
    w_samples = random.sample(files, n)
    y = [w_samples[0]]
    left = w_samples[0]
    for i in range(1, n):

        right = w_samples[i]

        overlap = random.uniform(0.01, 1.5)
        left_len = int(overlap * len(left))

        padded_right = np.pad(right, (left_len, 0))

        if len(left) > len(padded_right):
            padded_right = np.pad(
                padded_right, (0, len(left) - len(padded_right))
            )
        else:
            left = np.pad(left, (0, len(padded_right) - len(left)))

        y.append(padded_right)
        left = left + padded_right
    return left, y
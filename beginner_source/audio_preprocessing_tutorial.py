"""
Torchaudio Tutorial
===================

PyTorch is an open source deep learning platform that provides a
seamless path from research prototyping to production deployment with
GPU support.

Significant effort in solving machine learning problems goes into data
preparation. Torchaudio leverages PyTorch’s GPU support, and provides
many tools to make data loading easy and more readable. In this
tutorial, we will see how to load and preprocess data from a simple
dataset.

For this tutorial, please make sure the ``matplotlib`` package is
installed for easier visualization.

"""

import torch
import torchaudio
import matplotlib.pyplot as plt


######################################################################
# Opening a dataset
# -----------------
# 


######################################################################
# Torchaudio supports loading sound files in the wav and mp3 format.
# 

filename = "assets/steam-train-whistle-daniel_simon-converted-from-mp3.wav"
waveform, frequency = torchaudio.load(filename)

print("Shape of waveform: {}".format(waveform.size()))
print("Frequency of waveform: {}".format(frequency))

plt.figure()
plt.plot(waveform.transpose(0,1).numpy())


######################################################################
# Transformations
# ---------------
# 
# Torchaudio supports a growing list of
# `transformations <https://pytorch.org/audio/transforms.html>`_.
# 
# -  **Scale**: Scale audio tensor from a 16-bit integer (represented as a
#    FloatTensor) to a floating point number between -1.0 and 1.0. Note
#    the 16-bit number is called the “bit depth” or “precision”, not to be
#    confused with “bit rate”.
# -  **PadTrim**: PadTrim a 2d-Tensor
# -  **Downmix**: Downmix any stereo signals to mono.
# -  **LC2CL**: Permute a 2d tensor from samples (n x c) to (c x n).
# -  **Resample**: Resample the signal to a different frequency.
# -  **Spectrogram**: Create a spectrogram from a raw audio signal
# -  **MelScale**: This turns a normal STFT into a mel frequency STFT,
#    using a conversion matrix. This uses triangular filter banks.
# -  **SpectrogramToDB**: This turns a spectrogram from the
#    power/amplitude scale to the decibel scale.
# -  **MFCC**: Create the Mel-frequency cepstrum coefficients from an
#    audio signal
# -  **MelSpectrogram**: Create MEL Spectrograms from a raw audio signal
#    using the STFT function in PyTorch.
# -  **BLC2CBL**: Permute a 3d tensor from Bands x Sample length x
#    Channels to Channels x Bands x Samples length.
# -  **MuLawEncoding**: Encode signal based on mu-law companding.
# -  **MuLawExpanding**: Decode mu-law encoded signal.
# 
# Since all transforms are nn.Modules or jit.ScriptModules, they can be
# used as part of a neural network at any point.
# 


######################################################################
# To start, we can look at the log of the spectrogram on a log scale.
# 

specgram = torchaudio.transforms.Spectrogram()(waveform)

print("Shape of spectrogram: {}".format(specgram.size()))

plt.figure()
plt.imshow(specgram.log2().transpose(1,2)[0,:,:].numpy(), cmap='gray')


######################################################################
# Or we can look at the Mel Spectrogram on a log scale.
# 

specgram = torchaudio.transforms.MelSpectrogram()(waveform)

print("Shape of spectrogram: {}".format(specgram.size()))

plt.figure()
p = plt.imshow(specgram.log2().transpose(1,2)[0,:,:].detach().numpy(), cmap='gray')


######################################################################
# We can resample the signal, one channel at a time.
# 

new_frequency = frequency/10

# Since Resample applies to a single channel, we resample first channel here
channel = 0
transformed = torchaudio.transforms.Resample(frequency, new_frequency)(waveform[channel,:].view(1,-1))

print("Shape of transformed waveform: {}".format(transformed.size()))

plt.figure()
plt.plot(transformed[0,:].numpy())


######################################################################
# Or we can first convert the stereo to mono, and resample, using
# composition.
# 

transformed = torchaudio.transforms.Compose([
    torchaudio.transforms.LC2CL(),
    torchaudio.transforms.DownmixMono(),
    torchaudio.transforms.LC2CL(),
    torchaudio.transforms.Resample(frequency, new_frequency)
])(waveform)

print("Shape of transformed waveform: {}".format(transformed.size()))

plt.figure()
plt.plot(transformed[0,:].numpy())


######################################################################
# As another example of transformations, we can encode the signal based on
# the Mu-Law companding. But to do so, we need the signal to be between -1
# and 1. Since the tensor is just a regular PyTorch tensor, we can apply
# standard operators on it.
# 

# Let's check if the tensor is in the interval [-1,1]
print("Min of waveform: {}\nMax of waveform: {}\nMean of waveform: {}".format(waveform.min(), waveform.max(), waveform.mean()))


######################################################################
# Since the waveform is already between -1 and 1, we do not need to
# normalize it.
# 

def normalize(tensor):
    # Subtract the mean, and scale to the interval [-1,1]
    tensor_minusmean = tensor - tensor.mean()
    return tensor_minusmean/tensor_minusmean.abs().max()

# Let's normalize to the full interval [-1,1]
# waveform = normalize(waveform)


######################################################################
# Let’s apply encode the waveform.
# 

transformed = torchaudio.transforms.MuLawEncoding()(waveform)

print("Shape of transformed waveform: {}".format(transformed.size()))

plt.figure()
plt.plot(transformed[0,:].numpy())


######################################################################
# And now decode.
# 

reconstructed = torchaudio.transforms.MuLawExpanding()(transformed)

print("Shape of recovered waveform: {}".format(reconstructed.size()))

plt.figure()
plt.plot(reconstructed[0,:].numpy())


######################################################################
# We can finally compare the original waveform with its reconstructed
# version.
# 

# Compute median relative difference
err = ((waveform-reconstructed).abs() / waveform.abs()).median()

print("Median relative difference between original and MuLaw reconstucted signals: {:.2%}".format(err))


######################################################################
# Migrating to Torchaudio from Kaldi
# ----------------------------------
# 
# Users may be familiar with
# `Kaldi <http://github.com/kaldi-asr/kaldi>`_, a toolkit for speech
# recognition. Torchaudio offers compatibility with it in
# ``torchaudio.kaldi_io``. It can indeed read from kaldi scp, or ark file
# or streams with:
# 
# -  read_vec_int_ark
# -  read_vec_flt_scp
# -  read_vec_flt_arkfile/stream
# -  read_mat_scp
# -  read_mat_ark
# 
# Torchaudio provides Kaldi-compatible transforms for ``spectrogram`` and
# ``fbank`` with the benefit of GPU support, see
# `here <compliance.kaldi.html>`__ for more information.
# 

n_fft = 400.0
frame_length = n_fft / frequency * 1000.0
frame_shift = frame_length / 2.0

params = {
    "channel": 0,
    "dither": 0.0,
    "window_type": "hanning",
    "frame_length": frame_length,
    "frame_shift": frame_shift,
    "remove_dc_offset": False,
    "round_to_power_of_two": False,
    "sample_frequency": frequency,
}

specgram = torchaudio.compliance.kaldi.spectrogram(waveform, **params)

print("Shape of spectrogram: {}".format(specgram.size()))

plt.figure()
plt.imshow(specgram.transpose(0,1).numpy(), cmap='gray')


######################################################################
# We also support computing the filterbank features from raw audio signal,
# matching Kaldi’s implementation.
# 

fbank = torchaudio.compliance.kaldi.fbank(waveform, **params)

print("Shape of fbank: {}".format(fbank.size()))

plt.figure()
plt.imshow(fbank.transpose(0,1).numpy(), cmap='gray')


######################################################################
# Conclusion
# ----------
# 
# We used an example sound signal to illustrate how to open an audio file
# or using Torchaudio, and how to pre-process and transform an audio
# signal. Given that Torchaudio is built on PyTorch, these techniques can
# be used as building blocks for more advanced audio applications, such as
# speech recognition, while leveraging GPUs.
# 

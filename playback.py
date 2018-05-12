import mido
import pyaudio
import struct
import math
import numpy as np
CHANNELS = 2
RATE = 44100
INPUT_BLOCK_TIME = 0.05
INPUT_FRAMES_PER_BLOCK = int(RATE*INPUT_BLOCK_TIME)
SHORT_SIZE = 32768.0
THRESHOLD = 0.010
FORMAT = pyaudio.paInt16
numSounds = 0
stream = None
p = None
def to_array(block):
    if (block == None):
        return []
    count = len(block)/2
    fmt = "%dh"%(count)
    return np.array(list(struct.unpack(fmt, block)))/SHORT_SIZE
def midi_notes(filename):
    daFile = mido.MidiFile(filename)
    for msg in daFile.play():
        yield msg

def amplitude(soundArray):
    return np.linalg.norm(soundArray)/len(soundArray)**0.5

def init_pyaudio():
    global p, stream
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=INPUT_FRAMES_PER_BLOCK)
def onSound(soundArray):
    global numSounds
    amp = amplitude(soundArray)
    if (amp > THRESHOLD):
        numSounds += 1
        print("Sound %d %.2f"%(numSounds, amp))

def listen():
    block = None
    try:
        block = stream.read(INPUT_FRAMES_PER_BLOCK)
        onSound(to_array(block))
    except Exception as e:
        print(e)
    
    

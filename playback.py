import mido
import pyaudio
import struct
import math
import numpy as np
import matplotlib.pyplot as plt
import collections
import time
import sys
import threading
from scipy.signal import find_peaks_cwt
import requests
# Constants
CHANNELS = 2
RATE = 44100
INPUT_BLOCK_TIME = 0.0625
INPUT_FRAMES_PER_BLOCK = int(RATE*INPUT_BLOCK_TIME)
SHORT_SIZE = 32768.0
THRESHOLD = 0.05
FORMAT = pyaudio.paInt16
NUM_BLOCKS_AVERAGE = 1
# Graphing Stuff
figure, axes = plt.subplots(3)
x = np.arange(10000)
y = np.random.rand(10000)
li, = axes[0].plot(x, y)
li2, = axes[1].plot(x, y)
li3, = axes[2].plot(x, y)
li4, = axes[2].plot(x, y)

#li5, = axes[3].plot(x, y)
axes[0].set_xlim(0, INPUT_FRAMES_PER_BLOCK)
axes[0].set_ylim(-1, 1)
axes[0].set_title("Signal")
axes[1].set_xlim(0, INPUT_FRAMES_PER_BLOCK)
axes[1].set_ylim(0, 1000)
axes[1].set_title("FFT")
axes[2].set_xlim(0, 1000)
axes[2].set_ylim(0, 1)
axes[2].set_title("Amplitude")
##axes[3].set_xlim(0, 1)
##axes[3].set_ylim(0, 100)
##axes[3].set_title("FFT Amplitude")
figure.tight_layout()
plt.pause(0.01)

def plot_data(soundArray, amplitudes):
    li.set_xdata(np.arange(len(soundArray)))
    li.set_ydata(soundArray)
    dfft = abs(np.fft.rfft(soundArray))
    li2.set_xdata(np.arange(len(dfft))/INPUT_BLOCK_TIME)
    li2.set_ydata(dfft)
    graphWidth = len(amplitudes)
    li3.set_xdata(np.arange(graphWidth))
    li3.set_ydata(np.array(list(amplitudes)))
    li4.set_xdata(np.arange(graphWidth))
    li4.set_ydata([THRESHOLD]*graphWidth)
##    afft = abs(np.fft.rfft(amplitudes))
##    li5.set_xdata(np.arange(len(afft)))
##    li5.set_ydata(afft)
    #arr = find_peaks_cwt(dfft, range(1, 10))
    #li3.set_xdata(np.arange(len(dfft))[arr]/INPUT_BLOCK_TIME)
    #li3.set_ydata(dfft[arr])
    plt.pause(0.001)
def to_array(block):
    if (block == None):
        return []
    count = len(block)/2
    fmt = "%dh"%(count)
    return np.array(list(struct.unpack(fmt, block)))/SHORT_SIZE

def updateSheet(name, error, notesPlayed, time):
    res = requests.get("https://script.google.com/macros/s/AKfycbwRUZXf-CHjRETGzyFs0YcB2BrIMkO-h8Mk_gWlRSniofngQvs/exec", params={"name": name, "error": error, "notes": notesPlayed, "time":time})
def amplitude(soundArray):
    return np.linalg.norm(soundArray)/len(soundArray)**0.5
class Player:
    def __init__(self, filename):
        self.lastNotes = collections.deque(NUM_BLOCKS_AVERAGE*[[0]], NUM_BLOCKS_AVERAGE)
        self.filename = filename
        self.plotCounter = 0
        self.stopped = False
        self.currentAmplitude = 0;
        self.currentTempo = 500000
        self.playSpeed = 1
        self.amplitudes = collections.deque([0]*1000, 1000)
        self.songLength = 1
        self.init_pyaudio()
    def midi_notes(self):
        daFile = mido.MidiFile(self.filename)
        self.songLength = daFile.length
        noteGroups = []
        msgs = []
        for msg in daFile:
            if msg.time > 0:
                things = msgs
                msgs = []
                noteGroups.append(things)
            msgs.append(msg)
        return noteGroups

    def resetSong(self):
        self.notes = self.midi_notes()
        self.error = 0
        self.startTime = time.time()
        self.notesPlayed = 0

    def init_pyaudio(self):
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=INPUT_FRAMES_PER_BLOCK)
        self.port = mido.open_output()
        
    def shouldPlay(self):
        return self.currentAmplitude > THRESHOLD;
    def calculateError(self, noteGroup, playedNotes):
        if (len(playedNotes) == 1):
            return 0
        actual = abs(np.fft.rfft(playedNotes))
        weights = self.expectedFourier(noteGroup, len(actual)) * np.linalg.norm(actual)
        
        return np.linalg.norm(actual-weights)
    def expectedFourier(self, noteGroup, length):
        frequencies = np.array([2 ** ((note.note - 69)/12.0) * 440 for note in noteGroup if note.type == 'note_on'])
        if (len(frequencies) == 0):
            return np.zeros(length)
        weights = [min(abs(i - frequencies*INPUT_BLOCK_TIME))**(-2) for i in range(length)]
        weights = weights/np.linalg.norm(weights)
        return weights

    def songFinished(self):
        err = self.error / self.notesPlayed
        print("Error: %.1f"% err)
        elapsed = time.time() - self.startTime
        print("Time played: %.1f"%(elapsed))
        self.startTime = time.time()
        updateSheet(self.filename, err, self.notesPlayed, np.round(elapsed))
        self.resetSong()
    def run(self):
        while not self.stopped:
            if not self.shouldPlay():
                time.sleep(0.02)
                continue
            if (len(self.notes) == 0):
                self.songFinished()
                time.sleep(0.02)
                continue
            noteGroup = self.notes[0]
            waitTime = noteGroup[0].time
            time.sleep(waitTime)
            newError = self.calculateError(noteGroup, list(self.lastNotes)[0])
            self.error += newError
            for note in noteGroup:
                if note.type in ['note_on']:
                    avgAmplitude = np.mean(np.array(self.amplitudes)[-25:])
                    ve = max(min(int(self.currentAmplitude ** 2 * 2048), 127), 10)
                    noteC = note.copy(velocity=ve)
                    self.port.send(noteC)
                    self.notesPlayed += 1
                elif note.is_meta:
                    if note.type == 'set_tempo':
                        self.currentTempo = note.tempo
                else:
                    self.port.send(note)
            del self.notes[0]
    def stop(self):
        self.stopped = True
        self.songFinished()
    def startThread(self):
        self.t = threading.Thread(target=self.run)
        self.t.start()
    def onSound(self, soundArray):
        avgAmplitude = sum([amplitude(arr) for arr in self.lastNotes])/len(self.lastNotes)
        amp = amplitude(soundArray)
        self.currentAmplitude = amp
        def isNote(soundArray):
            return amplitude(soundArray) > max(avgAmplitude*0.2, THRESHOLD)
        # This block of code is never executed - it was the previous attempt at responding to played notes
        if (isNote(soundArray) and False):
            dfft = abs(np.fft.rfft(soundArray))
            
            freq = np.argmax(dfft)/INPUT_BLOCK_TIME
            #print(freq)
            #print(amp)
            try:
                x = self.notes[0]
            except Exception as e:
                print(e)
                self.resetSong()
                return
            #dfft = abs(np.fft.rfft(soundArray))
            #dfftdiff = (dfft - olddfft)*1.0 / np.linalg.norm(soundArray)
            #olddfft = dfft
            #score = np.linalg.norm(dfftdiff[dfftdiff > 0])
            # Figuring out the "note-ness" of a sound was too hard
            if False:
                for note in x:
                    if note.type in ['note_on']:
                        time.sleep(note.time)
                        noteC = note.copy(velocity=min(int(amp*256*2), 127))
                        self.port.send(noteC)
                        #notesToOff.append(noteC)
                    if note.type in ['note_off']:
                        time.sleep(note.time)
                        self.port.send(note.copy(velocity=min(int(amp*256*2), 127)))
                del self.notes[0]
        # Was used to turn off notes, now superseded by self.run()
        if (avgAmplitude < THRESHOLD):
            pass
    ##        print("Insufficient Amplitude")
    ##        for note in notesToOff:
    ##            n = mido.Message('note_off')
    ##            n.note = note.note
    ##            n.velocity = note.velocity
    ##            n.time = note.time
    ##            n.channel = note.channel
    ##            port.send(n)
    ##        del notesToOff[:]
        self.amplitudes.append(amp)
        if self.plotCounter % math.ceil(0.125/INPUT_BLOCK_TIME) == 0:
            plot_data(soundArray, self.amplitudes)
        self.plotCounter += 1
        self.lastNotes.appendleft(soundArray)
    def listen(self):
        block = self.stream.read(INPUT_FRAMES_PER_BLOCK)
        self.onSound(to_array(block))
   
if __name__ == "__main__":
    try:
        SONG_FNAME = sys.argv[1]
    except:
        SONG_FNAME = "My Dearest.mid"
    p = Player(SONG_FNAME)
    p.init_pyaudio()
    p.resetSong()
    p.startThread()
    while True:
        try:
            p.listen()
        except:
            p.stop()
            break

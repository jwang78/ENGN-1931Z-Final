import pyaudio
import youtube_dl # Requires ffmpeg
import wave
import mido
import numpy as np
import matplotlib.pyplot as plt
import struct
import time
import scipy.signal as signal
from scipy.signal import find_peaks_cwt, argrelextrema
p = pyaudio.PyAudio()
FRAMES_PER_BLOCK = 1000
START_THRESHOLD = FRAMES_PER_BLOCK/25*0
END_THRESHOLD = START_THRESHOLD/5
def download(link):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            # No more temp mp3 file!
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        'outtmpl' : 'a.webm'
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        x = ydl.download([link])
figure, axes = plt.subplots(1)
li, = axes.plot(np.zeros(100), np.zeros(100))
axes.set_xlim(0, 4000)
axes.set_ylim(0, 1000)
def plot_data(array, fft, blockTime):
 
    li.set_xdata(np.arange(len(fft))/blockTime)
    li.set_ydata(fft)
    plt.pause(0.001)
def to_midi(outfname):
    mf = mido.MidiFile()
    track = mido.MidiTrack()
    mf.tracks.append(track)
    wf = wave.open('a.wav', 'rb')
    data = wf.readframes(FRAMES_PER_BLOCK)
    sampleWidth = wf.getsampwidth()
    print("SWIDTH:%d"%sampleWidth)
    frameRate = wf.getframerate()
    #print(sampleWidth)
    fmt = {1:"%db", 2:"<%dh", 4: "%<dl"}[sampleWidth] % (len(data)//sampleWidth)
    def to_array(block):
        if (block == None):
            return []
        arr = np.array(list(struct.unpack(fmt, block)))
        return arr/32768.0
    active_notes = [0]*128
    deltaTime = 0
    defTempo = 500000
    totalTime = 0
    track.append(mido.Message('program_change', program=0, time=0))
    track.append(mido.MetaMessage('set_tempo', tempo=defTempo, time=0))
    expectedLength = len(data)
    while data:
        if (len(data) != expectedLength):
            data = None
            continue
        arr = to_array(data)
        fft = abs(np.fft.rfft(arr))
        #fft *= FRAMES_PER_BLOCK/np.linalg.norm(fft)
        frameTime = FRAMES_PER_BLOCK/frameRate
        
        peaks = argrelextrema(fft, np.greater)[0]/frameTime
        peaks = peaks[peaks > 80]
        peaks = peaks[peaks < 2000]
        for hump in peaks:
            if fft[int(hump*frameTime)] > 0.3 * np.linalg.norm(fft) + START_THRESHOLD:
                midi_index = int(12 * np.log2(hump/440) + 69)
                if active_notes[midi_index] == 0:
                    # Turn on the note
                    #print("Turning on frequency %.2f"%hump)
                    ve = int(min(fft[int(hump*frameTime)]//6, 127))
                    active_notes[midi_index] = ve
                    timeInTicks = int(mido.second2tick(deltaTime, mf.ticks_per_beat, defTempo))
                    track.append(mido.Message('note_on', note=midi_index, velocity=ve, time=timeInTicks))
                    deltaTime = 0
        for i in range(len(active_notes)):
            freq = 2 ** ((i - 69)/12) * 440
            index = int(np.round(freq*frameTime))
            # A previous attempt at discerning the notes in the FT
##            if fft[index] > START_THRESHOLD:
##                if active_notes[i] == 0:
##                    # Turn on the note
##                    print("Turning on frequency %.2f"%freq)
##                    ve = int(min(fft[index]//8, 127))
##                    active_notes[i] = ve
##                    timeInTicks = int(mido.second2tick(deltaTime, mf.ticks_per_beat, defTempo))
##                    # TODO: Amplitude
##                    track.append(mido.Message('note_on', note=i, velocity=ve, time=timeInTicks))
##                    deltaTime = 0
            if fft[index] < 0.1 * np.linalg.norm(fft) + END_THRESHOLD:
                if active_notes[i] != 0:
                    # Turn off the note
                    ve = int(active_notes[i])
                    active_notes[i] = 0
                    
                    timeInTicks = int(mido.second2tick(deltaTime, mf.ticks_per_beat, defTempo))
                    track.append(mido.Message('note_off', note=i, velocity=ve, time=timeInTicks))
                    deltaTime = 0
        deltaTime += frameTime           
        plot_data(arr, fft, frameTime)
        totalTime += frameTime
        # The time in the track
        if (totalTime % 2 < 0.001):
            print("Time elapsed: %.2f"%totalTime)
        #time.sleep(frameTime)
        data = wf.readframes(FRAMES_PER_BLOCK)
    for i in range(len(active_notes)):
        if active_notes[i] != 0:
            ve = active_notes[i]
            timeInTicks = int(mido.second2tick(deltaTime, mf.ticks_per_beat, defTempo))
            track.append(mido.Message('note_off', note=i, velocity=ve, time=timeInTicks))
    print("Finished playing track!")
    mf.save(outfname)
        
        
#download('https://www.youtube.com/watch?v=720z2iPsAkg')
#download('https://www.youtube.com/watch?v=3o_GX-e92mY')
#download('https://www.youtube.com/watch?v=OUvlamJN3nM')
#download('https://www.youtube.com/watch?v=Pi8xsZXibIc')
#download('https://www.youtube.com/watch?v=lsfj6lfiQTA')
#download('https://www.youtube.com/watch?v=kVThp7yTn0I')

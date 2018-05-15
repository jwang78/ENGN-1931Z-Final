import playback
import dl_youtube
import sys

def main():
    try:
        resource = sys.argv[1]
    except:
        print("Missing filename/url")
        exit()
    if "http" in resource:
        if (len(sys.argv) >= 2):
            dl_youtube.download(resource)
            print("To Miding")
            to_midi("out.mid")
            resource = "out.mid"
        else:
            print("Please provide an output file")
            exit()
    p = playback.Player(resource)
    p.resetSong()
    p.startThread()
    while True:
        try:
            p.listen()
        except:
            p.stop()
            break

if __name__ == "__main__":
    main()

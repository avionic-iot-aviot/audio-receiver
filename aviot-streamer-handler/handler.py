import argparse
import os
import datetime
import time
import subprocess


parser = argparse.ArgumentParser(
    description='Handle audio stream to janus server'
)


parser.add_argument(
    '--audio-raw',
    metavar="audio_raw",
    type=str,
    action="store",
    dest="audio_raw",
    required=True,
    help="path audio raw file"
)


parser.add_argument(
    '--janus-port',
    metavar="janus_port",
    type=str,
    action="store",
    dest="janus_port",
    required=True,
    help="janus UDP port"
)


parser.add_argument(
    '--janus-ip',
    metavar="janus_ip",
    type=str,
    action="store",
    dest="janus_ip",
    required=True,
    help="janus IP"
)

parser.add_argument(
    '--time-interval-start-stream',
    metavar="time_interval_start_stream",
    type=int,
    action="store",
    dest="time_interval_start_stream",
    required=True,
    help="time interval for starting stream with gstreamer"
)

parser.add_argument(
    '--time-interval-stop-stream',
    metavar="time_interval_stop_stream",
    type=int,
    action="store",
    dest="time_interval_stop_stream",
    required=True,
    help="time interval for stop stream (gstreamer) and remove raw audio file"
)

parser.add_argument(
    '--check-period',
    metavar="check_period",
    type=int,
    action="store",
    dest="check_period",
    required=True,
    help="check period"
)

# insert debug options


args = parser.parse_args()
time_interval_start_stream = args.time_interval_start_stream
time_interval_stop_stream = args.time_interval_stop_stream
audio_raw_file = args.audio_raw
check_period = args.check_period
janus_ip = args.janus_ip
janus_port = args.janus_port
gstreamer_pid = None

while True:

    try:

        now = datetime.datetime.now()

        # get mtime and implicity check if raw audio file exists
        mtime = datetime.datetime.fromtimestamp(os.path.getmtime(audio_raw_file))
        ctime = datetime.datetime.fromtimestamp(os.path.getatime(audio_raw_file))
        # get time delta in seconds
        tdelta_m = int((now - mtime).total_seconds())
        tdelta_c = int((now - ctime).total_seconds())

        print("now => %s" % str(now))
        print("mtime => %s" % str(mtime))
        print("ctime => %s" % str(ctime))

        print("tdelta_m => %s" % tdelta_m)
        print("tdelta_c => %s" % tdelta_c)
        print("gstreamer_pid => %s" % gstreamer_pid)

        if time_interval_stop_stream > tdelta_c > time_interval_start_stream and gstreamer_pid is None:
            print("start gstreamer")
            #proc = subprocess.Popen(["watch", "ls", audio_raw_file])
            #proc = subprocess.Popen(["sleep", "30"])
            proc = subprocess.Popen(
                    [f"cat {audio_raw_file} | gst-launch-1.0 fdsrc fd=0 ! rawaudioparse use-sink-caps=false format=pcm pcm-format=s16be sample-rate=6000 num-channels=1 ! audioconvert  !  audioresample !  opusenc ! rtpopuspay ! udpsink host={janus_ip} port={janus_port}"],
                shell=True
            )

            gstreamer_pid = proc.pid
            print(gstreamer_pid)

        elif tdelta_m > time_interval_stop_stream and gstreamer_pid is not None:
            print("kill gstream")
            print("removing raw audio file")
            os.kill(gstreamer_pid, 9)
            os.remove(audio_raw_file)
            gstreamer_pid = None

    except FileNotFoundError as e:
        print("file not found exception")

    except Exception as e:
        print(str(e))

    finally:
        time.sleep(check_period)

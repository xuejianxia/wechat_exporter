# .aud files converter to wav
# [Author: Nicodemo Gawronski] Need help? write: nico AT deftlinux dot net
# 

import os, argparse, codecs, re, sys, shutil,subprocess
from datetime import datetime

def arm_header(converted):
    sys.stdout.write("Appending the arm header to the .aud files...")    
    for dirname, dirnames, filenames in os.walk(converted):

        header= "audio_header/amr_header.bin"
        for filename in filenames:
            #print os.path.join(dirname, filename)
            aud_file = os.path.join(dirname, filename)
            new_arm = os.path.join(dirname, filename).replace(".aud", ".arm", 1)
            #print new_arm
            #with open(new_arm, 'wb') as f:
            file(new_arm,'wb').write(file(header,'rb').read()+file(aud_file,'rb').read())
    print("done!")

#Convert the chat audio files from arm to wav.
def convert_audio(converted):
    sys.stdout.write("Converting the .arm files to wav...")
    for dirname, dirnames, filenames in os.walk(converted):

        for filename in filenames:
            print os.path.join(dirname, filename)
            if ".arm" in os.path.join(dirname, filename):
				convert_this = os.path.join(dirname, filename)
				to_wav = convert_this.replace(".arm", ".wav", 1)
				black_hole = open("black_hole", "w")
				subprocess.call(["ffmpeg", "-i", convert_this, to_wav], stdout = black_hole, stderr = black_hole)
				black_hole.close()
    print("done!")

def clean_old_audio(converted):
    sys.stdout.write("Taking out the trash (old copies of .aud files)... ")
    delete = "black_hole"
    os.remove(delete)
	
    for dirname, dirnames, filenames in os.walk(converted):
        for filename in filenames:
            #print os.path.join(dirname, filename)
            if ".arm" in os.path.join(dirname, filename) or ".aud" in os.path.join(dirname, filename):
                delete_this = os.path.join(dirname, filename)
                os.remove(delete_this)
    print("done!")

class Main(argparse.Action):
     def __call__(self, parser, namespace, values, option_string=None):
         
         audio_src = values
         print audio_src
         now = datetime.utcnow()
         now = datetime.strptime(str(now), '%Y-%m-%d %H:%M:%S.%f')
         now = now.strftime('%d-%m-%Y %H.%M.%S')
         converted = now+"_converted"
         try:
             #Copy Audio files
             shutil.copytree(audio_src, converted)
             #Append ARM header to audio files and Convert them to ogg format
             arm_header(converted)
             convert_audio(converted)
             clean_old_audio(converted)
         except:
             print("Something went wrong converting the audio files...")



parser = argparse.ArgumentParser(description=".aud converter: convert wechat .aud files into .wav", epilog="Wechat Xtractor is an open source tool written for DEFT 8 under the GNU GPLv3 license. If you have any trouble or if you find a bug please report it on DEFT forum at http://www.deftlinux.net/forum/ or write an email to the developer at nico@deftlinux.net")
parser.add_argument("Folder", action=Main, help=".aud files root folder.")


args = parser.parse_args()

import youtube_dl
import logging
import config
import boto3
import os
from bs4 import BeautifulSoup
import requests
import sys
import vlc
import pafy
import time
import sqlite3
import spotipy.util as util
import spotipy
from datetime import datetime






logging.basicConfig(level=logging.INFO,filename='logs.log',format='%(asctime)s %(message)s') # include timestamp



def soup(search):

    main = "https://www.youtube.com/results?search_query=" + search.replace(" ", "+")


    page = requests.get(main)

    soup = BeautifulSoup(page.content, 'html.parser')

    vids = soup.findAll('a',attrs={'class':'yt-uix-tile-link'})

    youtube_list=[]

    [youtube_list.append('https://www.youtube.com' + v['href']) for v in vids[:3]]

  
    soundcloud_list = []
    main = "https://soundcloud.com/search?q=" + search.replace(" ", "%20")

    page = requests.get(main)
    soup = BeautifulSoup(page.content, "html.parser")

    for link in soup.find_all('a', href=True):
        soundcloud_list.append('https://soundcloud.com' + link['href'])

    soundcloud_list = soundcloud_list[6:9]


    return youtube_list,soundcloud_list

def download(url):
    cwd = os.getcwd()
    ydl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': cwd+ '/%(title)s.%(ext)s',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '999',  
    }],
            }  

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:

        ydl.download([url])

        #contains urls to location of
        info_dict = ydl.extract_info(url, download=False)
        file_name = info_dict.get('title', None) + '.mp3'


        
        print('\nUploading to s3 bucket...\n')

        
    return file_name 
       
def upload(file_name, sub):
    s3 = boto3.client(
        's3',
        aws_access_key_id=config.access_key,
        aws_secret_access_key=config.secret_access_key,
    )
    bucket_name = 'songss'
    print(file_name)
    s3.upload_file(file_name.replace('"',"'").replace("/","_"), bucket_name, sub + '/' + file_name)
    conn = sqlite3.connect('songs_db')
    c = conn.cursor()

    c.execute("CREATE TABLE IF NOT EXISTS Songs(file_name PRIMARY KEY, date_added)")
    conn.commit() 

    
    try:
        date_added = datetime.now()
        entities = (file_name,date_added)
        c.execute("INSERT INTO Songs(file_name, date_added) VALUES(?,?)", entities)
        conn.commit()
    except Exception as e:
        print(e)
        pass

    logging.info(file_name)
    conn.close()

def results(ylist,slist):



    num = input(f"""Here are the top three results:\n\nYoutube\n--------------------------------------\n1.) {ylist[0]}\n2.) {ylist[1]}\n3.) {ylist[2]}\n 
Soundcloud\n--------------------------------------\n4.) {slist[0]}\n5.) {slist[1]}\n6.) {slist[2]}\n\nChoose an option.\n""")
    
    choice = {
        '1': ylist[0],
        '2': ylist[1],
        '3': ylist[2],
        '4': slist[0],
        '5': slist[1], 
        '6': slist[2],
    }

    try:
        if num == 'back':
            block1()

       
        x = num.split(" ")
        if len(x) == 2:
            url = choice.get(x[1]).strip()
        else:
            url = choice.get(x[0].strip())
        video = pafy.new(url)
        best = video.getbestaudio()
        playurl = best.url
        Instance = vlc.Instance()
        player = Instance.media_player_new()
        Media = Instance.media_new(playurl)
        Media.get_mrl()
        player.set_media(Media)
                 
        if 'play' in num:
        
            while True:
                try:
                    time.sleep(.1)
                    player.play()
                    j = input("\nPlaying..\n")
                except Exception as e:
                    print(f"Unable to play because: {e}")
                    results(ylist,slist)
        
                if 'stop' in j:
                    player.stop()
                    results(ylist,slist)
    
        if int(num) > 0 and int(num) < 7:
            pass
        else:
            print('\nPlease select a valid choice (1-6).')
            results(ylist,slist)
            
    except Exception as e:
            print(e)
            results(ylist,slist)


                
    


    url = choice.get(num)

    q4 = input('\nSpecify the folder you want to place it in. (pop, hiphop, rnb, edm)\n')
    
    if q4 == 'back':
            results(ylist,slist)
        

    name = download(url)
    upload(name,q4)
    remove(name)
    run_again()  

def remove(file_name):
    try:

        os.remove(file_name)
        print('\nRemoved file.\n')
    except Exception as e:
        print(e)

def start():
    print('''
                                o  o   o  o
                                |\/ \^/ \/|
                                |,-------.|
                             #################
                       #######---------------- #####
                   ## ---------------------------- ###
                ## ---------------------------------- ##
           #  ------------------------------------------  #
          #  ----------------------------#--------------#  #
          #  -----------------------------#------------#--  #
         #  ------------------------------##----------##--- #   #####
         #  ----#####----------------------###------###---- # ##     #
         #  ---#     ##--------------------#  ######  #----  ##     -- #
        #  ---# --     ##------------------#  ######  #-----  # ------ #
        #  ----# -------- # ---------------#  #----#  #-----  #----- #
        #  ----# --------- # ---------------#  #----# #-----  #---- # 
       #  ------# --------------------------##------##-------  #----#      
       #  ------# -------------------------------------------  #---#
       #  -------# ------------------------------------------  #- #
      #  ---------# -----------------------------------------  #-#
      #  ---------# -----------------------------------------  # #
      #  ----------#  -----------------------###----###------  ##
      #  -----------## ---------------------#   ####  %#-----  #
     #  --------------##-------------------#%   %%%   %#-----  #
   #  ------------------------------------#%%%%%%%%%%%%%#---  #
  #  -------------------------------------#% %%%%%%%%% %#---  #
#  -------------------------------------##  %%%##%%  ##----  # 
#  --------------------------------------------------------  #
 ##--------------------------------------------------------  #
     ################# ----------------------------------- ##
                      ####  ---------------------------- ####
                          ##############################
''')

    q = input("Welcome to King Boo's Song Downloader. Do you want to: (type '1' or '2', etc. and press enter to confirm your choice) \n1.) Search for a song.\n2.) Enter url.\n3.) Search for song (quick).\n4.) Download Spotify Playlist\n ")

    if q != '1' and q != '2' and q!= '3' and q!= '4':
        print('Please select a valid choice.')
        start()

    elif q == '1':
        block1()
    
    elif q == '2':
        block2()
    elif q =='3':
        block3()
    elif q =='4':
        block4()
        
def block1():
        q2 = input("Enter search terms. It is recommended to enter both the song name and the artist. E.g. lollipop lil wayne.\n")

        if q2 == 'back':
            os.execl(sys.executable, sys.executable, *sys.argv)

        
        print(f"\nGetting links...")
    
        youtube_list = soup(q2)[0]
        soundcloud_list = soup(q2)[1]

        results(youtube_list, soundcloud_list)

def run_again():
    q3 = input(f"Upload to bucket is successful. Do you want to run again? (y/n)\n")
    if q3 not in ('y', 'n'):
        print('Enter a valid choice.')
        run_again()
    if q3 == 'y':
        os.execl(sys.executable, sys.executable, *sys.argv)

    else:
        sys.exit()
    
def block2():
    while True:
        q2 = input("Enter url.\n")
        try:
            if q2 == 'back':
                os.execl(sys.executable, sys.executable, *sys.argv)


            q4 = input('\nSpecify the folder you want to place it in. (pop, hiphop, rnb, edm)\n')
            name = download(q2.strip())
            upload(name,q4)
            remove(name)
            run_again()
           
        except Exception as e:
            print('Please enter a valid url.')
            continue  

def block3():
    q = input("Enter search terms. It is recommended to enter both the song name and  the artist. E.g. song name artist.\n")
    
    if q == 'back':
        os.execl(sys.executable, sys.executable, *sys.argv)


    q2 = input('\nSpecify the folder you want to place the song in. (pop, hiphop, rnb, edm)\n')

    search = soup(q)[0]
    one = search[0]
    name = download(one)
    upload(name,q2)
    remove(name)
    run_again()


def block4():
    username = 'agrawa48'
    token = util.prompt_for_user_token(username, scope='playlist-modify-private,playlist-modify-public,playlist-read-private', client_id=config.spotify_client_id, client_secret=config.spotify_client_secret, redirect_uri='https://localhost:8080')
    
    if token:
        sp = spotipy.Spotify(auth=token)

    playlists = sp.current_user_playlists()
    count = 0
    plid_list = []
    plname_list = []
    d = {}
    d2 = {}

    for pl in playlists['items']:
        count += 1

    for i in range(count):
        pl_id =  playlists['items'][i]['uri'].replace("spotify:playlist:","").replace('"',"")
        pl_name = playlists['items'][i]['name'].replace('"',"")
        d[i] = pl_name

        plid_list.append(pl_id)
        plname_list.append(pl_name)

        d2[pl_name] = pl_id


  

       

    print(f"Which playlist do you want to download?")
    for key, value in d.items():
        print(str(key+1) + ".) " + value)
    q = input("").strip()
    if q == 'back':
        os.execl(sys.executable, sys.executable, *sys.argv)

    print(q)
    print(d)
    x = d.get(int(int(q)-1))
    print(x)

    playlist_id = d2.get(x)
    q_list = []
    tracks = sp.user_playlist_tracks(username,playlist_id=playlist_id)
    for track in tracks["items"]:
        #track name + track artist
        query = track['track']['name'] + " " +  track['track']['artists'][0]['name']
        print(query)
        q_list.append(query)

    for q in q_list:
        search = soup(q)[0]
        one = search[0]

        try:

            name = download(one)
        except Exception as e:
            logging.info(f'Error: {e}')
            remove(name)
            pass
            
        try:
            upload(name, x)
            remove(name)
        except:
            pass

    run_again()



if __name__ == "__main__":
    start()








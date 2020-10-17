import discord
import glob
import shutil
import os
import sys
import youtube_dl
import ffmpeg
from pydub import AudioSegment
import asyncio

client = discord.Client()

###初期値###
commands = {'/Rhelp':{},
            '/Rdog':{},
            '/Roppai':{},
            '/Rtask':{'add':'task names','show':None,'del':'task names'},
            '/Rmusic':{'show':None,'download':'url','del':'numbers','play':'numbers','play-loop':'numbars','add':'urls','remove':'numbers'}}

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

#メインの処理
@client.event
async def on_message(message):
    # メッセージ送信者がBotだった場合は無視する
    if message.author.bot:
        return

    #メッセージをリストで取得
    if message.content.startswith('/R'):
        #マルチコマンド対応
        #main,sub,optionに分割する
        user_message_lst = message.content.split(" ")
        if len(user_message_lst) == 1:
            user_message_lst += [None,None]
        elif len(user_message_lst) == 2:
            user_message_lst += [None]
        else:
            pass
        
        main_command = user_message_lst[0]
        sub_command = user_message_lst[1]
        options = user_message_lst[2:]
        
    else:
        return

    #コマンドを間違えているときの処理
    if not main_command in commands.keys():
        await message.channel.send("そのメインコマンドは存在しません。以下のメインコマンドが稼働中です。")
        await message.channel.send("\n".join(commands.keys()))
        
    
    #sub_commandがないとき
    elif (main_command in commands.keys()) and (sub_command==None):
        if commands[main_command] == {}:
            out_message = await single_command_func(main=main_command,commands=commands)
            await message.channel.send(out_message)
        else:
            out_message = 'このコマンドはサブコマンドを持ちます。\n先程のメインコマンドに続けて以下のサブコマンドを一つ打ち込んでください。'
            await message.channel.send(out_message)
            await message.channel.send('\n'.join(commands[main_command].keys()))

    #sub_commandが間違えている
    elif (main_command in commands.keys()) and not (sub_command in commands[main_command].keys()):
        out_message = 'サブコマンドを間違えていませんか？\n先程のメインコマンドに続けて以下のサブコマンドを一つ打ち込んでください。'
        await message.channel.send(out_message)
        await message.channel.send('\n'.join(commands[main_command].keys()))
 

    #sub_commandが正しく、そのsub_commandにオプションが存在しない場合
    elif (main_command in commands.keys()) and (sub_command in commands[main_command].keys()) and (commands[main_command][sub_command]==None):
        out_message = await sub_command_func(main=main_command,sub=sub_command,commands=commands)
        await message.channel.send(out_message)
    
    #オプションが存在するコマンドが呼び出されて、オプションが入力されていない場合
    elif (main_command in commands.keys()) and (sub_command in commands[main_command].keys()) and (commands[main_command][sub_command]!=None) and options==[None]:
        out_message = 'オプションの必要なコマンドです。\nこのコマンドにおけるオプションの種類は以下の通りです。'
        await message.channel.send(out_message)
        await message.channel.send(commands[main_command][sub_command])
    
    #オプションまでが正しく入力されている場合
    elif (main_command in commands.keys()) and (sub_command in commands[main_command].keys()) and (commands[main_command][sub_command]!=None) and options!=[None]:
        out_message = await option_command_func(main=main_command,sub=sub_command,options=options,message=message)
        await message.channel.send(out_message)


    #不明なエラー
    else:
        out_message = '不明なエラーです。ヘルプを参照してください。'
        await message.channel.send(out_message)
        out_message = single_command('/Rhelp')

        await message.channel.send(out_message)



#メインコマンドまでの処理
@client.event
async def single_command_func(main,commands):
    if main == '/Rhelp':
        return '以下のメインコマンドが稼働中です。\n'+'\n'.join(commands.keys())

    # 「/dog」と発言したら「BOWWOW」が返る処理
    if main == '/Rdog':
        return 'BOWWOW'

    if main == '/Roppai':
        return 'BOING BOING!!'


#サブコマンドまでの処理
@client.event
async def sub_command_func(main,sub,commands):
    #task関連のコマンド
    if main == '/Rtask':
        if sub == 'show':
            f = open(r'dev-info\task.txt','r')
            task = f.readlines()
            f.close()
            return ''.join(task)

    if main == '/Rmusic':
        if sub == 'show':
            out_message = []
            music_list = glob.glob('./music/*.mp3')
            for i,music in enumerate(music_list):
                out_message.append('{0}.'.format(i+1) + music[7:])
        return '\n'.join(out_message)

@client.event
async def option_command_func(main,sub,options,message):
    #music play
    if main == '/Rmusic':
        music_dict = {}

        if sub == "download":

            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
            for option in options:
                with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                    ydl.download(['{0}'.format(option)])
                    shutil.move(glob.glob('./*.mp3')[0], './music/'+glob.glob('./*.mp3')[0].split('-')[0]+'.mp3')
            return "ダウンロード完了しました。"

        if sub == 'del':
            pass

        if sub == "play":
            #print(type(channel))
            #voice = channel.guild.voice_client
            music_list = glob.glob('./music/*.mp3')
            for i,music in enumerate(music_list):
                music_dict[str(i+1)] = music

            voice = await message.author.voice.channel.connect(timeout=100,reconnect=True)
            await message.channel.send('楽曲を再生します。')
            for option in options:
                sourceAudio = AudioSegment.from_file(music_dict[option], "mp3")
                sleeptime = sourceAudio.duration_seconds
                voice.play(discord.FFmpegPCMAudio(music_dict[option]))
                await asyncio.sleep(sleeptime+0.5)
                    
            await voice.disconnect()

        if sub == "play-loop":
            """
            main   = '/Rmusic'
            sub    = 'play'
            option = 'numbers'
            """
            
            music_list = glob.glob('./music/*.mp3')
            for i,music in enumerate(music_list):
                    music_dict[str(i+1)] = music

            voice = await message.author.voice.channel.connect()
            await message.channel.send('楽曲を再生します。')
            while True:
                for option in options:
                    try:
                        voice.play(discord.FFmpegPCMAudio(music_dict[option]))
                        while voice.is_playing():
                            time.sleep(2)
                    except youtube_dl.utils.DownloadError:
                        #await message.channel.send('エラーが発生しました。')
                        return 'エラーが発生しました。'


async def play_music(path,message,voice):
    try:
        voice.play(discord.FFmpegPCMAudio(source=path))
        sourceAudio = AudioSegment.from_file(music_dict[option], "mp3")
        sleeptime = sourceAudio.duration_seconds
        await asyncio.sleep(sleeptime)

    except youtube_dl.utils.DownloadError:
        #await message.channel.send('エラーが発生しました。')
        return 'エラーが発生しました。'

#ボットを走らせる
client.run("NzY1NTg0MDM2NjA0MTQ5Nzkx.X4W7sg.zR88hFOPuzSYdZV88Ds8oIy9oRw")
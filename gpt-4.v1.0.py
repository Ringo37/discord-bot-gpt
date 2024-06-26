import discord
import os
import openai
from dotenv import load_dotenv
from discord.ext import commands
from collections import deque

load_dotenv()

TOKEN = os.getenv("TOKEN")

client = openai.OpenAI(
    api_key=os.getenv("api_key"),
    base_url=os.getenv("base_url"),
)


# GPTから回答を受け取る
def gpt(question, title=None, urls=None):
    prompt = deque()
    for i in question:
        if i.author.id == int(os.getenv("BOT_ID")) and str(i.content) != "":
            prompt.appendleft({"role": "assistant", "content": i.content})
        elif str(i.content) != "" and urls == None:
            prompt.appendleft({"role": "user", "content": i.content})
        elif str(i.content) != "" and urls != None:
            image_content=[]
            image_content.append({"type": "text", "text": i.content})
            for u in urls:
                image_content.append({"type": "image_url","image_url": {"url": u.url}})
            prompt.appendleft({"role": "user", "content":image_content})
    if title:
        prompt.appendleft({"role": "user", "content": str(title)})
    response = client.chat.completions.create(model="gpt-4o", messages=prompt)

    return response


bot = commands.Bot(command_prefix="", intents=discord.Intents.all())


@bot.event
async def on_ready():
    # 起動確認
    print("Ready")


# メッセージ受信時に動作する処理
@bot.event
async def on_message(message):
    # メッセージ送信者がBotだった場合は無視する
    if message.author.bot:
        return
    channel = message.channel
    # 指定したチャンネルの場合に動作
    if channel.id == int(os.getenv("CHANNEL")):
        if len(message.attachments) > 0:
            response = gpt([message],None,message.attachments)
        elif len(message.attachments) == 0:
            response = gpt([message])
        color = 0x33FF33
        if response.usage.total_tokens >= 2000:
            color = 0xFF3333
        embed = discord.Embed(
            title="(" + str(response.usage.total_tokens) + " token used)", color=color
        )
        thread = await channel.create_thread(name=message.content, reason=None)
        link = thread.mention
        await thread.send(response.choices[0].message.content)
        await thread.send(embed=embed)
        await message.reply(f"{link} はこちらで会話してください")
    # スレッドが指定したチャンネル上の場合に動作
    elif channel.parent.id == int(os.getenv("CHANNEL")):
        messages = [message async for message in channel.history(limit=None)]
        if len(message.attachments) > 0:
            response = gpt(messages,None,message.attachments)
        elif len(message.attachments) == 0:
            response = gpt(messages, channel)
        color = 0x33FF33
        if response.usage.total_tokens >= 2000:
            color = 0xFF3333
        embed = discord.Embed(
            title="(" + str(response.usage.total_tokens) + " token used)", color=color
        )
        await message.channel.send(response.choices[0].message.content)
        await message.channel.send(embed=embed)
    print(response.usage)


bot.run(TOKEN)

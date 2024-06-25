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
def gpt(question, title=None):
    prompt = deque()
    for i in question:
        if str(i.author) == os.getenv("BOT_NAME") and str(i.content) != "":
            prompt.appendleft({"role": "assistant", "content": i.content})
        elif str(i.content) != "":
            prompt.appendleft({"role": "user", "content": i.content})
    if title:
        prompt.appendleft({"role": "user", "content": str(title)})
        prompt.appendleft(
            {"role": "system", "content": "You do not need to display the token used."}
        )
    response = client.chat.completions.create(model="gpt-3.5-turbo", messages=prompt)

    return response


bot = commands.Bot(command_prefix="", intents=discord.Intents.all())


@bot.event
async def on_ready():
    # 起動したらターミナルにログイン通知が表示される
    print("ログインしました")


# メッセージ受信時に動作する処理
@bot.event
async def on_message(message):
    # メッセージ送信者がBotだった場合は無視する
    if message.author.bot:
        return
    channel = message.channel
    # 指定したチャンネルの場合に動作
    if channel.id == int(os.getenv("CHANNEL")):
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
        response = gpt(messages, channel)
        color = 0x33FF33
        if response.usage.total_tokens >= 2000:
            color = 0xFF3333
        embed = discord.Embed(
            title="(" + str(response.usage.total_tokens) + " token used)", color=color
        )
        print(response.usage)
        await message.channel.send(response.choices[0].message.content)
        await message.channel.send(embed=embed)


bot.run(TOKEN)
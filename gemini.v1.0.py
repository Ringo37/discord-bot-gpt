import discord
import os
import google.generativeai as genai
from dotenv import load_dotenv
from discord.ext import commands
from collections import deque

load_dotenv()

TOKEN = os.getenv("TOKEN")

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  generation_config=generation_config,
  # safety_settings = Adjust safety settings
  # See https://ai.google.dev/gemini-api/docs/safety-settings
)

display_token_usage = True


# Geminiから回答を受け取る
def gemini(question, title=None):
    prompt_history = deque()
    questions=deque(question)
    message=questions.popleft()
    for i in questions:
        if str(i.author) == os.getenv("BOT_NAME") and str(i.content) != "":
            prompt_history.appendleft({"role": "model", "parts": [i.content]})
        elif str(i.content) != "":
            prompt_history.appendleft({"role": "user", "parts": [i.content]})
    if title:
        prompt_history.appendleft({"role": "user", "parts": [str(title)]})
    chat_session = model.start_chat(history=prompt_history)
    response = chat_session.send_message(message.content)
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
        response = gemini([message])
        color = 0x33FF33
        if response.usage_metadata.total_token_count >= 2000:
            color = 0xFF3333
        embed = discord.Embed(
            title=str(response.usage_metadata.total_token_count) + " tokens used", color=color
        )
        thread = await channel.create_thread(name=message.content, reason=None)
        link = thread.mention
        await thread.send(response.text)
        if display_token_usage:
            await thread.send(embed=embed)
        await message.reply(f"{link} はこちらで会話してください")
    # スレッドが指定したチャンネル上の場合に動作
    elif channel.parent.id == int(os.getenv("CHANNEL")):
        messages = [message async for message in channel.history(limit=None)]
        response = gemini(messages, channel)
        color = 0x33FF33
        if response.usage_metadata.total_token_count >= 2000:
            color = 0xFF3333
        embed = discord.Embed(
            title=str(response.usage_metadata.total_token_count) + " tokens used", color=color
        )
        await message.channel.send(response.text)
        if display_token_usage:
            await message.channel.send(embed=embed)


bot.run(TOKEN)

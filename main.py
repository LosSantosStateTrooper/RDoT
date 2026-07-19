import os
import discord
from discord.ext import commands

# Botの初期設定（インテントの有効化）
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ルールを投稿する対象のチャンネルID
TARGET_CHANNEL_ID = 1528374067923779594

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    
    # 指定されたチャンネルを取得
    channel = bot.get_channel(TARGET_CHANNEL_ID)
    if channel is None:
        try:
            channel = await bot.fetch_channel(TARGET_CHANNEL_ID)
        except Exception as e:
            print(f"ERROR: Could not find or access channel with ID {TARGET_CHANNEL_ID}: {e}")
            return

    print(f"Checking channel: #{channel.name} ({channel.id})")

    # チャンネルの履歴を読み込んで、すでにBotが発言しているかチェック
    already_posted = False
    try:
        async for message in channel.history(limit=50):
            # Bot自身が送信した埋め込みメッセージ（Embed）があるか確認
            if message.author.id == bot.user.id and len(message.embeds) > 0:
                # タイトルに特徴的な文字が含まれているかチェック
                if any("Robloxian Department of Transportation" in str(embed.title) for embed in message.embeds):
                    already_posted = True
                    break
    except Exception as e:
        print(f"Failed to read channel history: {e}")

    if already_posted:
        print("Official rules are already posted in the channel. Skipping.")
    else:
        print("Official rules not found. Posting now...")
        
        # 整理したルールを一画面で見やすいよう1つのEmbedにまとめました
        embed = discord.Embed(
            title="🏢 Robloxian Department of Transportation",
            description="Welcome to the RDoT. By joining this server, you agree to uphold the following standards.",
            color=discord.Color.blue()
        )
        
        # 旧1番＋RZRMルールの順守を統合
        embed.add_field(
            name="1. Professionalism & Conduct",
            value="• **Maintain Decorum:** Always treat fellow members with respect. Toxic behavior, harassment, or unnecessary drama will not be tolerated.\n• **Adhere to Regulations:** All members must comply with standard Discord TOS as well as RZRM rules and guidelines at all times.",
            inline=False
        )
        
        # 旧3番を「2」に繰り上げ
        embed.add_field(
            name="2. Operational Guidelines (RDoT Focus)",
            value="• **Neutrality & Support:** We are a logistical and infrastructure organization, not a combat faction. Do not engage in combat unless absolutely necessary for self-defense (TSD) or under authorized direct orders.\n• **Chain of Command:** Respect the hierarchy. Direct all operational inquiries to your respective Division Chiefs.\n• **Cooperation, Not Reliance:** We support other factions (the Military, Police, etc.), but we maintain our administrative independence. Do not compromise RDoT’s integrity by acting as an unofficial subordinate to other groups.",
            inline=False
        )
        
        embed.set_footer(text="⚠️ Failure to adhere to these rules may result in formal reprimands or removal from the organization.")

        try:
            await channel.send(embed=embed)
            print("Official rules have been posted successfully!")
        except Exception as e:
            print(f"Failed to send rules to the channel: {e}")

# Renderの環境変数からDiscord Tokenを読み込んで起動
TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("ERROR: DISCORD_TOKEN environment variable is missing.")

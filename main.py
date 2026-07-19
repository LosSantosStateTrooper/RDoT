import os
import discord
from discord import app_commands
from discord.ext import commands
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# ==========================================
# 🛑 Renderのタイムアウト対策（ダミーWEBサーバー）
# ==========================================
class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"RDoT Bot is alive!")

def run_dummy_server():
    # Renderはデフォルトで環境変数 PORT (通常10000) を指定してくるのでそれを読み込む
    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), DummyServer)
    print(f"Dummy web server started on port {port}")
    server.serve_forever()

# 別スレッドでWEBサーバーを起動（Botの邪魔をしないように）
threading.Thread(target=run_dummy_server, daemon=True).start()


# ==========================================
# 🤖 Discord Bot の本体設定
# ==========================================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # メンバーの参加検知用

bot = commands.Bot(command_prefix="!", intents=intents)

# ルールを投稿する対象のチャンネルID
TARGET_CHANNEL_ID = 1528374067923779594

# 自動付与するロールIDのリスト
ROLE_IDS = [
    1528079171891494922,
    1528076207122288810,
    1528077244201697320
]

@bot.event
async def on_member_join(member):
    print(f"New member joined: {member.name} ({member.id})")
    guild = member.guild
    roles_to_add = []
    
    for role_id in ROLE_IDS:
        role = guild.get_role(role_id)
        if role:
            roles_to_add.append(role)
        else:
            print(f"WARNING: Role ID {role_id} not found.")
            
    if roles_to_add:
        try:
            await member.add_roles(*roles_to_add)
            print(f"Successfully added {len(roles_to_add)} roles to {member.name}!")
        except discord.Forbidden:
            print("ERROR: Bot lacks permission. Check role hierarchy!")
        except Exception as e:
            print(f"Failed to add roles: {e}")

async def run_test_command(target):
    embed = discord.Embed(
        title="🚧 RDoT System Check",
        description="The RDoT Bot infrastructure is fully operational.",
        color=discord.Color.green()
    )
    embed.add_field(name="Status", value="🟢 Online & Ready", inline=True)
    embed.add_field(name="Available Protocols", value="• Prefix: `!`\n• Slash: `/`", inline=True)
    
    if isinstance(target, discord.Interaction):
        await target.response.send_message(embed=embed)
    else:
        await target.send(embed=embed)

@bot.tree.command(name="test", description="Check if the RDoT bot is responding to slash commands.")
async def test_slash(interaction: discord.Interaction):
    await run_test_command(interaction)

@bot.command(name="test")
async def test_prefix(ctx):
    await run_test_command(ctx.channel)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    
    channel = bot.get_channel(TARGET_CHANNEL_ID)
    if channel is None:
        try:
            channel = await bot.fetch_channel(TARGET_CHANNEL_ID)
        except Exception as e:
            print(f"ERROR: Could not find channel {TARGET_CHANNEL_ID}: {e}")
            return

    already_posted = False
    try:
        async for message in channel.history(limit=50):
            if message.author.id == bot.user.id and len(message.embeds) > 0:
                if any("Robloxian Department of Transportation" in str(embed.title) for embed in message.embeds):
                    already_posted = True
                    break
    except Exception as e:
        print(f"Failed to read channel history: {e}")

    if already_posted:
        print("Official rules are already posted. Skipping.")
    else:
        print("Official rules not found. Posting now...")
        embed = discord.Embed(
            title="🏢 Robloxian Department of Transportation",
            description="Welcome to the RDoT. By joining this server, you agree to uphold the following standards.",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="⚖️ 1. Professionalism & Conduct",
            value="• **Maintain Decorum:** Always treat fellow members with respect. Toxic behavior, harassment, or unnecessary drama will not be tolerated.\n• **Adhere to Regulations:** All members must comply with standard Discord TOS as well as RZRM rules and guidelines at all times.",
            inline=False
        )
        embed.add_field(
            name="🚧 2. Operational Guidelines (RDoT Focus)",
            value="• **Neutrality & Support:** We are a logistical and infrastructure organization, not a combat faction. Do not engage in combat unless absolutely necessary for self-defense (TSD) or under authorized direct orders.\n• **Chain of Command:** Respect the hierarchy. Direct all operational inquiries to your respective Division Chiefs.\n• **Cooperation, Not Reliance:** We support other factions (the Military, Police, etc.), but we maintain our administrative independence. Do not compromise RDoT’s integrity by acting as an unofficial subordinate to other groups.",
            inline=False
        )
        embed.set_footer(text="⚠️ Failure to adhere to these rules may result in formal reprimands or removal from the organization.")

        try:
            await channel.send(embed=embed)
            print("Official rules have been posted successfully!")
        except Exception as e:
            print(f"Failed to send rules: {e}")

TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("ERROR: DISCORD_TOKEN environment variable is missing.")

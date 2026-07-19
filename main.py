import os
import discord
from discord import app_commands
from discord.ext import commands
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# ==========================================
# 🛑 Render Timeout Prevention (Dummy Web Server)
# ==========================================
class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"RDoT Bot is alive!")

def run_dummy_server():
    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), DummyServer)
    print(f"Dummy web server started on port {port}")
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()


# ==========================================
# 🤖 Discord Bot Configuration
# ==========================================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True     # Required for tracking member joins
intents.reactions = True   # Required for tracking reaction adds

bot = commands.Bot(command_prefix="!", intents=intents)

# --- Configuration IDs ---
RULES_CHANNEL_ID = 1528374067923779594     # Rules channel
WELCOME_CHANNEL_ID = 1282971470774931460   # Welcome channel (Updated!)

INITIAL_ROLE_IDS = [
    1528079171891494922,
    1528076207122288810,
    1528077244201697320
]
RULES_AGREE_ROLE_ID = 1528404374429106366  # Rules agree role


# ==========================================
# 🚪 Member Join Event (Auto-roles & Welcome)
# ==========================================
@bot.event
async def on_member_join(member):
    print(f"New member joined: {member.name} ({member.id})")
    guild = member.guild
    
    # 1. Assign Initial Roles (3 roles)
    roles_to_add = []
    for role_id in INITIAL_ROLE_IDS:
        role = guild.get_role(role_id)
        if role:
            roles_to_add.append(role)
    if roles_to_add:
        try:
            await member.add_roles(*roles_to_add)
            print(f"Successfully added initial roles to {member.name}")
        except discord.Forbidden:
            print("ERROR: Bot lacks permission for initial roles.")
    
    # 2. Send Welcome Message
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        member_count = guild.member_count  # Total member count
        
        embed = discord.Embed(
            title="👋 Welcome to RDoT!",
            description=f"Welcome to the server, {member.mention}!\nYou are our **{member_count}**th member!",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="🔗 Quick Links",
            value=(
                f"Rules are here: https://discord.com/channels/1282971470774931457/1528374067923779594\n"
                f"Announce is here: https://discord.com/channels/1282971470774931457/1528373975300706314"
            ),
            inline=False
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        
        try:
            await channel.send(content=member.mention, embed=embed)
        except Exception as e:
            print(f"Failed to send welcome message: {e}")


# ==========================================
# ✅ Reaction Add Event (Rules Agreement)
# ==========================================
@bot.event
async def on_raw_reaction_add(payload):
    # Ignore reactions outside the rules channel
    if payload.channel_id != RULES_CHANNEL_ID:
        return
        
    # Ignore reactions other than White Heavy Check Mark
    if str(payload.emoji) != "✅":
        return
        
    # Ignore reactions added by the bot itself
    if payload.user_id == bot.user.id:
        return

    guild = bot.get_guild(payload.guild_id)
    if not guild:
        return

    member = guild.get_member(payload.user_id)
    if not member:
        return

    role = guild.get_role(RULES_AGREE_ROLE_ID)
    if role:
        try:
            if role not in member.roles:
                await member.add_roles(role)
                print(f"Successfully added rules agree role to {member.name}!")
        except discord.Forbidden:
            print("ERROR: Bot lacks permission to add rules agree role. Check role hierarchy!")
        except Exception as e:
            print(f"Failed to add rules agree role: {e}")


# ==========================================
# 🚀 Bot Ready Event (Rules Auto-Post Check)
# ==========================================
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    
    channel = bot.get_channel(RULES_CHANNEL_ID)
    if channel is None:
        return

    already_posted = False
    try:
        async for message in channel.history(limit=50):
            if message.author.id == bot.user.id and len(message.embeds) > 0:
                if any("Robloxian Department of Transportation" in str(embed.title) for embed in message.embeds):
                    already_posted = True
                    # Auto-react with ✅ if the rule message exists but lacks it
                    if "✅" not in [str(r.emoji) for r in message.reactions]:
                        await message.add_reaction("✅")
                    break
    except Exception as e:
        print(f"Failed to read channel history: {e}")

    if not already_posted:
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
        embed.set_footer(text="⚠️ Please react with ✅ below to agree to the rules.")

        try:
            msg = await channel.send(embed=embed)
            await msg.add_reaction("✅")
            print("Official rules have been posted successfully!")
        except Exception as e:
            print(f"Failed to send rules: {e}")

TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)

import os
import discord
from discord import app_commands
from discord.ext import commands
import threading
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler

# ==========================================
# Render Timeout Prevention (Dummy Web Server)
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
# Discord Bot Configuration
# ==========================================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

# --- Configuration IDs ---
RULES_CHANNEL_ID = 1528374067923779594
WELCOME_CHANNEL_ID = 1282971470774931460
APPLICATION_CHANNEL_ID = 1282972073806794776
LOG_CHANNEL_ID = 1528610922632057004

# ▼ ロール付与パネルを設置するチャンネルID ▼
ROLE_PANEL_CHANNEL_ID = 1528397429932818513

INITIAL_ROLE_IDS = [
    1528079171891494922,
    1528076207122288810,
    1528077244201697320
]
RULES_AGREE_ROLE_ID = 1528404374429106366
TRAINEE_ROLE_ID = 1528077358857326625

# ▼ 付与する対象のロールID ▼
ANNOUNCE_ROLE_ID = 1529012567874469920
GAMENIGHT_ROLE_ID = 1529012524400246795


# ==========================================
# Staff Approval Panel (Buttons in Log Channel)
# ==========================================
class StaffActionView(discord.ui.View):
    def __init__(self, applicant_id: int):
        super().__init__(timeout=None)
        self.applicant_id = applicant_id
        self.children[0].custom_id = f"approve_btn_{applicant_id}"
        self.children[1].custom_id = f"deny_btn_{applicant_id}"

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.success)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = guild.get_member(self.applicant_id)
        
        if not member:
            await interaction.response.send_message("Error: Cannot find this member in the server.", ephemeral=True)
            return

        role = guild.get_role(TRAINEE_ROLE_ID)
        if role:
            try:
                await member.add_roles(role)
                
                try:
                    dm_embed = discord.Embed(
                        title="Application Accepted",
                        description=f"Your application to RDoT has been approved.\nYou have been granted the Trainee role. Please check the server channels.",
                        color=discord.Color.green()
                    )
                    await member.send(embed=dm_embed)
                except discord.Forbidden:
                    pass
                
                button.disabled = True
                self.children[1].disabled = True
                await interaction.response.edit_message(content=f"Status: Approved by {interaction.user.mention}", view=self)
                
            except discord.Forbidden:
                await interaction.response.send_message("Error: Bot lacks permission to add the Trainee role.", ephemeral=True)
        else:
            await interaction.response.send_message("Error: Trainee role not found.", ephemeral=True)

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.danger)
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = guild.get_member(self.applicant_id)
        
        if member:
            try:
                dm_embed = discord.Embed(
                    title="Application Update",
                    description=f"Thank you for your interest in RDoT. Unfortunately, your application has been denied at this time.",
                    color=discord.Color.red()
                )
                await member.send(embed=dm_embed)
            except discord.Forbidden:
                pass

        button.disabled = True
        self.children[0].disabled = True
        await interaction.response.edit_message(content=f"Status: Denied by {interaction.user.mention}", view=self)


# ==========================================
# DM Application System Components
# ==========================================
class DMApplicationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Apply via DM", style=discord.ButtonStyle.primary, custom_id="apply_dm_btn")
    async def start_dm_app(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        
        try:
            await interaction.response.send_message("The application form has been sent to your DMs.", ephemeral=True)
        except Exception:
            pass

        try:
            intro_embed = discord.Embed(
                title="RDoT Official Application Form",
                description=(
                    "Thank you for your interest in joining the Robloxian Department of Transportation.\n"
                    "Please answer the following questions one by one. You have 5 minutes to answer each question.\n\n"
                    "The application process has officially started below:"
                ),
                color=discord.Color.blue()
            )
            await user.send(embed=intro_embed)
        except discord.Forbidden:
            await interaction.followup.send(content=f"Error: Could not send a DM to {user.mention}. Please enable direct messages from server members in your privacy settings.", ephemeral=True)
            return

        questions = [
            "**[Question 0]** What is your Timezone?",
            "**[Question 1]** Why do you want to join the RDoT?",
            "**[Question 2]** What would you do if you witnessed an RDoT staff member abusing their authority/power?",
            "**[Question 3]** How would you handle a civilian who is intentionally disrupting or interfering with an ongoing operation?",
            "**[Question 4]** Have you ever worked in an infrastructure or logistical organization before? If yes, please state your previous rank/experience.",
            "**[Question 5]** How active can you be throughout the week, and what unique skills or qualities can you bring to RDoT?"
        ]

        answers = []

        def check(m):
            return m.author.id == user.id and isinstance(m.channel, discord.DMChannel)

        for q in questions:
            await user.send(content=q)
            try:
                msg = await bot.wait_for("message", timeout=300.0, check=check)
                answers.append(msg.content)
            except asyncio.TimeoutError:
                timeout_embed = discord.Embed(
                    title="Application Cancelled",
                    description="Session timed out due to inactivity. Please click the button in the server to restart.",
                    color=discord.Color.red()
                )
                await user.send(embed=timeout_embed)
                return

        success_embed = discord.Embed(
            title="Application Submitted",
            description="Thank you for completing the application. Our recruitment staff will review your responses shortly.",
            color=discord.Color.green()
        )
        await user.send(embed=success_embed)

        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            log_embed = discord.Embed(
                title="New Application Received",
                description=f"**Applicant:** {user.mention} ({user.name} / ID: {user.id})",
                color=discord.Color.orange()
            )
            for i, ans in enumerate(answers):
                log_embed.add_field(name=f"Question {i}", value=ans, inline=False)
            
            log_embed.set_thumbnail(url=user.display_avatar.url)
            await log_channel.send(content="Status: Pending Review", embed=log_embed, view=StaffActionView(user.id))


# ==========================================
# Member Join Event (Auto-roles & Welcome)
# ==========================================
@bot.event
async def on_member_join(member):
    print(f"New member joined: {member.name} ({member.id})")
    guild = member.guild
    
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
            print("Error: Bot lacks permission for initial roles.")
    
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        member_count = guild.member_count
        
        embed = discord.Embed(
            title="Welcome to RDoT",
            description=f"Welcome to the server, {member.mention}.\nYou are member number {member_count}.",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Information Links",
            value=(
                f"Rules: https://discord.com/channels/1282971470774931457/1528374067923779594\n"
                f"Announcements: https://discord.com/channels/1282971470774931457/1528373975300706314"
            ),
            inline=False
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        
        try:
            await channel.send(content=member.mention, embed=embed)
        except Exception as e:
            print(f"Failed to send welcome message: {e}")


# ==========================================
# Reaction Add & Remove Event (Rules & Roles)
# ==========================================
@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return

    guild = bot.get_guild(payload.guild_id)
    if not guild:
        return

    member = guild.get_member(payload.user_id)
    if not member:
        return

    # --- Rules Channel (規約同意) ---
    if payload.channel_id == RULES_CHANNEL_ID and str(payload.emoji) == "✅":
        role = guild.get_role(RULES_AGREE_ROLE_ID)
        if role:
            try:
                if role not in member.roles:
                    await member.add_roles(role)
                    print(f"Successfully added rules agree role to {member.name}")
            except discord.Forbidden:
                print("Error: Bot lacks permission to add rules agree role.")
            except Exception as e:
                print(f"Failed to add role: {e}")

    # --- Role Panel Channel (通知ロール付与) ---
    elif payload.channel_id == ROLE_PANEL_CHANNEL_ID:
        if str(payload.emoji) == "📢":
            role = guild.get_role(ANNOUNCE_ROLE_ID)
            if role and role not in member.roles:
                try:
                    await member.add_roles(role)
                    print(f"Successfully added Announce role to {member.name}")
                except discord.Forbidden:
                    print("Error: Bot lacks permission to add Announce role.")
        elif str(payload.emoji) == "🎮":
            role = guild.get_role(GAMENIGHT_ROLE_ID)
            if role and role not in member.roles:
                try:
                    await member.add_roles(role)
                    print(f"Successfully added Game Night role to {member.name}")
                except discord.Forbidden:
                    print("Error: Bot lacks permission to add Game Night role.")


@bot.event
async def on_raw_reaction_remove(payload):
    guild = bot.get_guild(payload.guild_id)
    if not guild:
        return

    member = guild.get_member(payload.user_id)
    if not member:
        return

    # --- Role Panel Channel (通知ロール解除) ---
    if payload.channel_id == ROLE_PANEL_CHANNEL_ID:
        if str(payload.emoji) == "📢":
            role = guild.get_role(ANNOUNCE_ROLE_ID)
            if role and role in member.roles:
                try:
                    await member.remove_roles(role)
                    print(f"Successfully removed Announce role from {member.name}")
                except discord.Forbidden:
                    print("Error: Bot lacks permission to remove Announce role.")
        elif str(payload.emoji) == "🎮":
            role = guild.get_role(GAMENIGHT_ROLE_ID)
            if role and role in member.roles:
                try:
                    await member.remove_roles(role)
                    print(f"Successfully removed Game Night role from {member.name}")
                except discord.Forbidden:
                    print("Error: Bot lacks permission to remove Game Night role.")


# ==========================================
# Bot Ready Event (Rules, Apps & Role Panel Setup)
# ==========================================
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    
    bot.add_view(DMApplicationView())
    
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    
    # 1. Application Panel
    app_channel = bot.get_channel(APPLICATION_CHANNEL_ID)
    if app_channel:
        app_posted = False
        async for message in app_channel.history(limit=20):
            if message.author.id == bot.user.id and len(message.embeds) > 0:
                if any("RDoT Application Hub" in str(embed.title) for embed in message.embeds):
                    app_posted = True
                    break
        
        if not app_posted:
            embed = discord.Embed(
                title="RDoT Application Hub",
                description="Click the button below to start your recruitment process. The bot will send you the application questions directly via DM.",
                color=discord.Color.blue()
            )
            await app_channel.send(embed=embed, view=DMApplicationView())
            print("DM Application panel posted successfully.")

    # 2. Rules Panel
    channel = bot.get_channel(RULES_CHANNEL_ID)
    if channel:
        already_posted = False
        try:
            async for message in channel.history(limit=50):
                if message.author.id == bot.user.id and len(message.embeds) > 0:
                    if any("Robloxian Department of Transportation" in str(embed.title) for embed in message.embeds):
                        already_posted = True
                        if "✅" not in [str(r.emoji) for r in message.reactions]:
                            await message.add_reaction("✅")
                        break
        except Exception as e:
            print(f"Failed to read channel history: {e}")

        if not already_posted:
            print("Official rules not found. Posting now...")
            embed = discord.Embed(
                title="Robloxian Department of Transportation",
                description="Welcome to the RDoT. By joining this server, you agree to uphold the following standards.",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="1. Professionalism & Conduct",
                value="• Maintain Decorum: Always treat fellow members with respect. Toxic behavior, harassment, or unnecessary drama will not be tolerated.\n• Adhere to Regulations: All members must comply with standard Discord TOS as well as RZRM rules and guidelines at all times.",
                inline=False
            )
            embed.add_field(
                name="2. Operational Guidelines (RDoT Focus)",
                value="• Neutrality & Support: We are a logistical and infrastructure organization, not a combat faction. Do not engage in combat unless absolutely necessary for self-defense (TSD) or under authorized direct orders.\n• Chain of Command: Respect the hierarchy. Direct all operational inquiries to your respective Division Chiefs.\n• Cooperation, Not Reliance: We support other factions (the Military, Police, etc.), but we maintain our administrative independence. Do not compromise RDoT’s integrity by acting as an unofficial subordinate to other groups.",
                inline=False
            )
            embed.set_footer(text="Please react with the checkmark below to agree to the rules.")

            try:
                msg = await channel.send(embed=embed)
                await msg.add_reaction("✅")
                print("Official rules have been posted successfully.")
            except Exception as e:
                print(f"Failed to send rules: {e}")

    # 3. Notification Role Panel (NEW)
    role_panel_channel = bot.get_channel(ROLE_PANEL_CHANNEL_ID)
    if role_panel_channel:
        role_posted = False
        try:
            async for message in role_panel_channel.history(limit=50):
                if message.author.id == bot.user.id and len(message.embeds) > 0:
                    if any("RDoT Notification Roles" in str(embed.title) for embed in message.embeds):
                        role_posted = True
                        reactions = [str(r.emoji) for r in message.reactions]
                        if "📢" not in reactions:
                            await message.add_reaction("📢")
                        if "🎮" not in reactions:
                            await message.add_reaction("🎮")
                        break
        except Exception as e:
            print(f"Failed to read role panel channel history: {e}")

        if not role_posted:
            print("Role assignment panel not found. Posting now...")
            embed = discord.Embed(
                title="RDoT Notification Roles",
                description="React below to get pinged for specific server updates and events!",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="📢 Announcements Role",
                value="React with 📢 to receive notifications about server news, updates, and official announcements.",
                inline=False
            )
            embed.add_field(
                name="🎮 Game Night Role",
                value="React with 🎮 to receive notifications whenever we host community game nights and events.",
                inline=False
            )
            embed.set_footer(text="React to get the role. Unreact to remove it.")

            try:
                msg = await role_panel_channel.send(embed=embed)
                await msg.add_reaction("📢")
                await msg.add_reaction("🎮")
                print("Role assignment panel posted successfully.")
            except Exception as e:
                print(f"Failed to send role panel: {e}")

TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)

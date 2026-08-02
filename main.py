import os
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from aiohttp import web

# ==========================================
# Render Timeout Prevention (Async Web Server)
# ==========================================
async def handle_health_check(request):
    return web.Response(text="RDoT Bot is alive!")

async def start_dummy_server():
    app = web.Application()
    app.router.add_get("/", handle_health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Async dummy web server started on port {port}")


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
ROLE_PANEL_CHANNEL_ID = 1528397429932818513
EXAM_CHANNEL_ID = 1533040845345919057

# Initial Roles & Base Roles
INITIAL_ROLE_IDS = [
    1528079171891494922,
    1528076207122288810,
    1528077244201697320
]
RULES_AGREE_ROLE_ID = 1528404374429106366
TRAINEE_ROLE_ID = 1528077358857326625
ANNOUNCE_ROLE_ID = 1529012567874469920
GAMENIGHT_ROLE_ID = 1529012524400246795

# Timezone & Exam Promotion Role IDs
WOR_ROLE_ID = 1528410248954646528        # WOR (条件判定用)
EOR_ROLE_ID = 1528410287110357113        # EOR (条件判定用)

WOR_JTT_ROLE_ID = 1528075985184882870    # WOR JTT (合格時付与)
EOR_JTT_ROLE_ID = 1528077441254428843    # EOR JTT (合格時付与)
ALL_TZ_ROLE_ID = 1528075908941086860     # 全タイムゾーン用 (合格時必須付与)

# ==========================================
# Exam System Components (Qualification Exam)
# ==========================================
EXAM_QUESTIONS = [
    {
        "q": "Q1. What is the official motto and core purpose of the RDOT?",
        "options": ["A) Protect and Serve", "B) Keeping Robloxia Moving", "C) Safety First, Always", "D) Building the Future"],
        "answer": "b"
    },
    {
        "q": "Q2. What is the main objective of Evacuation & Supply Route Maintenance?",
        "options": ["A) To build race tracks", "B) To track down hostiles", "C) To inspect/clear major roadways for emergency/evacuees", "D) To block roads completely"],
        "answer": "c"
    },
    {
        "q": "Q3. Which of the following is considered a Critical Transport Asset?",
        "options": ["A) Traffic signals, signage, utility vehicles", "B) Heavy battle tanks", "C) Commercial buildings", "D) Personal vehicles"],
        "answer": "a"
    },
    {
        "q": "Q4. Who is required to follow the rules outlined in this handbook?",
        "options": ["A) Only Trainees", "B) Only Junior Technicians", "C) Only active field workers", "D) All personnel, including higher ranks"],
        "answer": "d"
    },
    {
        "q": "Q5. Which of the following is classified as a Severe Violation?",
        "options": ["A) Accidental procedural error", "B) Missing 1 day of work", "C) ToS violations, NSFW content, or hate speech", "D) Forgetting to salute"],
        "answer": "c"
    },
    {
        "q": "Q6. What is the penalty for AFK Farming?",
        "options": ["A) Demotion, suspension, or reprimand", "B) Verbal warning only", "C) No penalty", "D) Double time count"],
        "answer": "a"
    },
    {
        "q": "Q7. Unexcused absence of what duration is classified as a Minor Violation?",
        "options": ["A) More than 3 days", "B) More than 1 week", "C) Exceeding 2 months", "D) More than 1 year"],
        "answer": "c"
    },
    {
        "q": "Q8. What is the retake waiting period upon failing the exam?",
        "options": ["A) No waiting period", "B) 12 hours", "C) 24 hours", "D) 1 week"],
        "answer": "c"
    },
    {
        "q": "Q9. What is the requirement to advance from Trainee to Junior Transportation Technician?",
        "options": ["A) 60 Mins Duty Time", "B) Pass Qualification Exam", "C) Attend 3 events", "D) High Command appointment"],
        "answer": "b"
    },
    {
        "q": "Q10. How much duty time is required to advance from Junior Technician to Transportation Technician?",
        "options": ["A) 30 Minutes", "B) 60 Minutes", "C) 120 Minutes", "D) 240 Minutes"],
        "answer": "b"
    }
]

class StartExamView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Take Qualification Exam", style=discord.ButtonStyle.success, custom_id="start_exam_btn")
    async def start_exam(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user

        try:
            await interaction.response.send_message("The Qualification Exam has started in your DMs!", ephemeral=True)
        except Exception:
            pass

        try:
            intro_embed = discord.Embed(
                title="RDOT Junior Transportation Technician Qualification Exam",
                description=(
                    "Welcome to the qualification exam.\n"
                    "Please reply with the corresponding letter (**A, B, C, or D**) for each question.\n"
                    "You have 3 minutes per question. Good luck!\n\n"
                    "**Passing Score:** 8 / 10 (80%)"
                ),
                color=discord.Color.gold()
            )
            await user.send(embed=intro_embed)
        except discord.Forbidden:
            await interaction.followup.send(content=f"Error: Could not send a DM to {user.mention}. Please enable DMs from server members in your privacy settings.", ephemeral=True)
            return

        score = 0
        def check(m):
            return m.author.id == user.id and isinstance(m.channel, discord.DMChannel)

        for i, item in enumerate(EXAM_QUESTIONS):
            q_embed = discord.Embed(
                title=f"Question {i+1} / {len(EXAM_QUESTIONS)}",
                description=f"**{item['q']}**\n\n" + "\n".join(item["options"]),
                color=discord.Color.blue()
            )
            await user.send(embed=q_embed)

            try:
                msg = await bot.wait_for("message", timeout=180.0, check=check)
                user_ans = msg.content.strip().lower()
                if user_ans.startswith(item["answer"]):
                    score += 1
            except asyncio.TimeoutError:
                timeout_embed = discord.Embed(
                    title="Exam Cancelled",
                    description="Session timed out due to inactivity. You may restart from the server when ready.",
                    color=discord.Color.red()
                )
                await user.send(embed=timeout_embed)
                return

        # 結果判定
        passed = score >= 8
        result_color = discord.Color.green() if passed else discord.Color.red()
        result_title = "🎉 Exam Passed!" if passed else "❌ Exam Failed"
        result_desc = f"Your Score: **{score} / 10** (Passing Score: 8/10)\n\n"
        
        if passed:
            result_desc += "Congratulations! You have passed the Junior Transportation Technician Exam.\nYour results have been logged and your new roles have been assigned!"
            
            # --- ロール自動付与ロジック ---
            try:
                guild = interaction.guild
                if guild:
                    member = guild.get_member(user.id)
                    if member:
                        roles_to_add = []
                        
                        # 1. 全タイムゾーン用共通ロールを絶対に追加
                        all_tz_role = guild.get_role(ALL_TZ_ROLE_ID)
                        if all_tz_role:
                            roles_to_add.append(all_tz_role)

                        # 2. WOR か EOR かを判定して該当するJTTロールを追加
                        if any(r.id == WOR_ROLE_ID for r in member.roles):
                            wor_jtt_role = guild.get_role(WOR_JTT_ROLE_ID)
                            if wor_jtt_role:
                                roles_to_add.append(wor_jtt_role)

                        elif any(r.id == EOR_ROLE_ID for r in member.roles):
                            eor_jtt_role = guild.get_role(EOR_JTT_ROLE_ID)
                            if eor_jtt_role:
                                roles_to_add.append(eor_jtt_role)

                        # 付与を実行
                        if roles_to_add:
                            await member.add_roles(*roles_to_add)
                            print(f"Assigned JTT roles to {member.name}: {[r.name for r in roles_to_add]}")

            except Exception as e:
                print(f"Failed to assign JTT roles to {user.name}: {e}")
            # ----------------------------------

        else:
            result_desc += "Unfortunately, you did not reach the passing score. You may retake the exam after the 24-hour waiting period."

        res_embed = discord.Embed(title=result_title, description=result_desc, color=result_color)
        await user.send(embed=res_embed)

        # ログチャンネルへ通知
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            log_embed = discord.Embed(
                title="Exam Result Log",
                description=f"**User:** {user.mention} ({user.name})\n**Score:** {score}/10\n**Status:** {'Passed' if passed else 'Failed'}",
                color=result_color
            )
            await log_channel.send(embed=log_embed)


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
# Events
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

    if payload.channel_id == RULES_CHANNEL_ID and str(payload.emoji) == "✅":
        role = guild.get_role(RULES_AGREE_ROLE_ID)
        if role and role not in member.roles:
            try:
                await member.add_roles(role)
            except Exception as e:
                print(f"Failed to add role: {e}")

    elif payload.channel_id == ROLE_PANEL_CHANNEL_ID:
        if str(payload.emoji) == "📢":
            role = guild.get_role(ANNOUNCE_ROLE_ID)
            if role and role not in member.roles:
                await member.add_roles(role)
        elif str(payload.emoji) == "🎮":
            role = guild.get_role(GAMENIGHT_ROLE_ID)
            if role and role not in member.roles:
                await member.add_roles(role)


@bot.event
async def on_raw_reaction_remove(payload):
    guild = bot.get_guild(payload.guild_id)
    if not guild:
        return

    member = guild.get_member(payload.user_id)
    if not member:
        return

    if payload.channel_id == ROLE_PANEL_CHANNEL_ID:
        if str(payload.emoji) == "📢":
            role = guild.get_role(ANNOUNCE_ROLE_ID)
            if role and role in member.roles:
                await member.remove_roles(role)
        elif str(payload.emoji) == "🎮":
            role = guild.get_role(GAMENIGHT_ROLE_ID)
            if role and role in member.roles:
                await member.remove_roles(role)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    
    bot.add_view(DMApplicationView())
    bot.add_view(StartExamView())
    
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

    # 2. Exam Panel
    exam_channel = bot.get_channel(EXAM_CHANNEL_ID)
    if exam_channel:
        exam_posted = False
        async for message in exam_channel.history(limit=20):
            if message.author.id == bot.user.id and len(message.embeds) > 0:
                if any("RDOT Qualification Exam" in str(embed.title) for embed in message.embeds):
                    exam_posted = True
                    break
        
        if not exam_posted:
            embed = discord.Embed(
                title="RDOT Qualification Exam",
                description="Click the button below to take the Junior Transportation Technician Qualification Exam.\n\n"
                            "• **Format:** 10 Multiple Choice Questions (via DM)\n"
                            "• **Passing Score:** 80% (8/10)\n"
                            "• **Retake Cooldown:** 24 Hours",
                color=discord.Color.gold()
            )
            await exam_channel.send(embed=embed, view=StartExamView())

    # 3. Rules Panel
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
            embed = discord.Embed(
                title="Robloxian Department of Transportation",
                description="Welcome to the RDoT. By joining this server, you agree to uphold the following standards.",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="1. Professionalism & Conduct",
                value="• Maintain Decorum: Always treat fellow members with respect.\n• Adhere to Regulations: Compliance with Discord TOS and RZRM rules.",
                inline=False
            )
            embed.add_field(
                name="2. Operational Guidelines (RDoT Focus)",
                value="• Neutrality & Support: Logistical focus.\n• Chain of Command: Respect hierarchy.",
                inline=False
            )
            embed.set_footer(text="Please react with the checkmark below to agree to the rules.")

            try:
                msg = await channel.send(embed=embed)
                await msg.add_reaction("✅")
            except Exception as e:
                print(f"Failed to send rules: {e}")

    # 4. Notification Role Panel
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
            embed = discord.Embed(
                title="RDoT Notification Roles",
                description="React below to get pinged for specific server updates and events!",
                color=discord.Color.blue()
            )
            embed.add_field(name="📢 Announcements Role", value="React with 📢 to receive notifications.", inline=False)
            embed.add_field(name="🎮 Game Night Role", value="React with 🎮 to receive notifications.", inline=False)
            embed.set_footer(text="React to get the role. Unreact to remove it.")

            try:
                msg = await role_panel_channel.send(embed=embed)
                await msg.add_reaction("📢")
                await msg.add_reaction("🎮")
            except Exception as e:
                print(f"Failed to send role panel: {e}")


# ==========================================
# Main Async Runner
# ==========================================
async def main():
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        print("Error: DISCORD_TOKEN is missing.")
        return

    await start_dummy_server()
    
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())

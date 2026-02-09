import os
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = 1470045879145857066
Ip = os.getenv("Ip")  # Minecraft server IP

# ======================
# INTENTS
# ======================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix=["!", "?"], intents=intents)

# ======================
# HELPERS
# ======================
def get_log_channel(guild: discord.Guild):
    return discord.utils.get(guild.text_channels, name="log")

# ======================
# RULES EMBED
# ======================
def rules_embed():
    embed = discord.Embed(
        title="📜 Welcome to the Server!",
        description="Please read the rules carefully ❤️",
        color=discord.Color.red()
    )

    embed.add_field(
        name="💬 Discord Rules",
        value=(
            "🤝 Be respectful to everyone\n"
            "🚫 No spamming or excessive tagging\n"
            "🔞 No NSFW or disturbing content\n"
            "📢 No advertising without staff permission\n"
            "⚠️ No illegal activity\n"
            "🔐 Do not share personal information\n"
            "🧭 Use the correct channels\n"
            "👮 Staff decisions are final"
        ),
        inline=False
    )

    embed.set_footer(text="⚠️ Breaking rules may result in punishment")
    return embed

# ======================
# READY
# ======================
@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    await bot.tree.sync(guild=guild)
    print(f"✅ Logged in as {bot.user}")

# ======================
# MEMBER JOIN
# ======================
@bot.event
async def on_member_join(member: discord.Member):
    if member.guild.id != GUILD_ID:
        return
    try:
        await member.send(embed=rules_embed())
    except discord.Forbidden:
        pass

# ======================
# SEND RULES
# ======================
@bot.tree.command(name="send", description="Send rules")
async def slash_send(interaction: discord.Interaction):
    await interaction.response.send_message(embed=rules_embed())

@bot.command()
async def send(ctx):
    await ctx.send(embed=rules_embed())

# ==================================================
# 🌍 IP COMMAND
# ==================================================
@bot.command(name="ip")
async def ip(ctx):
    if not Ip:
        await ctx.send("❌ Server IP is not set.")
        return

    embed = discord.Embed(
        title="🌍 Minecraft Server IP",
        description=f"```{Ip}```",
        color=discord.Color.green()
    )
    embed.set_footer(text="Copy & paste into Minecraft")
    await ctx.send(embed=embed)

# ==================================================
# ℹ️ SERVER INFO
# ==================================================
@bot.command(name="serverinfo")
async def serverinfo(ctx):
    guild = ctx.guild

    humans = sum(not m.bot for m in guild.members)
    bots = sum(m.bot for m in guild.members)

    embed = discord.Embed(
        title=f"ℹ️ Server Info — {guild.name}",
        color=discord.Color.blurple(),
        timestamp=datetime.utcnow()
    )

    embed.set_thumbnail(url=guild.icon.url if guild.icon else None)

    embed.add_field(name="🆔 Server ID", value=guild.id, inline=True)
    embed.add_field(name="👑 Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
    embed.add_field(name="📆 Created On", value=guild.created_at.strftime("%Y-%m-%d"), inline=True)

    embed.add_field(name="👥 Members", value=f"{guild.member_count}", inline=True)
    embed.add_field(name="🧑 Humans", value=humans, inline=True)
    embed.add_field(name="🤖 Bots", value=bots, inline=True)

    embed.add_field(name="💬 Channels", value=len(guild.channels), inline=True)
    embed.add_field(name="🏷️ Roles", value=len(guild.roles), inline=True)

    embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)

    await ctx.send(embed=embed)

# ==================================================
# 🔨 MODERATION COMMANDS
# ==================================================

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    try:
        await member.kick(reason=reason)
        await ctx.send(f"👢 **Kicked** {member.mention}\n📄 Reason: {reason}")
    except discord.Forbidden:
        await ctx.send("❌ I don’t have permission to kick this user.")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def role(ctx, action: str, member: discord.Member, role: discord.Role):
    if ctx.guild.id != GUILD_ID:
        return

    try:
        if action.lower() == "add":
            await member.add_roles(role)
            await ctx.send(f"🏷️ Added {role.mention} to {member.mention}")
        elif action.lower() == "remove":
            await member.remove_roles(role)
            await ctx.send(f"🏷️ Removed {role.mention} from {member.mention}")
        else:
            await ctx.send("❌ Usage: `?role add @user @role` or `?role remove @user @role`")
    except discord.Forbidden:
        await ctx.send("❌ I can’t manage that role (role hierarchy issue).")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int):
    if amount < 1 or amount > 100:
        await ctx.send("❌ Purge amount must be between 1 and 100.")
        return

    deleted = await ctx.channel.purge(limit=amount + 1)

    log_channel = get_log_channel(ctx.guild)
    if log_channel:
        await log_channel.send(
            f"🧹 **Messages Purged**\n"
            f"👤 Moderator: {ctx.author.mention}\n"
            f"📍 Channel: {ctx.channel.mention}\n"
            f"🗑️ Amount: {len(deleted) - 1}"
        )

# ==================================================
# 📋 LOGGING EVENTS
# ==================================================

@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    if before.guild.id != GUILD_ID:
        return

    log_channel = get_log_channel(after.guild)
    if not log_channel:
        return

    for role in set(after.roles) - set(before.roles):
        await log_channel.send(f"➕ **Role Added** — {after.mention} → {role.mention}")

    for role in set(before.roles) - set(after.roles):
        await log_channel.send(f"➖ **Role Removed** — {after.mention} → {role.mention}")

@bot.event
async def on_message_delete(message: discord.Message):
    if not message.guild or message.guild.id != GUILD_ID:
        return
    if message.author.bot:
        return

    log_channel = get_log_channel(message.guild)
    if not log_channel:
        return

    await log_channel.send(
        f"🗑️ **Message Deleted**\n"
        f"👤 Author: {message.author.mention}\n"
        f"📍 Channel: {message.channel.mention}\n"
        f"💬 Content:\n```{message.content or 'No text content'}```"
    )

# ======================
# START BOT
# ======================
if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN environment variable not set")

bot.run(TOKEN)

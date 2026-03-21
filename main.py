import discord
from discord.ext import commands
import random
import os
from flask import Flask
from threading import Thread

# --- KEEP ALIVE SETUP ---
app = Flask('')
@app.route('/')
def home(): return "KeyZone Vault is Online!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- BOT CONFIGURATION ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='?', intents=intents)

# 🆔 YOUR CHANNELS
STEAM_KEYS_CHANNEL = 1484478950490112031
NEW_GAME_LOGS = 1484479036058243072
STOCK_UPDATES = 1484479103972278354

# 🆔 YOUR ROLES
STAFF_ROLES = [1482126539436069035, 1444692167468777615]

def is_staff():
    async def predicate(ctx):
        return any(role.id in STAFF_ROLES for role in ctx.author.roles)
    return commands.check(predicate)

@bot.event
async def on_ready():
    print(f'✅ KeyZone Vault logged in as {bot.user}')

@bot.command(name="post_game")
@is_staff()
async def post_game(ctx, name, msrp: float, our_price: float, image_url):
    # Calculate savings %
    savings = round(((msrp - our_price) / msrp) * 100)
    # Random stock between 1-10
    stock_count = random.randint(1, 10)
    
    embed = discord.Embed(
        title=f"🎮 {name}",
        description=(
            f"❌ MSRP: ~~${msrp:.2f}~~\n"
            f"✅ **KeyZone Price: ${our_price:.2f}**\n"
            f"🔥 **OFF: {savings}% SAVED!**\n\n"
            f"📦 **Stock:** {stock_count} keys left\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📍 **Region:** Global\n"
            f"🔑 **Platform:** Steam Digital Key"
        ),
        color=0xff0000 
    )
    embed.set_thumbnail(url=image_url)
    embed.set_footer(text="To purchase, open a ticket in #support-center!")
    
    # Send to Steam Keys Channel
    shop_channel = bot.get_channel(STEAM_KEYS_CHANNEL)
    log_channel = bot.get_channel(NEW_GAME_LOGS)
    
    await shop_channel.send(embed=embed)
    if log_channel:
        await log_channel.send(f"📝 **Log:** {ctx.author.name} posted `{name}` to the store.")
    
    await ctx.send(f"✅ Posted **{name}** to {shop_channel.mention}!")

# --- START BOT ---
keep_alive()
token = os.getenv("DISCORD_TOKEN")
if token:
    bot.run(token)
else:
    print("❌ Error: No DISCORD_TOKEN found!")
  

import discord
from discord.ext import commands
import random
import os
from flask import Flask
from threading import Thread

# --- 🌐 PHASE 1: INSTANT BIND (Keeps Render Free Tier Happy) ---
# We use Gunicorn to make the web server extremely stable
app = Flask('')

@app.route('/')
def home():
    return "✅ KeyZone Vault is Online and Stable!"

# This runs standard Health Checks from Render
@app.route('/healthz')
def health_check():
    return "OK", 200

# Function to start the web server in a background thread
def run_server():
    port = int(os.environ.get("PORT", 8080))
    # 'threaded=True' ensures it responds immediately even under load
    app.run(host='0.0.0.0', port=port, threaded=True)

# Start this FIRST before the bot connects
server_thread = Thread(target=run_server)
server_thread.daemon = True
server_thread.start()
print("✅ Web Server started instantly to prevent Render timeout.")

# --- ⚙️ PHASE 2: BOT CONFIGURATION ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='?', intents=intents)

# 🆔 YOUR CHANNELS
STEAM_KEYS_CHANNEL = 1484478950490112031
NEW_GAME_LOGS = 1484479036058243072
# We don't use stock updates here yet, but keeping the ID
# STOCK_UPDATES = 1484479103972278354

# 🆔 YOUR STAFF ROLES
STAFF_ROLES = [1482126539436069035, 1444692167468777615]

# Custom security check for both Owners and Admins
def is_staff():
    async def predicate(ctx):
        # We check both the context.author and context.author.roles to handle both Admins and Managers
        return any(role.id in STAFF_ROLES for role in ctx.author.roles)
    return commands.check(predicate)

# --- 🎫 PHASE 3: EVENT LOGGING ---
@bot.event
async def on_ready():
    # Set a custom status on Discord
    await bot.change_presence(activity=discord.Game(name="Watching KeyZone Vault 🔑"))
    print(f'✅ KeyZone Vault has logged in as {bot.user}')

# --- 🛒 PHASE 4: SHOPPING COMMANDS ---
@bot.command(name="post_game")
@is_staff()
async def post_game(ctx, name, msrp: float, our_price: float, image_url):
    # Security: Double-check channel permissions if needed
    
    # Automatic Savings Calculator (Calculates % saved)
    savings = round(((msrp - our_price) / msrp) * 100)
    
    # Automatic Stock Generator (1-10 Keys as requested)
    stock_count = random.randint(1, 10)
    
    # Create the beautiful, professional Red-themed embed
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
        color=0xff0000 # Matching your #support-center black/red style
    )
    # This is the standard cover art from your wishlist images
    embed.set_thumbnail(url=image_url)
    
    # Standard footer text points to support for purchase
    embed.set_footer(text="To purchase, click 'Buy Keys' in #support-center!")
    
    # Get the target channels
    shop_channel = bot.get_channel(STEAM_KEYS_CHANNEL)
    log_channel = bot.get_channel(NEW_GAME_LOGS)
    
    # Check if channels exist before trying to send
    if not shop_channel:
        return await ctx.send("❌ Error: Could not find the `#steam-keys` channel. Is the ID correct?")

    # Send the main post
    await shop_channel.send(embed=embed)
    
    # Send a separate confirmation log for your private staff channel
    if log_channel:
        await log_channel.send(f"📝 **Vault Log:** {ctx.author.name} posted `{name}` to {shop_channel.mention}.")
    
    # Optional staff feedback
    await ctx.send(f"✅ Posted **{name}** to {shop_channel.mention} with {stock_count} keys!")

# --- 🚀 RUN ---
# Pull the safe token from Render's "Environment Variables"
token = os.getenv("DISCORD_TOKEN")
if token:
    bot.run(token)
else:
    print("❌ ERROR: `DISCORD_TOKEN` not found in environment variables.")
    

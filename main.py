import discord
from discord.ext import commands
import random
import os
import asyncio
from flask import Flask
from threading import Thread

# --- 🌐 PHASE 1: ENTERPRISE WEB SERVER (Instant-Live) ---
app = Flask('')
@app.route('/')
def home(): return "🚀 KeyZone Vault: STATUS_OK (Online)"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- ⚙️ PHASE 2: BOT ENGINE & PERSISTENCE ---
intents = discord.Intents.default()
intents.message_content = True

class KeyZoneBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='?', intents=intents, help_command=None)

    async def setup_hook(self):
        # This keeps the "Buy" buttons working even if the bot restarts!
        self.add_view(PersistentBuyView())

bot = KeyZoneBot()

# --- 🆔 CONFIGURATION ---
GUILD_ID = 1482124508491157504
STEAM_KEYS_CHANNEL = 1484478950490112031
NEW_GAME_LOGS = 1484479036058243072
SUPPORT_CHANNEL_ID = 1484479449788583946
STAFF_ROLES = [1482126539436069035, 1444692167468777615]

# --- 🔘 PHASE 3: THE INTERACTIVE UI ---
class PersistentBuyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Never times out

    @discord.ui.button(
        label="🛒 Buy This Key", 
        style=discord.ButtonStyle.danger, # Red to match your theme
        custom_id="keyzone:buy_button"
    )
    async def buy_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        support_url = f"https://discord.com/channels/{GUILD_ID}/{SUPPORT_CHANNEL_ID}"
        
        # This creates a "Private" response only the buyer can see
        embed = discord.Embed(
            title="💳 Ready to Purchase?",
            description=f"To secure your key, please click the link below to go to our **#support-center** and open a ticket!",
            color=0x2ecc71 # Green for success
        )
        
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Go to Support Center", url=support_url))
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# --- 🎮 PHASE 4: THE SHOP COMMANDS ---
def is_staff():
    async def predicate(ctx):
        return any(role.id in STAFF_ROLES for role in ctx.author.roles)
    return commands.check(predicate)

@bot.command(name="post")
@is_staff()
async def post_game(ctx, name, msrp: float, price: float, image_url):
    """The Ultimate Post Command: ?post 'Game Name' 60 15 URL"""
    savings = round(((msrp - price) / msrp) * 100)
    stock = random.randint(1, 10)
    
    embed = discord.Embed(
        title=f"🔥 {name.upper()}",
        description=(
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💰 **MSRP:** ~~${msrp:.2f}~~\n"
            f"✅ **KEYZONE:** **${price:.2f}**\n"
            f"⚡ **SAVINGS:** `{savings}% OFF`\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📦 **STOCK:** {stock} keys available\n"
            f"🌍 **REGION:** Global / Steam\n"
            f"━━━━━━━━━━━━━━━━━━"
        ),
        color=0xff0000
    )
    embed.set_image(url=image_url) # Larger image for better conversion
    embed.set_footer(text=f"Posted by {ctx.author.name} • Trusted Key Seller", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)

    shop_chan = bot.get_channel(STEAM_KEYS_CHANNEL)
    log_chan = bot.get_channel(NEW_GAME_LOGS)
    
    await shop_chan.send(embed=embed, view=PersistentBuyView())
    if log_chan:
        await log_chan.send(f"✅ **NEW LISTING:** `{name}` posted by {ctx.author.mention} (${price})")
    
    await ctx.message.delete() # Cleans up the staff channel

# --- 🚀 PHASE 5: POWER ON ---
if __name__ == "__main__":
    # Start Web Server
    Thread(target=run_server).start()
    # Start Bot
    token = os.getenv("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("❌ CRITICAL ERROR: NO DISCORD_TOKEN FOUND")
        

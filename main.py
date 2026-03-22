import discord
from discord.ext import commands, tasks
from discord import app_commands
import random
import string
import sqlite3
import time

# ==========================
# CONFIGURATION
# ==========================
TOKEN = "YOUR_BOT_TOKEN_HERE"
SUPPORT_CHANNEL_ID = 1484479449788583946
STORE_CHANNEL_ID = 1484478950490112031
NEW_GAMES_CHANNEL_ID = 1484479036058243072
ADMIN_ROLE_ID = 1482126539436069035 
PAYMENT_INFO = "PayPal: keyzone1help@gmail.com"

# ==========================
# DATABASE SETUP
# ==========================
conn = sqlite3.connect("orders.db")
cursor = conn.cursor()

# Table for Orders
cursor.execute(""" 
CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY, user_id INTEGER, game TEXT, 
    status TEXT, created_at INTEGER, price REAL, cost REAL 
) """)

# Table for Products (Catalog)
cursor.execute("""
CREATE TABLE IF NOT EXISTS product_catalog (
    name TEXT PRIMARY KEY, steam REAL, price REAL, cost REAL, image TEXT
) """)
conn.commit()

# ==========================
# BOT CLASS
# ==========================
class StoreBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Starts the loops and syncs slash commands
        auto_post_products.start()
        await self.tree.sync()
        print("✅ Slash commands synced and loops started.")

bot = StoreBot()

def generate_order_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

# ==========================
# VIEWS & MODALS
# ==========================

class BuyView(discord.ui.View):
    def __init__(self, game, price, cost):
        super().__init__(timeout=None)
        self.game = game
        self.price = price
        self.cost = cost

    @discord.ui.button(label="Buy Now", style=discord.ButtonStyle.green, emoji="🛒")
    async def buy(self, interaction: discord.Interaction, button: discord.ui.Button):
        order_id = generate_order_id()
        created_at = int(time.time())

        cursor.execute("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (order_id, interaction.user.id, self.game, "PENDING", created_at, self.price, self.cost))
        conn.commit()

        guild = interaction.guild
        admin_role = guild.get_role(ADMIN_ROLE_ID)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        if admin_role:
            overwrites[admin_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel = await guild.create_text_channel(name=f"order-{order_id}", overwrites=overwrites)

        embed = discord.Embed(title="🧾 Order Invoice", color=discord.Color.gold())
        embed.add_field(name="Order ID", value=f"`{order_id}`", inline=False)
        embed.add_field(name="Product", value=self.game, inline=True)
        embed.add_field(name="Total Due", value=f"**${self.price}**", inline=True)
        embed.add_field(name="Payment Method", value=PAYMENT_INFO, inline=False)
        embed.set_footer(text="Send payment then ping staff in this channel.")

        await channel.send(f"Welcome {interaction.user.mention}! Staff will assist you shortly.", embed=embed)
        await interaction.response.send_message(f"✅ Private ticket created: {channel.mention}", ephemeral=True)

class AddGameModal(discord.ui.Modal, title='Add New Game to Catalog'):
    g_name = discord.ui.TextInput(label='Game Name', placeholder='e.g. Elden Ring')
    g_steam = discord.ui.TextInput(label='Steam Price', placeholder='60.00')
    g_price = discord.ui.TextInput(label='Your Store Price', placeholder='45.00')
    g_cost = discord.ui.TextInput(label='Your Purchase Cost', placeholder='30.00')
    g_image = discord.ui.TextInput(label='Image Link (Direct URL)', placeholder='https://i.imgur.com/example.png')

    async def on_submit(self, interaction: discord.Interaction):
        try:
            name = self.g_name.value
            steam = float(self.g_steam.value)
            price = float(self.g_price.value)
            cost = float(self.g_cost.value)
            img = self.g_image.value

            cursor.execute("INSERT OR REPLACE INTO product_catalog VALUES (?, ?, ?, ?, ?)",
                           (name, steam, price, cost, img))
            conn.commit()
            await interaction.response.send_message(f"✅ **{name}** added! It will appear in the store on the next refresh.", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ Error: Use numbers for prices (e.g. 19.99).", ephemeral=True)

# ==========================
# SLASH COMMANDS
# ==========================

@bot.tree.command(name="setup", description="Add a new game to the store (Admin Only)")
async def setup(interaction: discord.Interaction):
    if interaction.user.get_role(ADMIN_ROLE_ID):
        await interaction.response.send_modal(AddGameModal())
    else:
        await interaction.response.send_message("❌ You do not have the required role to use this.", ephemeral=True)

@bot.tree.command(name="search", description="Search for a game in our shop")
async def search(interaction: discord.Interaction, query: str):
    cursor.execute("SELECT * FROM product_catalog WHERE name LIKE ?", (f"%{query}%",))
    results = cursor.fetchall()

    if not results:
        return await interaction.response.send_message(f"❌ No games found matching '{query}'.", ephemeral=True)

    if len(results) == 1:
        name, steam, price, cost, img = results[0]
        embed = discord.Embed(title=name, color=discord.Color.blue())
        embed.add_field(name="Retail", value=f"~~${steam}~~", inline=True)
        embed.add_field(name="Our Price", value=f"**${price}**", inline=True)
        embed.set_image(url=img)
        await interaction.response.send_message(embed=embed, view=BuyView(name, price, cost))
    else:
        embed = discord.Embed(title=f"Results for '{query}'", color=discord.Color.blue())
        desc = ""
        for r in results[:10]:
            desc += f"• **{r[0]}** - ${r[2]}\n"
        embed.description = desc
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.command()
async def dashboard(ctx):
    # Only allow the specific Admin Role ID to use this
    if ctx.author.get_role(ADMIN_ROLE_ID):
        cursor.execute("SELECT COUNT(*), SUM(price), SUM(price - cost) FROM orders")
        res = cursor.fetchone()
        embed = discord.Embed(title="📊 Store Statistics", color=discord.Color.purple())
        embed.add_field(name="Total Sales", value=res[0] or 0)
        embed.add_field(name="Gross Revenue", value=f"${res[1] or 0:.2f}")
        embed.add_field(name="Total Profit", value=f"${res[2] or 0:.2f}")
        await ctx.send(embed=embed)

# ==========================
# BACKGROUND TASKS
# ==========================

@tasks.loop(hours=1)
async def auto_post_products():
    channel = bot.get_channel(STORE_CHANNEL_ID)
    if not channel: return

    # Clear old shop messages to keep it fresh
    await channel.purge()

    cursor.execute("SELECT * FROM product_catalog")
    rows = cursor.fetchall()
    
    for row in rows:
        name, steam, price, cost, img = row
        savings = int((1 - price/steam) * 100) if steam > 0 else 0
        
        embed = discord.Embed(title=f"🔥 {name}", color=discord.Color.green())
        embed.add_field(name="Steam Price", value=f"~~${steam}~~", inline=True)
        embed.add_field(name="Our Deal", value=f"**${price}**", inline=True)
        embed.add_field(name="Discount", value=f"{savings}% OFF", inline=True)
        embed.set_image(url=img)

        # Post the game with its specific Buy button
        await channel.send(embed=embed, view=BuyView(name, price, cost))

@bot.event
async def on_ready():
    print(f"✅ {bot.user} is now active!")

bot.run(TOKEN)
        

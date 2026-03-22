import discord
from discord.ext import commands, tasks
import random
import string
import sqlite3
import time
import os

intents = discord.Intents.default() intents.message_content = True intents.guilds = True intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

==========================

CONFIG

==========================

STORE_CHANNEL_ID = 1484478950490112031 NEW_GAMES_CHANNEL_ID = 1484479036058243072 ADMIN_ROLE_IDS = [1482126539436069035, 1444692167468777615]  # Manager/Owner + Admin  # Add more role IDs here (Admin, Manager, Owner) PAYMENT_INFO = "PayPal: keyzone1help@gmail.com"

==========================

DATABASE

==========================

conn = sqlite3.connect("store.db") cursor = conn.cursor()

cursor.execute(""" CREATE TABLE IF NOT EXISTS products ( name TEXT PRIMARY KEY, steam REAL, price REAL, image TEXT ) """)

cursor.execute(""" CREATE TABLE IF NOT EXISTS orders ( order_id TEXT PRIMARY KEY, user_id INTEGER, game TEXT, status TEXT, created_at INTEGER ) """) conn.commit()

==========================

UTIL

==========================

def generate_order_id(): return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

==========================

BUY VIEW

==========================

class BuyView(discord.ui.View): def init(self, game, price): super().init(timeout=None) self.game = game self.price = price

@discord.ui.button(label="Buy", style=discord.ButtonStyle.green, emoji="🛒")
async def buy(self, interaction: discord.Interaction, button: discord.ui.Button):
    order_id = generate_order_id()
    cursor.execute("INSERT INTO orders VALUES (?, ?, ?, ?, ?)",
                   (order_id, interaction.user.id, self.game, "PENDING", int(time.time())))
    conn.commit()

    embed = discord.Embed(title="🧾 Order Created")
    embed.add_field(name="Order ID", value=order_id)
    embed.add_field(name="Game", value=self.game)
    embed.add_field(name="Price", value=f"${self.price}")
    embed.add_field(name="Payment", value=PAYMENT_INFO)

    await interaction.user.send(embed=embed)
    await interaction.response.send_message("Check your DM for payment.", ephemeral=True)

==========================

POST PRODUCT

==========================

async def post_product(channel, product): name, steam, price, image = product

discount = int((1 - price/steam) * 100) if steam else 0

embed = discord.Embed(title=name)
embed.add_field(name="Steam Price", value=f"${steam}")
embed.add_field(name="Your Price", value=f"${price}")
embed.add_field(name="Discount", value=f"{discount}%")
embed.set_image(url=image)

await channel.send(embed=embed, view=BuyView(name, price))

==========================

COMMANDS (ADMIN)

==========================

@bot.command() @commands.check(lambda ctx: any(role.id in ADMIN_ROLE_IDS for role in ctx.author.roles)) async def addgame(ctx, name, steam: float, price: float, image): cursor.execute("INSERT OR REPLACE INTO products VALUES (?, ?, ?, ?)", (name, steam, price, image)) conn.commit()

channel = bot.get_channel(STORE_CHANNEL_ID)
await post_product(channel, (name, steam, price, image))

new_channel = bot.get_channel(NEW_GAMES_CHANNEL_ID)
if new_channel:
    await new_channel.send(f"🔥 New game added: **{name}** for ${price}")

await ctx.send(f"Game {name} added.")

@bot.command() @commands.check(lambda ctx: any(role.id in ADMIN_ROLE_IDS for role in ctx.author.roles)) async def removegame(ctx, name): cursor.execute("DELETE FROM products WHERE name=?", (name,)) conn.commit() await ctx.send(f"Game {name} removed.")

@bot.command() @commands.check(lambda ctx: any(role.id in ADMIN_ROLE_IDS for role in ctx.author.roles)) async def editprice(ctx, name, new_price: float): cursor.execute("UPDATE products SET price=? WHERE name=?", (new_price, name)) conn.commit() await ctx.send(f"Updated {name} price to ${new_price}.")

==========================

LOAD PRODUCTS ON START

==========================

@bot.event async def on_ready(): print(f"Logged in as {bot.user}")

channel = bot.get_channel(STORE_CHANNEL_ID)
if not channel:
    return

cursor.execute("SELECT * FROM products")
products = cursor.fetchall()

for p in products:
    await post_product(channel, p)

bot.run("YOUR_BOT_TOKEN")

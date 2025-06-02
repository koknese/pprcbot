import discord
import os
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from discord import app_commands, Embed, ui
from datetime import datetime
from misc.paginator import Pagination
import sqlite3
import requests
import json
from discord.app_commands import Group, command
from discord.ext.commands import GroupCog

load_dotenv('../.version', override=True)
load_dotenv('../.config', override=True)
server_id = int(os.getenv('SERVER_ID'))
version = os.getenv('VERSION')
confirmationChannel = int(os.getenv('CONFIRMATION_CHANNEL'))
ID_API_ENDPOINT = "https://users.roblox.com/v1/usernames/users"
logo = "https://media.discordapp.net/attachments/1379158277887365192/1379161729572929659/Phoenix.png?ex=683f3bf3&is=683dea73&hm=bfc7c64dfc07adbe067950b705012cfe5b75fcaaf5b7f596310dec44729000c6&=&format=webp&quality=lossless&width=622&height=604"

class Experience(GroupCog, group_name="exp", group_description="Phoenix EXP system"):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @command(
        name="modify",
        description="Modify someone's EXP"
    )
    @app_commands.guilds(discord.Object(id=server_id))
    @app_commands.describe(exp="Set the number to a negative number to deduct EXP.")
    async def post(self, interaction:discord.Interaction, user:discord.Member, exp:float):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("You are lacking permissions!", ephemeral=True)
            return

        try:
            print((user))
            print(type(user))
            print(user.id)
            print(type(user.id))
            conn = sqlite3.connect('data.db')
            c = conn.cursor()
            c.execute("SELECT * FROM ids WHERE discord_id = ?", (user.id,))
            row = c.fetchone()
            if row:
                c.execute(f"UPDATE ids SET exp = exp + ? WHERE discord_id = ?", (exp, user.id)) # fix so lazy i am ashamed of myself
                conn.commit()
                c.close()
                conn.close()
                embed = discord.Embed(title="EXP added!",
                          colour=0x57e389,
                          timestamp=datetime.now())
                embed.set_footer(text=f"Phoenix v.{version}", icon_url=logo)
                await interaction.response.send_message(embed=embed)
            else:
                embed = discord.Embed(title="Phoenix eID for specified user not found!", colour=0xc01c28)
                embed.set_footer(text=f"Phoenix v.{version}", icon_url=logo)
                await interaction.response.send_message(embed=embed)
        except sqlite3.OperationalError:
                embed = discord.Embed(title="SQL: Table not found!", colour=0xc01c28, description="Perhaps a database hasn't been generated yet? Creating an ID creates one!")
                embed.set_footer(text=f"Phoenix v.{version}", icon_url=logo)
                await interaction.response.send_message(embed=embed)
        except sqlite3.ProgrammingError:
            embed = discord.Embed(title="SQL: Database closed!", colour=0xc01c28, description="Either database is currently opened in a browser by the developer or something has gone terribly wrong. :slight_smile:")
            embed.set_footer(text=f"Phoenix v.{version}", icon_url=logo)
            await interaction.response.send_message(embed=embed)
        except discord.app_commands.MissingPermissions:
            await interaction.response.send_message("You are lacking permissions!", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Experience(bot), guild=discord.Object(id=server_id))

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

def getHeadshot(roblox_username):
    userRawHeadshot = f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={getUserId(roblox_username)}&format=png&size=352x352"
    response = requests.get(userRawHeadshot)
    if response.status_code == 200:
        userParsedHeadshot = response.json()
        userFinalHeadshot = userParsedHeadshot['data'][0]['imageUrl']
        print(f"getHeadshot :: Fetched headshot of {roblox_username}")
        return userFinalHeadshot
    else:
        placeholderImg = "https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fi.imgflip.com%2Fd0tb7.jpg&f=1&nofb=1&ipt=e1c23bf6c418254a56c19b09cc9ece6238ead393652e54278f0d535f9fb81c56"
        return placeholderImg

async def getID(gettingMethod, discordID):
        try:
            conn = sqlite3.connect('data.db')
            c = conn.cursor()
            c.execute(f"SELECT * FROM ids WHERE {gettingMethod} = ?", (discordID,))
            row = c.fetchone()
            if row:
                roblox_username_db = row[0]
                discord_id_db = row[1]
                rank_db = row[2]
                exp_db = row[3]
                embed = discord.Embed(colour=0xf66151)
                embed.set_author(name="SECURITAS DIGITAL ID")

                embed.add_field(name="Roblox Username",
                                value=roblox_username_db,
                                inline=False)
                embed.add_field(name="Discord ID",
                                value=f"{discord_id_db} | <@{discord_id_db}>",
                                inline=False)
                embed.add_field(name="EXP",
                                value=exp_db,
                                inline=False)
                embed.add_field(name="Rank",
                                value=rank_db,
                                inline=False)
                
                embed.set_footer(text=f"Phoenix v.{version}", icon_url=logo)
                embed.set_thumbnail(url=getHeadshot(roblox_username_db))
                c.close()
                conn.close()
                return embed
            else:
                embed = discord.Embed(title="ID not found!", colour=0xc01c28)
                embed.set_footer(text=f"Phoenix v.{version}", icon_url=logo)
                return embed
        except sqlite3.OperationalError:
                embed = discord.Embed(title="SQL: Table not found!", colour=0xc01c28, description="Perhaps a database hasn't been generated yet? Creating an ID creates one!")
                embed.set_footer(text=f"Securitas Managment v.{version}", icon_url=logo)
                return embed

def getUserId(username):
    requestPayload = {
            "usernames": [
                username
            ],
            "excludeBannedUsers": True # Whether to include banned users within the request, change this as you wish
           }
        
    responseData = requests.post(ID_API_ENDPOINT, json=requestPayload)
        
            # Make sure the request succeeded
    assert responseData.status_code == 200
        
    userId = responseData.json()["data"][0]["id"]
        
    print(f"getUserId :: Fetched user ID of username {username} -> {userId}")
    return userId

class Identificationui(ui.Modal, title='You are signing up for a Phoenix eID ©'):
   username = ui.TextInput(label='Roblox username', placeholder="Type your username here...", style=discord.TextStyle.short)
   async def on_submit(self, interaction: discord.Interaction):
       roblox_username = self.username.value
       applicant = interaction.user.id
       class Confirmapplication(discord.ui.View):
           def __init__(self, roblox_username, discordid, *, timeout=43200):
               super().__init__(timeout=timeout)
               self.roblox_username = roblox_username.lower()
               self.discordid = applicant

           @discord.ui.button(label="Accept application",style=discord.ButtonStyle.green)
           async def accept_application(self, interaction:discord.Interaction, view: discord.ui.View):
               try:
                   conn = sqlite3.connect('data.db')
                   c = conn.cursor()
        
                   c.execute("""CREATE TABLE IF NOT EXISTS ids(
                                    roblox_username TEXT NOT NULL,
                                    discord_id BIGINT NOT NULL UNIQUE,
                                    rank TEXT,
                                    exp INT
                                    )""")
                   c.execute("SELECT 1 FROM ids WHERE roblox_username = ? LIMIT 1;", (self.roblox_username,))
                   if c.fetchone():
                       embed = discord.Embed(title="User with the same Roblox username already is registered!", colour=0xc01c28)
                       embed.set_footer(text=f"Phoenix v.{version}")
                       await interaction.response.send_message(embed=embed)
                       c.close()
                       conn.close()
                       return
        
                   c.execute("""INSERT INTO ids (roblox_username, discord_id, exp)
                                    VALUES (?, ?, ?);
                                 """, (self.roblox_username, self.discordid, 0))
        
                   embed = discord.Embed(title=f"User registered to database by {interaction.user}!", colour=0x2ec27e)
                   embed.set_footer(text=f"Phoenix v.{version}")
                       
                   conn.commit()
                   c.close()
                   conn.close()

                   await interaction.response.send_message(embed=embed)
                   print(self.discordid)
                   applicant = interaction.client.get_user(self.discordid)
                   await applicant.send(f"Your Phoenix eID application was accepted by {interaction.user}!\nView it with ***/id view_own***.")
               except Exception as e:
                   embed = discord.Embed(title="[Errno 4] Unknown error!", description=str(e), colour=0xa51d2d)
                   await interaction.response.send_message(embed=embed)

       class Confirmpreview(discord.ui.View):
           def __init__(self, *, timeout=180):
               super().__init__(timeout=timeout)
               self.embed = embed
               self.confirmationChannel = confirmationChannel

           @discord.ui.button(label="Accept preview",style=discord.ButtonStyle.green)
           async def accept_preview(self, interaction:discord.Interaction, view: discord.ui.View):
               await interaction.response.send_message("Preview accepted. Your ID was sent to the moderation team for further approval.", ephemeral=True)
               confirmationChannelParsed = interaction.client.get_channel(self.confirmationChannel)
               await confirmationChannelParsed.send("You have received an ID application!", embed=embed, view=Confirmapplication(roblox_username, applicant))

       userRawHeadshot = f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={getUserId(self.username.value)}&format=png&size=352x352"
       response = requests.get(userRawHeadshot)

       if response.status_code == 200:
           userParsedHeadshot = response.json()
           userFinalHeadshot = userParsedHeadshot['data'][0]['imageUrl']
       else:
           embed = discord.Embed(title="[Errno 4] Unknown error!", description=response, colour=0xa51d2d)
           embed.set_image(url=f'https://http.cat/{response.status_code}.jpg')
           embed.set_footer(text=f"Phoenix v.{version}")
           await interaction.response.send_message(embed=embed)

       embed = discord.Embed(colour=0xf66151,
                      timestamp=datetime.now())

       embed.set_author(name="PHOENIX eID (PREVIEW MODE)")

       embed.add_field(name="Roblox Username",
                       value=self.username.value,
                       inline=False)
       embed.add_field(name="Discord ID",
                       value=f"{interaction.user.id} | <@{interaction.user.id}>",
                       inline=False)
       
       embed.set_footer(text=f"Phoenix v.{version}")
       embed.set_thumbnail(url=userFinalHeadshot)

       await interaction.response.send_message(embed=embed, ephemeral=True, view=Confirmpreview())
   async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
       if interaction.response.is_done():
           embed = discord.Embed(title="[Errno 4] Unknown error!", description="God give us strength.", colour=0xa51d2d)
           embed.set_image(url=f'https://http.cat/{error.status}.jpg')
           embed.set_footer(text=f"Phoenix v.{version}")
           await interaction.send_message(embed=embed)
       else:
           embed = discord.Embed(title="[Errno 4] Unknown error!", description="God give us strength.", colour=0xa51d2d)
           embed.set_image(url=f'https://http.cat/{error.status}.jpg')
           embed.set_footer(text=f"Phoenix v.{version}")
           await interaction.response.send_message(error, embed=embed)
        
class Identification(GroupCog, group_name="id", group_description="Phoenix eID system"):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @command(
        name="create",
        description="Create your Phoenix eID"
    )
    @app_commands.guilds(discord.Object(id=server_id))
    async def post(self, interaction:discord.Interaction):
        modal = Identificationui()
        await interaction.response.send_modal(modal)

    @command(
            name="view_from_roblox_username",
            description="Find an ID using a Roblox username"
    )
    @app_commands.guilds(discord.Object(id=server_id))
    async def find_by_roblox(self, interaction:discord.Interaction, roblox_username:str):
        await interaction.response.send_message(":mag::white_check_mark: ID found!", embed=await getID("roblox_username", roblox_username), ephemeral=True)

    @command(
            name="delete",
            description="Delete an ID using a Roblox username"
    )
    @app_commands.guilds(discord.Object(id=server_id))
    async def delete(self, interaction:discord.Interaction, roblox_username:str):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("You are lacking permissions!", ephemeral=True)
            return

        try:
            conn = sqlite3.connect('data.db')
            c = conn.cursor()
            c.execute("SELECT * FROM ids WHERE roblox_username = ?", (roblox_username.lower(),))
            row = c.fetchone()
            if row:
                c.execute("DELETE FROM ids WHERE roblox_username = ?", (roblox_username.lower(),))
                conn.commit()
                c.close()
                conn.close()
                embed = discord.Embed(title="ID deleted!",
                          description=f"ID {roblox_username} was deleted succesfully!",
                          colour=0x57e389,
                          timestamp=datetime.now())
                embed.set_footer(text=f"Phoenix v.{version}", icon_url=logo)
                await interaction.response.send_message(embed=embed)
                c.close()
                conn.close()
            else:
                embed = discord.Embed(title="ID not found!", colour=0xc01c28)
                embed.set_footer(text=f"Phoenix v.{version}", icon_url=logo)
                await interaction.response.send_message(embed=embed)
        except sqlite3.OperationalError:
                embed = discord.Embed(title="SQL: Table not found!", colour=0xc01c28, description="Perhaps a database hasn't been generated yet? Creating an ID creates one!")
                embed.set_footer(text=f"Phoenix v.{version}", icon_url=logo)
                await interaction.response.send_message(embed=embed)
        except discord.errors.MissingPermissions:
            await interaction.response.send_message("You are lacking permissions!", ephemeral=True)

    @command(
            name="view_from_discord_account",
            description="Find an ID using a Discord username"
    )
    @app_commands.guilds(discord.Object(id=server_id))
    async def find_by_discord(self, interaction:discord.Interaction, user: discord.Member):
        await interaction.response.send_message(":mag::white_check_mark: ID found!", embed=await getID("discord_id", user.id), ephemeral=True)

    @command(
            name="view_own",
            description="View your own id"
    )
    @app_commands.guilds(discord.Object(id=server_id))
    async def view_own(self, interaction:discord.Interaction):
        await interaction.response.send_message(":mag::white_check_mark: ID found!", embed=await getID("discord_id", interaction.user.id), ephemeral=True)

    @command(
            name="help",
            description="Get help with ID commands"
    )
    @app_commands.guilds(discord.Object(id=server_id))
    async def help(self, interaction:discord.Interaction):
        embed = discord.Embed(colour=0xf66151, title="Help")
        embed.set_author(name="Phoenix eID")
        embed.add_field(name="/id create",
                        value="Start the process for creating your own ID. Once filled out, wait for approval.",
                        inline=False)
        embed.add_field(name="/id view_own",
                        value="View your own ID.",
                        inline=False)
        embed.add_field(name="/id view_from_roblox_username",
                        value="(Usage of this command is restricted) View someone's id from their Roblox username.",
                        inline=False)
        embed.add_field(name="/id view_from_discord_account",
                        value="(Usage of this command is restricted) View someone's id from their Discord account.",
                        inline=False)
        embed.add_field(name="/id list",
                        value="(Usage of this command is restricted) List all registered ids.",
                        inline=False)
        embed.add_field(name="/id delete",
                        value="(Usage of this command is restricted) Delete someone's id.",
                        inline=False)
        embed.add_field(name="/id set_rank",
                        value="(Usage of this command is restricted) Set the rank for a user.",
                        inline=False)
        await interaction.response.send_message(embed=embed)

    @command(
            name="set_rank",
            description="Set a user's rank to be displayed in their ID"
    )
    @app_commands.guilds(discord.Object(id=server_id))
    async def set_rank(self, interaction: discord.Interaction, target_user: discord.Member, rank: discord.Role):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("You are lacking permissions!", ephemeral=True)
            return
        # convert rank to string 
        parsedRank = str(rank)
        try: 
            conn = sqlite3.connect('data.db')
            c = conn.cursor()
            
            # update the tables ids by setting the rank to parsedRank for target_user
            c.execute("""
            UPDATE ids
            SET rank = ?
            WHERE discord_id = ?;
            """, (parsedRank, target_user.id))

            conn.commit()
            c.close()
            conn.close()
            await interaction.response.send_message(f"Rank for {target_user} was set to {parsedRank}!")
        except Exception as e:
                embed = discord.Embed(title="Unknown error occured!", colour=0xc01c28, description=f"```{e}```")
                embed.set_footer(text=f"Phoenix v.{version}", icon_url=logo)
                await interaction.response.send_message(embed=embed)

    @command(name='list', description='List IDs')
    async def show(self, interaction: discord.Interaction):
        try:
            conn = sqlite3.connect('data.db')
            c = conn.cursor()
            c.execute("SELECT roblox_username FROM ids;")
            taglist = [row[0] for row in c.fetchall()]
            L = 10
            async def get_page(page: int):
                emb = discord.Embed(title="ID list (Roblox usernames)", description="")
                offset = (page-1) * L
                for tag in taglist[offset:offset+L]:
                    emb.description += f"`{tag}`\n"
                emb.set_author(name=f"Requested by {interaction.user}")
                n = Pagination.compute_total_pages(len(taglist), L)
                emb.set_footer(text=f"Page {page} from {n}")
                return emb, n
            await Pagination(interaction, get_page).navegate()
        except Exception as e:
            embed = discord.Embed(title="Unknown error occured!", colour=0xc01c28, description=f"```{e}```")
            embed.set_footer(text=f"Phoenix v.{version}", icon_url=logo)
            await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Identification(bot), guild=discord.Object(id=server_id))

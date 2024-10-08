# Discord imports
import discord
from discord.ext import commands
from discord import app_commands

# Other imports
import os
import dotenv
from dotenv import load_dotenv
load_dotenv()

# jikanPy import
from jikanpy import AioJikan

# open Jikan Client
jikan = AioJikan()

intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

# Load Test Server
test_guild_id = int(os.getenv('TEST_GUILD_ID'))

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

# DO NOT SYNC ON 'on_ready()', OR WILL SUFFER FROM RATELIMITING... THANKS DISCORD!
# Sync command: Clear existing commands and sync only the new ones
@bot.hybrid_command()
async def sync(ctx: commands.Context):
    await ctx.send('Clearing old commands and syncing new ones...')
    
    try:
        guild = discord.Object(id=test_guild_id)
        
        # Clear all existing commands in the test guild (this is NOT awaitable)
        bot.tree.clear_commands(guild=guild)  # No await here
        await ctx.send(f"Cleared all old commands from test guild {test_guild_id}.")
        
        # Sync the current commands to the test guild (this IS awaitable)
        await bot.tree.sync(guild=guild)
        await ctx.send(f"Commands synced to test guild with ID: {test_guild_id}")
        
    except Exception as e:
        await ctx.send(f"Failed to sync commands: {str(e)}")

        
# # Test command
# @bot.hybrid_command()
# async def ping(ctx: commands.Context):
#     await ctx.send('pong')

# Animeinfo command
@bot.hybrid_command()
@app_commands.describe(title="The title of the anime you want to search for")
async def animeinfo(ctx: commands.Context, *, title: str):
    """Searches for anime details by title using AioJikan"""
    await ctx.defer()  # Defer the response to avoid timeout while processing

    try:
        # Search for anime by title (use async call)
        search_result = await jikan.search('anime', title)

        # Debug: Print the actual response from the API
        print(f"Raw search results for '{title}':", search_result)

        # Check if the 'data' key exists and is not empty
        if 'data' in search_result and len(search_result['data']) > 0:
            anime = search_result['data'][0]  # Get the first result
            anime_title = anime.get('title', 'Unknown Title')
            synopsis = anime.get('synopsis', 'No synopsis available.')
            episodes = anime.get('episodes', 'N/A')
            score = anime.get('score', 'N/A')
            image_url = anime['images']['jpg']['image_url']  # Corrected image URL field

            # Create an embed to display anime info nicely
            embed = discord.Embed(title=anime_title, description=synopsis, color=discord.Color.blue())
            embed.add_field(name="Episodes", value=episodes, inline=True)
            embed.add_field(name="Score", value=score, inline=True)
            embed.set_thumbnail(url=image_url)

            # Send the embedded message with the anime details
            await ctx.send(embed=embed)
            print(f"Successfully sent embed for anime '{anime_title}'")
        else:
            await ctx.send(f"No anime found with the title: {title}")
            print(f"No results found for anime title: {title}")

    except Exception as e:
        # Send the error to the user and log it
        await ctx.send(f"An error occurred while fetching anime info: {str(e)}")
        print(f"Error occurred while fetching anime info: {e}")

# Runs the bot
bot.run(os.getenv('DISCORD_TOKEN'))

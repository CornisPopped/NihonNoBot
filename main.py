import logging
import discord
from discord.ext import commands
from discord import app_commands
from jikanpy import Jikan  # Import JikanPy
import os
from dotenv import load_dotenv
import asyncio

# Set up logging
logging.basicConfig(level=logging.INFO)

# Load environment variables from the .env file
load_dotenv()

# Create bot instance
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize JikanPy API client
jikan = Jikan()  # Use JikanPy

# Syncing
@bot.event
async def on_ready():
    test_guild = discord.Object(id=os.getenv('TEST_GUILD_ID'))  # specific test guild

    try:
        # Force command re-sync to update parameter types
        await bot.tree.sync(guild=test_guild)
        print(f'Successfully synced commands to test guild {test_guild.id}')

    except Exception as e:
        logging.error(f'Failed to sync commands: {e}')

    print(f'Bot is online as {bot.user}')


    
# Slash command to get popular anime
@bot.tree.command(name="popular", description="Get the top 10 most popular anime")
async def popular(interaction: discord.Interaction):
    await interaction.response.defer()  # Defer response to avoid timing out

    try:
        logging.info("Fetching top 10 most popular anime from Jikan API")
        
        # Fetching top anime using JikanPy
        top_anime = jikan.top(type='anime', page=1)  # Fetch top anime from JikanPy
        
        # Check if data is available
        if 'data' in top_anime:
            # Create a list of the top 10 popular anime
            top_list = "\n".join(
                [f"{i+1}. {anime['title']} (Score: {anime.get('score', 'N/A')})" for i, anime in enumerate(top_anime['data'][:10])]
            )
            await interaction.followup.send(f"Top 10 most popular anime:\n{top_list}")
        else:
            await interaction.followup.send("No popular anime data available.")
    
    except Exception as e:
        logging.error(f"Error in /popular command: {e}")
        await interaction.followup.send(f"Error fetching popular anime: {e}")

# Slash command to get detailed anime info by title (corrected for string input)
@bot.tree.command(name="animeinfo", description="Get detailed info about an anime")
@app_commands.describe(title="The title of the anime to search for")  # Describe the parameter
async def animeinfo(interaction: discord.Interaction, title: str):  # Use `str` type for title
    await interaction.response.defer()  # Defer response to avoid timing out

    try:
        logging.info(f"Searching for anime with title: {title}")
        
        # Search for anime by title using JikanPy
        jikan = AioJikan()
        search_result = await jikan.search('anime', title)
        await jikan.close()

        if search_result['results']:
            # Fetch the first search result's ID (MAL ID)
            anime_id = search_result['results'][0]['mal_id']
            
            # Fetch detailed anime info using the anime ID
            anime_info = await jikan.anime(anime_id)

            # Extract relevant details
            title = anime_info['title']
            synopsis = anime_info.get('synopsis', 'No synopsis available.')
            episodes = anime_info.get('episodes', 'N/A')
            duration = anime_info.get('duration', 'N/A')
            status = anime_info.get('status', 'N/A')
            genres = ", ".join([genre['name'] for genre in anime_info['genres']]) if 'genres' in anime_info else 'N/A'
            score = anime_info.get('score', 'N/A')
            rank = anime_info.get('rank', 'N/A')
            image_url = anime_info['images']['jpg']['image_url']  # Anime title card image

            # Create embed message
            embed = discord.Embed(title=title, description=synopsis, color=discord.Color.blue())
            embed.set_thumbnail(url=image_url)
            embed.add_field(name="Episodes", value=episodes, inline=True)
            embed.add_field(name="Duration", value=duration, inline=True)
            embed.add_field(name="Status", value=status, inline=True)
            embed.add_field(name="Genres", value=genres, inline=False)
            embed.add_field(name="Average Rating", value=score, inline=True)
            embed.add_field(name="Rank", value=rank, inline=True)

            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(f"No anime found with title '{title}'.")

    except Exception as e:
        logging.error(f"Error in /animeinfo command: {e}")
        await interaction.followup.send(f"Error retrieving info for anime '{title}': {e}")

# Slash command to recommend anime based on a genre
@bot.tree.command(name="recommend", description="Recommend anime based on a genre")
async def recommend(interaction: discord.Interaction, genre: str):
    await interaction.response.defer()  # Defer response

    try:
        logging.info(f"Fetching anime recommendations for genre: {genre}")
        
        # Search for anime in the genre
        search_result = jikan.search(search_type='anime', query=genre)
        
        if 'results' in search_result:
            recommendations = "\n".join(
                [f"{entry['title']} (Score: {entry['score']})" for entry in search_result['results'][:5]]
            )
            await interaction.followup.send(f"Recommended anime for the genre {genre}:\n{recommendations}")
        else:
            await interaction.followup.send(f"No recommendations found for genre: {genre}")
    
    except Exception as e:
        logging.error(f"Error in /recommend command: {e}")
        await interaction.followup.send(f"Error fetching recommendations for {genre}: {e}")


# Run the bot using the token from the .env file
bot.run(os.getenv('DISCORD_TOKEN'))

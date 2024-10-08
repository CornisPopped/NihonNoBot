import logging
import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View
from jikan4snek import Jikan4SNEK
import os
from dotenv import load_dotenv
import asyncio

# Set up logging
logging.basicConfig(level=logging.INFO)

# Load environment variables from the .env file
load_dotenv()

# Create bot instance
# Intents must comply with what I've set
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize Jikan4SNEK API client
jikan = Jikan4SNEK()

# Syncing both globally and for a specific guild (for testing purposes)
@bot.event
async def on_ready():
    test_guild = discord.Object(id=os.getenv('TEST_GUILD_ID'))  # specific test guild

    try:
        # Sync globally (for all servers)
        await bot.tree.sync()
        print('Successfully synced commands globally')

        # Sync to a specific guild for faster testing
        await bot.tree.sync(guild=test_guild)
        print(f'Successfully synced commands to test guild {test_guild.id}')

    except Exception as e:
        logging.error(f'Failed to sync commands: {e}')

    print(f'Bot is online as {bot.user}')


# Paginator class for handling embed navigation
class PaginatorView(View):
    def __init__(self, embeds, timeout=60):
        super().__init__(timeout=timeout)
        self.embeds = embeds
        self.current_page = 0
        self.total_pages = len(embeds)
        self.message = None

    async def send_initial_message(self, interaction: discord.Interaction):
        self.message = await interaction.followup.send(embed=self.embeds[self.current_page], view=self)

    @discord.ui.button(label='◀️', style=discord.ButtonStyle.primary)
    async def previous_page(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.current_page = (self.current_page - 1) % self.total_pages
        await self.message.edit(embed=self.embeds[self.current_page])

    @discord.ui.button(label='▶️', style=discord.ButtonStyle.primary)
    async def next_page(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.current_page = (self.current_page + 1) % self.total_pages
        await self.message.edit(embed=self.embeds[self.current_page])


# Slash command to display latest anime updates on MAL
@bot.tree.command(name="animelist", description="Display the latest updates on MAL")
async def animelist(interaction: discord.Interaction):
    try:
        logging.info("Fetching latest anime updates from Jikan API")
        latest_anime = await asyncio.wait_for(jikan.get("anime"), timeout=10)  # Timeout of 10 seconds
        if 'data' in latest_anime and latest_anime['data']:
            response = "\n".join([f"{entry['title']}" for entry in latest_anime['data'][:5]])
        else:
            response = "No anime updates available at the moment."
        await interaction.response.send_message(f"Latest updates on MAL:\n{response}")
    except asyncio.TimeoutError:
        logging.error("Request to Jikan API timed out")
        await interaction.response.send_message("The request to MAL timed out. Please try again later.")
    except Exception as e:
        logging.error(f"Error in /animelist command: {e}")
        await interaction.response.send_message(f"Error fetching updates: {e}")


# Slash command to get detailed anime info by title
@bot.tree.command(name="animeinfo", description="Get detailed info about an anime")
async def animeinfo(interaction: discord.Interaction, title: str):
    await interaction.response.defer()  # Defer response to avoid timing out

    try:
        logging.info(f"Fetching detailed info for anime with title: {title}")
        
        # Search for the anime using the title
        search_result = await asyncio.wait_for(jikan.search(title).anime(), timeout=20)
        
        if 'data' in search_result and search_result['data']:
            # Find the first related or original entry
            earliest_anime = None
            
            for anime in search_result['data']:
                anime_id = anime['mal_id']
                
                # Fetch full anime details to check for related prequels
                anime_info = await asyncio.wait_for(jikan.get(anime_id).anime(), timeout=20)
                related_anime = anime_info['data'].get('related', {})

                # Check if there is a prequel or original version in related data
                if 'Prequel' in related_anime:
                    prequel_id = related_anime['Prequel'][0]['mal_id']
                    earliest_anime = await asyncio.wait_for(jikan.get(prequel_id).anime(), timeout=20)
                    break  # Exit once we find the prequel (the first entry in the series)
                else:
                    # If no prequel is found, consider this the original anime
                    earliest_anime = anime_info
                    break

            if earliest_anime:
                # Extract relevant details
                title = earliest_anime['data']['title']
                synopsis = earliest_anime['data'].get('synopsis', 'No synopsis available.')
                episodes = earliest_anime['data'].get('episodes', 'N/A')
                duration = earliest_anime['data'].get('duration', 'N/A')
                status = earliest_anime['data'].get('status', 'N/A')
                genres = ", ".join([genre['name'] for genre in earliest_anime['data']['genres']]) if 'genres' in earliest_anime['data'] else 'N/A'
                score = earliest_anime['data'].get('score', 'N/A')
                rank = earliest_anime['data'].get('rank', 'N/A')
                image_url = earliest_anime['data']['images']['jpg']['image_url']  # Anime title card image

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
                await interaction.followup.send(f"No anime found with the title {title}.")

        else:
            await interaction.followup.send(f"No anime found with the title {title}.")
    
    except asyncio.TimeoutError:
        logging.error("Request to Jikan API timed out")
        await interaction.followup.send("The request to MAL timed out. Please try again later.")
    
    except Exception as e:
        logging.error(f"Error in /animeinfo command: {e}")
        await interaction.followup.send(f"Error retrieving info for {title}: {e}")


# Slash command to get popular anime
@bot.tree.command(name="popular", description="Get the top 10 most popular anime")
async def popular(interaction: discord.Interaction):
    await interaction.response.defer()  # Defer response to avoid timing out

    try:
        logging.info("Fetching top 10 most popular anime from Jikan API")
        
        # Fetching top anime using Jikan4SNEK's search method with a limit of 10
        top_anime = await asyncio.wait_for(jikan.search("anime", limit=10).anime(), timeout=10)

        if 'data' in top_anime and top_anime['data']:
            # Create a list of the top 10 popular anime
            top_list = "\n".join(
                [f"{i+1}. {anime['title']} (Score: {anime.get('score', 'N/A')})" for i, anime in enumerate(top_anime['data'][:10])]
            )
            await interaction.followup.send(f"Top 10 most popular anime:\n{top_list}")
        else:
            await interaction.followup.send("No popular anime data available.")
    
    except asyncio.TimeoutError:
        logging.error("Request to Jikan API timed out")
        await interaction.followup.send("The request to MAL timed out. Please try again later.")
    
    except Exception as e:
        logging.error(f"Error in /popular command: {e}")
        await interaction.followup.send(f"Error fetching popular anime: {e}")


# Slash command to recommend anime based on a genre
@bot.tree.command(name="recommend", description="Recommend anime based on a genre")
async def recommend(interaction: discord.Interaction, genre: str):
    try:
        logging.info(f"Fetching anime recommendations for genre: {genre}")
        genre_anime = await asyncio.wait_for(jikan.search(genre).anime(), timeout=10)
        if 'data' in genre_anime and genre_anime['data']:
            recommendations = "\n".join(
                [f"{entry['title']} (Score: {entry['score']})" for entry in genre_anime['data'][:5]]
            )
            await interaction.response.send_message(f"Recommended anime for the genre {genre}:\n{recommendations}")
        else:
            await interaction.response.send_message(f"No recommendations found for genre: {genre}")
    except asyncio.TimeoutError:
        logging.error("Request to Jikan API timed out")
        await interaction.response.send_message("The request to MAL timed out. Please try again later.")
    except Exception as e:
        logging.error(f"Error in /recommend command: {e}")
        await interaction.response.send_message(f"Error fetching recommendations for {genre}: {e}")


# Run the bot using the token from the .env file
bot.run(os.getenv('DISCORD_TOKEN'))

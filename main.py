import discord
from discord.ext import commands
from discord import app_commands
from jikan4snek import Jikan4SNEK  # Correct import for Jikan4SNEK

# Create bot instance
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize Jikan4SNEK API client
jikan = Jikan4SNEK()

# Syncing the slash commands on bot ready event
@bot.event
@bot.event
async def on_ready():
    guild = discord.Object(id= # INSERT DISCORD SERVER ID HERE)  # Replace with your actual server's ID
    try:
        await bot.tree.sync(guild=guild)  # Syncs the commands to your server
        print(f'Successfully synced commands to guild {guild.id}')
    except Exception as e:
        print(f'Failed to sync commands: {e}')
    print(f'Bot is online as {bot.user}')

# Slash command to display latest anime updates on MAL
@bot.tree.command(name="animelist", description="Display the latest updates on MAL")
async def animelist(interaction: discord.Interaction):
    try:
        latest_anime = await jikan.get("anime")
        response = "\n".join([f"{entry['title']}" for entry in latest_anime['data'][:5]])
        await interaction.response.send_message(f"Latest updates on MAL:\n{response}")
    except Exception as e:
        await interaction.response.send_message(f"Error fetching updates: {e}")

# Slash command to search for an anime by title
@bot.tree.command(name="search", description="Search for an anime by title")
async def search(interaction: discord.Interaction, query: str):
    try:
        search_result = await jikan.search(query).anime()
        if search_result['data']:
            top_result = search_result['data'][0]
            response = (
                f"**{top_result['title']}**\n"
                f"Synopsis: {top_result['synopsis']}\n"
                f"Score: {top_result['score']}\n"
                f"Episodes: {top_result.get('episodes', 'N/A')}"
            )
        else:
            response = f"No results found for {query}."
        await interaction.response.send_message(response)
    except Exception as e:
        await interaction.response.send_message(f"Error searching for {query}: {e}")

# Slash command to get detailed anime info by title
@bot.tree.command(name="animeinfo", description="Get detailed info about an anime")
async def animeinfo(interaction: discord.Interaction, title: str):
    try:
        search_result = await jikan.search(title).anime()
        if search_result['data']:
            anime_id = search_result['data'][0]['mal_id']
            anime_info = await jikan.get(anime_id).anime()
            response = (
                f"**{anime_info['data']['title']}**\n"
                f"Synopsis: {anime_info['data']['synopsis']}\n"
                f"Score: {anime_info['data']['score']}\n"
                f"Episodes: {anime_info['data']['episodes']}"
            )
        else:
            response = f"No anime found with the title {title}."
        await interaction.response.send_message(response)
    except Exception as e:
        await interaction.response.send_message(f"Error retrieving info for {title}: {e}")

# Slash command to get popular anime
@bot.tree.command(name="popular", description="Get the top 10 most popular anime")
async def popular(interaction: discord.Interaction):
    try:
        top_anime = await jikan.search("anime").anime()
        top_list = "\n".join(
            [f"{i+1}. {anime['title']} (Score: {anime['score']})" for i, anime in enumerate(top_anime['data'][:10])]
        )
        await interaction.response.send_message(f"Top 10 most popular anime:\n{top_list}")
    except Exception as e:
        await interaction.response.send_message(f"Error fetching popular anime: {e}")

# Slash command to recommend anime based on a genre
@bot.tree.command(name="recommend", description="Recommend anime based on a genre")
async def recommend(interaction: discord.Interaction, genre: str):
    try:
        genre_anime = await jikan.search(genre).anime()
        recommendations = "\n".join(
            [f"{entry['title']} (Score: {entry['score']})" for entry in genre_anime['data'][:5]]
        )
        await interaction.response.send_message(f"Recommended anime for the genre {genre}:\n{recommendations}")
    except Exception as e:
        await interaction.response.send_message(f"Error fetching recommendations for {genre}: {e}")

# Slash command to find similar anime to a title
@bot.tree.command(name="similar", description="Find similar anime to a title")
async def similar(interaction: discord.Interaction, title: str):
    try:
        search_result = await jikan.search(title).anime()
        if search_result['data']:
            anime_id = search_result['data'][0]['mal_id']
            related_anime = await jikan.get(anime_id, entry="related").anime()
            similar_anime = "\n".join(
                [rec['title'] for rec in related_anime['data'][:5]]
            )
            await interaction.response.send_message(f"Anime similar to {title}:\n{similar_anime}")
        else:
            await interaction.response.send_message(f"No similar anime found for {title}.")
    except Exception as e:
        await interaction.response.send_message(f"Error retrieving similar anime: {e}")

# Run the bot using your bot token
# bot.run('INSERT-DISCORD-TOKEN-HERE')

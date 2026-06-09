import discord
from discord import app_commands
from discord.ext import commands
import roblox

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)
roblox_client = roblox.Client()

@bot.event
async def on_ready()
    print(f'Бот {bot.user} запущен!')
    try
        synced = await bot.tree.sync()
        print(fКоманды синхронизированы)
    except Exception as e
        print(fОшибка {e})

@bot.tree.command(name=roblox_id, description=Найти игрока Roblox по ID)
async def roblox_id(interaction discord.Interaction, user_id str)
    await interaction.response.defer()
    try
        user_data = await roblox_client.get_user(int(user_id))
        embed = discord.Embed(title=fИнформация {user_data.name}, color=discord.Color.blue())
        embed.add_field(name=ID, value=user_data.id, inline=True)
        embed.add_field(name=Никнейм, value=user_data.name, inline=True)
        embed.add_field(name=Описание, value=user_data.description or Нет описания, inline=False)
        await interaction.followup.send(embed=embed)
    except
        await interaction.followup.send(Ошибка! Проверьте ID)

@bot.tree.command(name=roblox_user, description=Найти игрока Roblox по нику)
async def roblox_user(interaction discord.Interaction, username str)
    await interaction.response.defer()
    try
        user_data = await roblox_client.get_user_by_username(username)
        embed = discord.Embed(title=fИнформация {user_data.name}, color=discord.Color.green())
        embed.add_field(name=ID, value=user_data.id, inline=True)
        embed.add_field(name=Никнейм, value=user_data.name, inline=True)
        embed.add_field(name=Описание, value=user_data.description or Нет описания, inline=False)
        await interaction.followup.send(embed=embed)
    except
        await interaction.followup.send(Ошибка! Проверьте никнейм)

TOKEN = 'MTUxMzc3ODIxNzQxNTIxNzI3Mg.GAOorr.aDQ7TqUDRWmciVHuEiBVjiIO9GatQ2Xnpo9r3k'

bot.run(TOKEN)
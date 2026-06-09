import discord
from discord import app_commands
from discord.ext import commands
import roblox
import os
import asyncio
from aiohttp import web

# ========== НАСТРОЙКИ ==========
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
PORT = int(os.getenv('PORT', 10000))

# ========== DICORD БОТ ==========
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)
roblox_client = roblox.Client()

@bot.event
async def on_ready():
    print(f'✅ Бот {bot.user} запущен!')
    try:
        synced = await bot.tree.sync()
        print(f"✅ Синхронизировано {len(synced)} команд")
    except Exception as e:
        print(f"❌ Ошибка синхронизации: {e}")

# КОМАНДА 1: Поиск по ID
@bot.tree.command(name="roblox_id", description="Найти игрока Roblox по ID")
async def roblox_id(interaction: discord.Interaction, user_id: str):
    await interaction.response.defer()
    try:
        if not user_id.isdigit():
            await interaction.followup.send("❌ ID должен состоять только из цифр!")
            return
            
        user_data = await roblox_client.get_user(int(user_id))
        
        embed = discord.Embed(
            title=f"👤 {user_data.name}",
            description=f"Информация об аккаунте Roblox",
            color=discord.Color.blue()
        )
        embed.add_field(name="🆔 ID", value=f"`{user_data.id}`", inline=True)
        embed.add_field(name="📝 Никнейм", value=f"`{user_data.name}`", inline=True)
        embed.add_field(name="📜 Описание", value=user_data.description or "Нет описания", inline=False)
        embed.set_footer(text="Данные из официального API Roblox")
        
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ Ошибка! Пользователь с ID {user_id} не найден")

# КОМАНДА 2: Поиск по никнейму
@bot.tree.command(name="roblox_user", description="Найти игрока Roblox по нику")
async def roblox_user(interaction: discord.Interaction, username: str):
    await interaction.response.defer()
    try:
        user_data = await roblox_client.get_user_by_username(username)
        
        embed = discord.Embed(
            title=f"👤 {user_data.name}",
            description=f"Информация об аккаунте Roblox",
            color=discord.Color.green()
        )
        embed.add_field(name="🆔 ID", value=f"`{user_data.id}`", inline=True)
        embed.add_field(name="📝 Никнейм", value=f"`{user_data.name}`", inline=True)
        embed.add_field(name="📜 Описание", value=user_data.description or "Нет описания", inline=False)
        embed.set_footer(text="Данные из официального API Roblox")
        
        await interaction.followup.send(embed=embed)
    except:
        await interaction.followup.send(f"❌ Ошибка! Пользователь с ником '{username}' не найден")

# ========== ВЕБ-СЕРВЕР ДЛЯ RENDER ==========
async def health_check(request):
    return web.Response(text="Bot is running!", status=200)

async def run_web_server():
    app = web.Application()
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    print(f"✅ Веб-сервер запущен на порту {PORT}")

# ========== ЗАПУСК ==========
async def main():
    # Запускаем веб-сервер в фоне
    asyncio.create_task(run_web_server())
    
    # Запускаем Discord бота
    if not TOKEN:
        print("❌ ОШИБКА: Токен не найден!")
        return
    
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())

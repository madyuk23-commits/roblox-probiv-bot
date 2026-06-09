import discord
from discord import app_commands
from discord.ext import commands
import roblox
import os
import asyncio
from aiohttp import web
from datetime import datetime

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

# Функция для получения URL аватара
def get_avatar_url(user_id, size=420):
    """Возвращает прямую ссылку на аватар пользователя Roblox"""
    return f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size={size}x{size}&format=Png"

# Функция для получения текущей игры пользователя
async def get_current_game(user_id):
    """Пытается получить информацию об игре, в которую сейчас играет пользователь"""
    try:
        # Получаем информацию о присутствии пользователя
        presence_response = await roblox_client.presence.get_user_presence(user_id)
        
        if presence_response and presence_response.user_presence_type == 2:  # 2 = InGame
            # Проверяем, есть ли данные об игре и видна ли она
            if presence_response.place_id and presence_response.game_id:
                try:
                    # Пытаемся получить информацию об игре по universeId
                    universe_id = presence_response.universe_id
                    if universe_id:
                        game_info = await roblox_client.universes.get_universe(universe_id)
                        if game_info and hasattr(game_info, 'name'):
                            return {
                                "name": game_info.name,
                                "place_id": presence_response.place_id,
                                "is_visible": True
                            }
                except Exception:
                    pass
                
                # Если не удалось получить название, возвращаем базовую информацию
                return {
                    "name": "Игра на Roblox",
                    "place_id": presence_response.place_id,
                    "is_visible": True
                }
            else:
                # Пользователь в игре, но данные скрыты по приватности
                return {
                    "name": "Скрыто (настройки приватности)",
                    "is_visible": False
                }
        return None
    except Exception as e:
        print(f"Ошибка получения информации об игре: {e}")
        return None

# Функция для форматирования даты
def format_date(date_obj):
    """Форматирует дату создания аккаунта в читаемый вид"""
    if date_obj:
        return date_obj.strftime("%d.%m.%Y в %H:%M")
    return "Неизвестно"

# КОМАНДА 1: Поиск по ID
@bot.tree.command(name="roblox_id", description="Найти игрока Roblox по ID")
async def roblox_id(interaction: discord.Interaction, user_id: str):
    await interaction.response.defer()
    try:
        if not user_id.isdigit():
            await interaction.followup.send("❌ ID должен состоять только из цифр!")
            return
            
        user_data = await roblox_client.get_user(int(user_id))
        
        # Получаем дополнительную информацию
        avatar_url = get_avatar_url(user_data.id)
        created_date = format_date(user_data.created) if hasattr(user_data, 'created') else "Неизвестно"
        current_game = await get_current_game(user_data.id)
        
        # Создаем Embed
        embed = discord.Embed(
            title=f"👤 {user_data.name}",
            description=f"Информация об аккаунте Roblox",
            color=discord.Color.blue(),
            url=f"https://www.roblox.com/users/{user_data.id}/profile"
        )
        
        # Добавляем аватар
        embed.set_thumbnail(url=avatar_url)
        
        # Основная информация
        embed.add_field(name="🆔 ID", value=f"`{user_data.id}`", inline=True)
        embed.add_field(name="📝 Никнейм", value=f"`{user_data.name}`", inline=True)
        
        # Отображаемое имя (если есть)
        if hasattr(user_data, 'display_name') and user_data.display_name:
            embed.add_field(name="✨ Отображаемое имя", value=f"`{user_data.display_name}`", inline=True)
        
        # Дата создания
        embed.add_field(name="📅 Дата создания", value=created_date, inline=False)
        
        # Описание
        description_text = user_data.description or "Нет описания 😢"
        if len(description_text) > 1024:
            description_text = description_text[:1021] + "..."
        embed.add_field(name="📜 Описание", value=description_text, inline=False)
        
        # Информация об игре
        if current_game:
            if current_game.get("is_visible", True):
                game_text = f"🎮 **{current_game['name']}**"
                if current_game.get("place_id"):
                    game_text += f"\n🏠 ID места: `{current_game['place_id']}`"
                embed.add_field(name="🕹️ Сейчас играет", value=game_text, inline=False)
            else:
                embed.add_field(name="🕹️ Сейчас играет", value="*Играет, но информация скрыта настройками приватности*", inline=False)
        else:
            embed.add_field(name="🕹️ Сейчас играет", value="*Не в игре или информация недоступна*", inline=False)
        
        embed.set_footer(text="Данные из официального API Roblox")
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        print(f"Ошибка при поиске по ID: {e}")
        await interaction.followup.send(f"❌ Ошибка! Пользователь с ID {user_id} не найден")

# КОМАНДА 2: Поиск по никнейму
@bot.tree.command(name="roblox_user", description="Найти игрока Roblox по нику")
async def roblox_user(interaction: discord.Interaction, username: str):
    await interaction.response.defer()
    try:
        user_data = await roblox_client.get_user_by_username(username)
        
        if not user_data:
            await interaction.followup.send(f"❌ Пользователь с ником '{username}' не найден")
            return
        
        # Получаем дополнительную информацию
        avatar_url = get_avatar_url(user_data.id)
        created_date = format_date(user_data.created) if hasattr(user_data, 'created') else "Неизвестно"
        current_game = await get_current_game(user_data.id)
        
        # Создаем Embed
        embed = discord.Embed(
            title=f"👤 {user_data.name}",
            description=f"Информация об аккаунте Roblox",
            color=discord.Color.green(),
            url=f"https://www.roblox.com/users/{user_data.id}/profile"
        )
        
        # Добавляем аватар
        embed.set_thumbnail(url=avatar_url)
        
        # Основная информация
        embed.add_field(name="🆔 ID", value=f"`{user_data.id}`", inline=True)
        embed.add_field(name="📝 Никнейм", value=f"`{user_data.name}`", inline=True)
        
        # Отображаемое имя (если есть)
        if hasattr(user_data, 'display_name') and user_data.display_name:
            embed.add_field(name="✨ Отображаемое имя", value=f"`{user_data.display_name}`", inline=True)
        
        # Дата создания
        embed.add_field(name="📅 Дата создания", value=created_date, inline=False)
        
        # Описание
        description_text = user_data.description or "Нет описания 😢"
        if len(description_text) > 1024:
            description_text = description_text[:1021] + "..."
        embed.add_field(name="📜 Описание", value=description_text, inline=False)
        
        # Информация об игре
        if current_game:
            if current_game.get("is_visible", True):
                game_text = f"🎮 **{current_game['name']}**"
                if current_game.get("place_id"):
                    game_text += f"\n🏠 ID места: `{current_game['place_id']}`"
                embed.add_field(name="🕹️ Сейчас играет", value=game_text, inline=False)
            else:
                embed.add_field(name="🕹️ Сейчас играет", value="*Играет, но информация скрыта настройками приватности*", inline=False)
        else:
            embed.add_field(name="🕹️ Сейчас играет", value="*Не в игре или информация недоступна*", inline=False)
        
        embed.set_footer(text="Данные из официального API Roblox")
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        print(f"Ошибка при поиске по никнейму: {e}")
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

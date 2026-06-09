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

# Функция для получения URL аватара (только голова)
def get_avatar_head_url(user_id, size=420):
    """Возвращает прямую ссылку на аватар (голову) пользователя Roblox"""
    return f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size={size}x{size}&format=Png"

# Функция для получения URL полнотельного персонажа
def get_avatar_full_url(user_id, size=420):
    """Возвращает прямую ссылку на полнотельное изображение персонажа Roblox"""
    return f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size={size}x{size}&format=Png&isCircular=false"

# Функция для получения текущей игры пользователя
async def get_current_game(user_id):
    """Пытается получить информацию об игре, в которую сейчас играет пользователь"""
    try:
        # Получаем информацию о присутствии пользователя через низкоуровневый запрос
        async with roblox_client.requests.get(f"https://presence.roblox.com/v1/presence/users", json={"userIds": [user_id]}) as response:
            if response.status == 200:
                data = await response.json()
                if data and data.get("userPresences") and len(data["userPresences"]) > 0:
                    presence = data["userPresences"][0]
                    if presence.get("userPresenceType") == 2:  # 2 = InGame
                        game_id = presence.get("gameId")
                        place_id = presence.get("placeId")
                        
                        if game_id and game_id != "0":
                            try:
                                # Пытаемся получить информацию об игре
                                universe_response = await roblox_client.requests.get(f"https://games.roblox.com/v1/games?universeIds={game_id}")
                                if universe_response.status == 200:
                                    game_data = await universe_response.json()
                                    if game_data.get("data") and len(game_data["data"]) > 0:
                                        game_name = game_data["data"][0].get("name", "Неизвестная игра")
                                        return {
                                            "name": game_name,
                                            "place_id": place_id,
                                            "game_id": game_id,
                                            "is_visible": True
                                        }
                            except Exception:
                                pass
                            
                            return {
                                "name": "Игра на Roblox",
                                "place_id": place_id,
                                "game_id": game_id,
                                "is_visible": True
                            }
                        else:
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

# Функция для создания embed сообщения
async def create_user_embed(user_data, search_query, search_type):
    """Создает embed с полной информацией о пользователе"""
    
    # Получаем дополнительную информацию
    avatar_head_url = get_avatar_head_url(user_data.id)
    avatar_full_url = get_avatar_full_url(user_data.id)
    created_date = format_date(user_data.created) if hasattr(user_data, 'created') else "Неизвестно"
    current_game = await get_current_game(user_data.id)
    
    # Выбираем цвет в зависимости от типа поиска
    color = discord.Color.blue() if search_type == "ID" else discord.Color.green()
    
    # Создаем Embed
    embed = discord.Embed(
        title=f"👤 {user_data.name}",
        description=f"*Найдено по: {search_query} ({search_type})*",
        color=color,
        url=f"https://www.roblox.com/users/{user_data.id}/profile"
    )
    
    # Добавляем полнотельное фото персонажа (как основное изображение)
    embed.set_image(url=avatar_full_url)
    
    # Добавляем аватар-голову (как миниатюру справа)
    embed.set_thumbnail(url=avatar_head_url)
    
    # Основная информация
    embed.add_field(name="🆔 ID", value=f"`{user_data.id}`", inline=True)
    embed.add_field(name="📝 Никнейм", value=f"`{user_data.name}`", inline=True)
    
    # Отображаемое имя (если есть)
    if hasattr(user_data, 'display_name') and user_data.display_name and user_data.display_name != user_data.name:
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
            embed.add_field(name="🕹️ Сейчас играет", value="*🔒 Играет, но информация скрыта настройками приватности*", inline=False)
    else:
        embed.add_field(name="🕹️ Сейчас играет", value="*💤 Не в игре или информация недоступна*", inline=False)
    
    embed.set_footer(text="Данные из официального API Roblox")
    
    return embed

# КОМАНДА 1: Поиск по ID
@bot.tree.command(name="roblox_id", description="Найти игрока Roblox по ID")
async def roblox_id(interaction: discord.Interaction, user_id: str):
    # Отвечаем только тому, кто вызвал команду (ephemeral=True)
    await interaction.response.defer(ephemeral=True)
    try:
        if not user_id.isdigit():
            await interaction.followup.send("❌ ID должен состоять только из цифр!", ephemeral=True)
            return
            
        user_data = await roblox_client.get_user(int(user_id))
        
        embed = await create_user_embed(user_data, user_id, "ID")
        
        # ephemeral=True означает, что сообщение увидит только тот, кто вызвал команду
        await interaction.followup.send(embed=embed, ephemeral=True)
        
    except Exception as e:
        print(f"Ошибка при поиске по ID: {e}")
        await interaction.followup.send(f"❌ Ошибка! Пользователь с ID {user_id} не найден", ephemeral=True)

# КОМАНДА 2: Поиск по никнейму
@bot.tree.command(name="roblox_user", description="Найти игрока Roblox по нику")
async def roblox_user(interaction: discord.Interaction, username: str):
    # Отвечаем только тому, кто вызвал команду (ephemeral=True)
    await interaction.response.defer(ephemeral=True)
    try:
        user_data = await roblox_client.get_user_by_username(username)
        
        if not user_data:
            await interaction.followup.send(f"❌ Пользователь с ником '{username}' не найден", ephemeral=True)
            return
        
        embed = await create_user_embed(user_data, username, "Никнейму")
        
        # ephemeral=True означает, что сообщение увидит только тот, кто вызвал команду
        await interaction.followup.send(embed=embed, ephemeral=True)
        
    except Exception as e:
        print(f"Ошибка при поиске по никнейму: {e}")
        await interaction.followup.send(f"❌ Ошибка! Пользователь с ником '{username}' не найден", ephemeral=True)

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

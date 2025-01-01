import re
import sqlite3
import discord
from discord.ext import commands
from discord import Attachment, Interaction, app_commands
import random
import os
from dotenv import load_dotenv
import requests

# Cargar variables de entorno desde un archivo .env
load_dotenv()

# Obtener el token del bot desde la variable de entorno
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

if DISCORD_TOKEN is None:
    raise ValueError("Discord token not found in environment variables.")

# Crear una instancia del bot con intents necesarios
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    await bot.tree.sync()  # Sincronizar comandos de barra (slash commands)

# Suponiendo que 'bot' es una instancia de 'commands.Bot'
@bot.tree.command(name='sendfile', description='Send a file to a specified channel with an optional message.')
@app_commands.describe(channel='The channel to send the file to', file='The file to send', message='The optional message to send')
async def sendfile(interaction: discord.Interaction, channel: discord.TextChannel, file: discord.Attachment = None, message: str = None):
    # Defer the response to indicate that the command is being processed
    await interaction.response.defer(ephemeral=True)
    
    try:
        if file:
            # Create a file object from the attachment
            file_bytes = await file.read()
            file_name = file.filename
            
            # Prepare the file to be sent
            file_to_send = discord.File(fp=io.BytesIO(file_bytes), filename=file_name)
            
            # Send the file to the specified channel with the optional message
            await channel.send(content=message, file=file_to_send)
        else:
            # Send the optional message to the specified channel without a file
            await channel.send(content=message)
        
        # Follow up with a success message
        await interaction.followup.send(content=f'{"File and " if file else ""}Message sent to {channel.mention}.', ephemeral=True)
    except Exception as e:
        # Follow up with an error message
        await interaction.followup.send(content=f'Failed to send: {e}', ephemeral=True)



import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageOps, ImageFont
import io
import random
import requests

# Función para determinar el color del embed basado en el porcentaje de compatibilidad
def get_embed_color(percentage):
    if percentage <= 0:
        return discord.Color.red()
    elif percentage >= 100:
        return discord.Color.green()
    else:
        # Interpolación del color entre amarillo y rojo
        r = int(255 - (percentage / 100 * 255))
        g = int(255 * (percentage / 100))
        b = 0
        return discord.Color.from_rgb(r, g, b)

@bot.tree.command(name='ship', description='Match two users and show their compatibility.')
async def ship(interaction: discord.Interaction, user1: discord.Member, user2: discord.Member):
    if user1 == user2:
        await interaction.response.send_message("¡No puedes emparejar a la misma persona contigo mismo!", ephemeral=True)
        return

    ship_name = f"{user1.display_name[:3]}-{user2.display_name[:3]}"
    compatibility_percentage = random.randint(0, 100)

    # Lista de imágenes de fondo
    background_images = [
        "desktop-wallpaper-anime-kiss-blue-kiss-anime.jpg",
        "OIP.jpg",
        "OIP1.jpg",
        "OIP2.png",
        "OIP3.jpg"
    ]

    # Selecciona una imagen de fondo aleatoria
    background_image = random.choice(background_images)
    background = Image.open(background_image).convert("RGBA")

    # Calcula tamaños basados en el tamaño de la imagen de fondo
    base_width, base_height = background.size
    avatar_size = int(min(base_width, base_height) * 0.2)  # Tamaño de los avatares como el 20% del menor tamaño de la imagen
    font_size = int(min(base_width, base_height) * 0.1)  # Tamaño de la fuente como el 10% del menor tamaño de la imagen

    base = Image.new('RGBA', background.size)
    base.paste(background, (0, 0))

    draw = ImageDraw.Draw(base)

    def download_avatar(url):
        response = requests.get(url)
        avatar = Image.open(io.BytesIO(response.content)).convert("RGBA")
        return avatar

    avatar1 = download_avatar(user1.avatar.url)
    avatar2 = download_avatar(user2.avatar.url)

    avatar1 = avatar1.resize((avatar_size, avatar_size))
    avatar2 = avatar2.resize((avatar_size, avatar_size))

    mask = Image.new('L', (avatar_size, avatar_size), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.ellipse((0, 0, avatar_size, avatar_size), fill=255)

    avatar1 = ImageOps.fit(avatar1, (avatar_size, avatar_size), centering=(0.5, 0.5))
    avatar1.putalpha(mask)
    avatar2 = ImageOps.fit(avatar2, (avatar_size, avatar_size), centering=(0.5, 0.5))
    avatar2.putalpha(mask)

    avatar1_x = (base_width - avatar_size) / 2 - avatar_size - 40
    avatar2_x = (base_width - avatar_size) / 2 + avatar_size + 40
    avatar_y = (base_height - avatar_size) / 2

    base.paste(avatar1, (int(avatar1_x), int(avatar_y)), avatar1)
    base.paste(avatar2, (int(avatar2_x), int(avatar_y)), avatar2)

    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()

    text = f"{compatibility_percentage}%"
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    text_x = (base_width - text_width) / 2
    text_y = (base_height - text_height) / 2

    # Establece el color del texto como blanco para mejor visibilidad en la mayoría de los fondos
    draw.text((text_x, text_y), text, font=font, fill="red")

    with io.BytesIO() as buf:
        base.save(buf, format='PNG')
        buf.seek(0)
        image_file = discord.File(fp=buf, filename='ship_compatibility.png')

    # Obtener el color del embed basado en el porcentaje de compatibilidad
    embed_color = get_embed_color(compatibility_percentage)

    embed = discord.Embed(
        title="**Compatibilidad de Emparejamiento**",
        color=embed_color
    )
    embed.add_field(name="Usuario 1", value=user1.display_name, inline=True)
    embed.add_field(name="Usuario 2", value=user2.display_name, inline=True)
    embed.add_field(name="Nombre del Emparejamiento", value=f"**{ship_name}**", inline=True)
    embed.add_field(name="Compatibilidad", value=f"**{compatibility_percentage}%**", inline=True)
    embed.set_image(url="attachment://ship_compatibility.png")

    try:
        await interaction.response.send_message(embed=embed, file=image_file)
    except discord.errors.NotFound:
        await interaction.followup.send(embed=embed, file=image_file)




# Comando de barra para hacer anuncios
@bot.tree.command(name='announce', description='Send an announcement to a specified channel.')
@app_commands.describe(channel='The channel to send the announcement to', message='The announcement message')
async def announce(interaction: discord.Interaction, channel: discord.TextChannel, *, message: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    embed = discord.Embed(
        title="📢 Announcement",
        description=message,
        color=discord.Color.blue()
    )

    try:
        await channel.send(embed=embed)
        await interaction.response.send_message(f'Announcement sent to {channel.mention}.', ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f'Failed to send announcement: {e}', ephemeral=True)

# Comando de barra para asignar o quitar roles
@bot.tree.command(name='getrole', description='Assign or remove a role from a user')
@app_commands.describe(user='The user to assign or remove the role from', role='The role to assign or remove', action='The action (add/remove)')
async def getrole(interaction: discord.Interaction, user: discord.User, role: discord.Role, action: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    guild = interaction.guild
    if not guild:
        await interaction.response.send_message("This command can only be used in a server.")
        return

    member = guild.get_member(user.id)
    if not member:
        await interaction.response.send_message(f"Could not find user {user.mention}.")
        return

    embed = discord.Embed(title="Role Management", color=discord.Color.blue())
    
    if action == 'add':
        if role in member.roles:
            embed.description = f"{user.mention} already has the role {role.name}."
            embed.set_footer(text="Action: Add role")
        else:
            await member.add_roles(role)
            embed.description = f"Role {role.name} added to {user.mention}."
            embed.set_footer(text="Action: Add role")
    elif action == 'remove':
        if role not in member.roles:
            embed.description = f"{user.mention} does not have the role {role.name}."
            embed.set_footer(text="Action: Remove role")
        else:
            await member.remove_roles(role)
            embed.description = f"Role {role.name} removed from {user.mention}."
            embed.set_footer(text="Action: Remove role")
    else:
        embed.description = "Invalid action. Use 'add' to add or 'remove' to remove the role."
        embed.set_footer(text="Action: Error")
    
    await interaction.response.send_message(embed=embed)

# Comando de barra para crear canales
@bot.tree.command(name='create_channel', description='Create a new channel in the server.')
@app_commands.describe(channel_name='Name of the new channel', channel_type='Type of the channel (text/voice)')
async def create_channel(interaction: discord.Interaction, channel_name: str, channel_type: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    guild = interaction.guild

    if channel_type == 'text':
        new_channel = await guild.create_text_channel(channel_name)
    elif channel_type == 'voice':
        new_channel = await guild.create_voice_channel(channel_name)
    else:
        await interaction.response.send_message("Invalid channel type. Please use 'text' or 'voice'.", ephemeral=True)
        return

    embed = discord.Embed(
        title="New Channel Created",
        description=f"The channel {new_channel.mention} has been created.",
        color=discord.Color.green()
    )
    embed.add_field(name="Channel Name", value=channel_name, inline=True)
    embed.add_field(name="Channel Type", value=channel_type, inline=True)

    await interaction.response.send_message(embed=embed)

# Comando de barra para eliminar canales
@bot.tree.command(name='delete_channel', description='Delete a channel from the server')
@app_commands.describe(channel_name='Name of the channel to delete')
async def delete_channel(interaction: discord.Interaction, channel_name: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    guild = interaction.guild
    channel = discord.utils.get(guild.channels, name=channel_name)
    if channel:
        await channel.delete()

        embed = discord.Embed(title="Channel Deleted", description=f"The channel {channel_name} has been deleted.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed)

        announcement_channel = discord.utils.get(guild.text_channels, name="announcements")
        if announcement_channel:
            await announcement_channel.send(embed=embed)
    else:
        await interaction.response.send_message(f"Channel with name {channel_name} not found.", ephemeral=True)

# Lista de respuestas para el comando 8ball
responses = [
    "Sí", "No", "Puede ser", "No estoy seguro", "Probablemente sí", "Probablemente no",
    "Definitivamente sí", "Definitivamente no", "Quizás", "Pregunta de nuevo más tarde"
]

@bot.tree.command(name='8ball', description='Haz una pregunta y recibirás una respuesta.')
@app_commands.describe(question='La pregunta que quieres hacer.')
async def eight_ball(interaction: discord.Interaction, question: str):
    if not question:
        await interaction.response.send_message("Por favor, proporciona una pregunta.", ephemeral=True)
        return

    response = random.choice(responses)
    embed = discord.Embed(
        title="🎱 8-Ball",
        description=f"Pregunta: {question}\nRespuesta: {response}",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='serverinfo', description='Show server information.')
async def serverinfo(interaction: discord.Interaction):
    guild = interaction.guild

    # Información general
    server_name = guild.name
    server_id = guild.id
    owner = guild.owner
    member_count = guild.member_count
    role_count = len(guild.roles)
    text_channels = len(guild.text_channels)
    voice_channels = len(guild.voice_channels)
    creation_date = guild.created_at.strftime("%Y-%m-%d %H:%M:%S")

    # Crear el embed
    embed = discord.Embed(
        title="Server Information",
        color=discord.Color.random()
    )

    # Verificar si el servidor tiene un ícono
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    
    embed.add_field(name="Server Name", value=server_name, inline=True)
    embed.add_field(name="Server ID", value=server_id, inline=True)
    embed.add_field(name="Owner", value=owner.mention, inline=True)
    embed.add_field(name="Members", value=member_count, inline=True)
    embed.add_field(name="Roles", value=role_count, inline=True)
    embed.add_field(name="Text Channels", value=text_channels, inline=True)
    embed.add_field(name="Voice Channels", value=voice_channels, inline=True)
    embed.add_field(name="Creation Date", value=creation_date, inline=True)

    # Roles
    roles = [role.name for role in guild.roles if role.name != "@everyone"]
    max_roles_per_message = 25  # Cantidad máxima recomendada de roles por mensaje
    for i in range(0, len(roles), max_roles_per_message):
        roles_chunk = "\n".join(roles[i:i+max_roles_per_message])
        embed.add_field(name=f"Roles ({i + 1}-{min(i + max_roles_per_message, len(roles))})", value=roles_chunk, inline=False)

    await interaction.response.send_message(embed=embed)

# Comando de barra para mostrar el equipo de administración
@bot.tree.command(name='adminteam', description='Show admin team information.')
async def adminteam(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    guild = interaction.guild
    admin_roles = ["Admin", "Administrator", "Mod", "Moderator"]

    admins = []
    for member in guild.members:
        for role in member.roles:
            if role.name in admin_roles:
                admins.append(member)
                break

    embed = discord.Embed(
        title="Admin Team",
        description="List of Admins and Moderators in the server.",
        color=discord.Color.gold()
    )

    for admin in admins:
        embed.add_field(name=admin.display_name, value=admin.mention, inline=True)

    await interaction.response.send_message(embed=embed)

# Comando de barra para mostrar los miembros en línea
@bot.tree.command(name='online_members', description='Show currently online members.')
async def online_members(interaction: discord.Interaction):
    guild = interaction.guild
    online_members = [member for member in guild.members if member.status == discord.Status.online]

    embed = discord.Embed(
        title="Online Members",
        description=f"There are {len(online_members)} members online.",
        color=discord.Color.green()
    )

    for member in online_members:
        embed.add_field(name=member.display_name, value=member.mention, inline=True)

    await interaction.response.send_message(embed=embed)

# Comando de barra para sugerencias
@bot.tree.command(name='suggest', description='Make a suggestion.')
@app_commands.describe(suggestion='Your suggestion')
async def suggest(interaction: discord.Interaction, suggestion: str):
    guild = interaction.guild
    suggestion_channel = discord.utils.get(guild.text_channels, name='suggestions')

    if not suggestion_channel:
        await interaction.response.send_message("Suggestion channel not found.", ephemeral=True)
        return

    embed = discord.Embed(
        title="New Suggestion",
        description=suggestion,
        color=discord.Color.blue()
    )
    embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.avatar.url)

    suggestion_message = await suggestion_channel.send(embed=embed)
    await suggestion_message.add_reaction('👍')
    await suggestion_message.add_reaction('👎')

    await interaction.response.send_message("Suggestion submitted!", ephemeral=True)



import discord
from discord import app_commands
import asyncio

# Función para crear un embed de respuesta
def create_embed(title: str, description: str, color: discord.Color) -> discord.Embed:
    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )
    return embed

# Comando para expulsar a un miembro
@bot.tree.command(name='kick', description='Kick a member from the server.')
@app_commands.describe(user='The member to kick', reason='The reason for kicking')
async def kick(interaction: discord.Interaction, user: discord.Member, reason: str):
    if not interaction.user.guild_permissions.administrator:
        embed = create_embed(
            title="Error",
            description="You do not have permission to use this command.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if not interaction.guild.me.guild_permissions.kick_members:
        embed = create_embed(
            title="Error",
            description="I do not have permission to kick members.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    try:
        await user.kick(reason=reason)
        embed = create_embed(
            title="Success",
            description=f"{user.mention} has been kicked. Reason: {reason}",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except discord.Forbidden:
        embed = create_embed(
            title="Error",
            description="I do not have permission to kick this member.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        embed = create_embed(
            title="Error",
            description=f"An error occurred: {e}",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

# Comando para banear a un miembro
@bot.tree.command(name='ban', description='Ban a member from the server.')
@app_commands.describe(user='The member to ban', reason='The reason for banning')
async def ban(interaction: discord.Interaction, user: discord.Member, reason: str):
    if not interaction.user.guild_permissions.administrator:
        embed = create_embed(
            title="Error",
            description="You do not have permission to use this command.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if not interaction.guild.me.guild_permissions.ban_members:
        embed = create_embed(
            title="Error",
            description="I do not have permission to ban members.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    try:
        await user.ban(reason=reason)
        embed = create_embed(
            title="Success",
            description=f"{user.mention} has been banned. Reason: {reason}",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except discord.Forbidden:
        embed = create_embed(
            title="Error",
            description="I do not have permission to ban this member.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        embed = create_embed(
            title="Error",
            description=f"An error occurred: {e}",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


import discord
from discord import app_commands
import asyncio

@bot.tree.command(name='poll', description='Crea una encuesta para todo el servidor.')
@app_commands.describe(
    title='Título de la encuesta',
    question='La pregunta de la encuesta',
    options='Opciones para la encuesta (separadas por comas, usa | para más opciones)',
    duration='Duración de la encuesta en minutos'
)
async def poll(interaction: discord.Interaction, title: str, question: str, options: str, duration: int):
    # Verificar si el usuario tiene permisos de administrador
    if not any(role.permissions.administrator for role in interaction.user.roles):
        await interaction.response.send_message("No tienes permiso para usar este comando.", ephemeral=True)
        return

    # Indicar que la respuesta está en proceso
    await interaction.response.send_message("Estamos creando la encuesta, por favor espera...", ephemeral=True)

    # Separar opciones usando | como delimitador
    options_list = [opt.strip() for opt in options.split('|')]
    if len(options_list) < 2:
        await interaction.followup.send("Debes proporcionar al menos dos opciones.", ephemeral=True)
        return

    # Crear el embed para la encuesta
    embed = discord.Embed(
        title=title,
        description=question,
        color=discord.Color.blue()
    )
    embed.add_field(name="Opciones", value="\n".join(f"{i + 1}. {option}" for i, option in enumerate(options_list)), inline=False)
    
    # Enviar el mensaje de la encuesta
    message = await interaction.channel.send(embed=embed)

    # Agregar reacciones para cada opción
    emojis = [str(i + 1) + '️⃣' for i in range(len(options_list))]
    for emoji in emojis:
        await message.add_reaction(emoji)

    # Esperar a que la encuesta expire
    await asyncio.sleep(duration * 60)
    
    # Obtener el mensaje para actualizarlo con los resultados
    message = await interaction.channel.fetch_message(message.id)
    
    reactions = {emoji: reaction.count - 1 for emoji, reaction in zip(emojis, message.reactions)}
    results = '\n'.join([f'{option}: {reactions[emoji]} votos' for option, emoji in zip(options_list, emojis)])
    
    result_embed = discord.Embed(
        title=f'Resultados de la encuesta: {title}',
        description=f'{question}\n\n{results}',
        color=discord.Color.green()
    )
    await message.edit(embed=result_embed)

    # Confirmar que la encuesta se ha creado con éxito
    await interaction.followup.send("¡Encuesta creada con éxito!", ephemeral=True)

import aiohttp
from PIL import Image, ImageDraw, ImageFont, ImageOps
import io
import discord
from discord import app_commands
import random
from datetime import datetime

@bot.tree.command(name='funtweet', description='Generate a fun tweet with your text')
@app_commands.describe(tweet_text='The text of the tweet')
async def funtweet(interaction: discord.Interaction, tweet_text: str):
    user = interaction.user

    try:
        # Crear una imagen inicial con fondo blanco
        base_width, base_height = 800, 250
        base = Image.new('RGB', (base_width, base_height), 'white')  # Fondo blanco

        # Crear un dibujo en la imagen
        draw = ImageDraw.Draw(base)

        # Cargar la fuente
        try:
            font = ImageFont.truetype("arial.ttf", 20)
            font_large = ImageFont.truetype("arial.ttf", 24)  # Fuente para el nombre grande
            font_small = ImageFont.truetype("arial.ttf", 14)
        except IOError:
            font = ImageFont.load_default()
            font_large = font
            font_small = font

        # Obtener la imagen de perfil del usuario
        avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
        async with aiohttp.ClientSession() as session:
            async with session.get(avatar_url) as response:
                avatar_data = io.BytesIO(await response.read())

        avatar = Image.open(avatar_data).convert("RGBA").resize((60, 60))
        mask = Image.new("L", avatar.size, 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0) + avatar.size, fill=255)
        avatar = ImageOps.fit(avatar, mask.size, centering=(0.5, 0.5))
        avatar.putalpha(mask)

        base.paste(avatar, (20, 20), avatar)

        # Dibuja el nombre del servidor (display name) en tamaño grande
        display_name = user.display_name
        handle_text = f"@{user.name}"

        # Calcular el espacio necesario para el texto del tweet
        tweet_text = tweet_text[:200]  # Limita el texto a 200 caracteres
        lines = []
        max_width = base_width - 100  # Espacio disponible para el texto
        while tweet_text:
            line = ""
            while tweet_text and draw.textbbox((0, 0), line + tweet_text[0], font=font)[2] <= max_width:
                line += tweet_text[0]
                tweet_text = tweet_text[1:]
            lines.append(line)
            if not tweet_text:
                break

        # Ajustar la altura de la imagen si es necesario
        text_height = sum(draw.textbbox((0, 0), line, font=font)[3] - draw.textbbox((0, 0), line, font=font)[1] for line in lines) + 80  # 80 para espacio adicional
        new_height = max(text_height, 250)
        if new_height != base_height:
            base = base.resize((base_width, new_height))
            draw = ImageDraw.Draw(base)

        # Dibuja el nombre del servidor (display name) en tamaño grande
        draw.text((100, 20), display_name, font=font_large, fill=(0, 0, 0))

        # Dibuja el handle del usuario (nombre de usuario con @) en tamaño pequeño
        draw.text((100, 60), handle_text, font=font_small, fill=(100, 100, 100))

        # Dibuja el texto del tweet en múltiples líneas
        y_text = 80
        for line in lines:
            draw.text((100, y_text), line, font=font, fill=(0, 0, 0))
            y_text += draw.textbbox((0, 0), line, font=font)[3] - draw.textbbox((0, 0), line, font=font)[1]

        # Dibuja la hora del tweet y el número de vistas
        tweet_time = datetime.now().strftime('%I:%M %p · %b %d, %Y')
        view_count = random.randint(1, 1000000)  # Número de vistas aleatorio
        draw.text((100, y_text + 10), f"{view_count} views · {tweet_time}", font=font_small, fill=(100, 100, 100))

        # Dibuja los botones de interacción
        button_y_start = y_text + 40
        buttons = ['Reply', 'Retweet', 'Like', 'Share', 'Bookmark']
        button_width = 100
        button_height = 20
        spacing = 15

        # Calcular el ancho total del área de los botones
        button_area_width = len(buttons) * (button_width + spacing) - spacing
        button_area_x_start = 100
        button_area_x_end = button_area_x_start + button_area_width

        # Dibuja los botones y la línea encima y debajo
        for i, button in enumerate(buttons):
            x = button_area_x_start + i * (button_width + spacing)
            y = button_y_start
            # Dibuja el botón
            draw.rectangle([x, y, x + button_width, y + button_height], outline=(200, 200, 200), width=1)
            draw.text((x + 5, y + 2), button, font=font_small, fill=(100, 100, 100))

        # Añadir números aleatorios para botones
        like_count = random.randint(1, 1000000)
        retweet_count = random.randint(1, 1000000)
        draw.text((button_area_x_start, button_y_start + button_height + 10), f"❤️ {like_count}   🔁 {retweet_count}", font=font_small, fill=(100, 100, 100))

        # Añadir líneas horizontales arriba y abajo de los botones
        line_y_top = button_y_start - 10
        line_y_bottom = button_y_start + button_height + 30
        draw.line((button_area_x_start, line_y_top, button_area_x_end, line_y_top), fill=(200, 200, 200), width=1)
        draw.line((button_area_x_start, line_y_bottom, button_area_x_end, line_y_bottom), fill=(200, 200, 200), width=1)

        # Dibuja la línea de cierre en la parte superior derecha
        close_button_size = 20
        close_button_x = base_width - 40
        close_button_y = 10
        draw.rectangle([close_button_x, close_button_y, close_button_x + close_button_size, close_button_y + close_button_size], outline=(200, 200, 200), width=1)
        draw.line((close_button_x + 5, close_button_y + 5, close_button_x + close_button_size - 5, close_button_y + close_button_size - 5), fill=(200, 200, 200), width=2)
        draw.line((close_button_x + 5, close_button_y + close_button_size - 5, close_button_x + close_button_size - 5, close_button_y + 5), fill=(200, 200, 200), width=2)

        # Guardar la imagen en un buffer
        with io.BytesIO() as buf:
            base.save(buf, format='PNG')
            buf.seek(0)
            tweet_image = discord.File(fp=buf, filename='tweet_image.png')

        # Enviar solo la imagen
        await interaction.response.send_message(file=tweet_image)

    except Exception as e:
        # Manejo básico de excepciones
        print(f"Error al generar la imagen del tweet: {e}")
        await interaction.response.send_message("Hubo un error al generar el tweet.")


import random



@bot.command(name='shutdown')
@commands.has_permissions(administrator=True)
async def shutdown(ctx):
    await ctx.send("Apagando el bot...")
    await bot.close()

@shutdown.error
async def shutdown_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("No tienes permiso para usar este comando.")

from discord import app_commands
import discord
from datetime import datetime, timedelta, timezone

@bot.tree.command(name="timeout", description="Añadir o quitar timeout a un usuario")
@app_commands.describe(user="Usuario al que se le aplicará el timeout", duration="Duración del timeout en minutos", reason="Razón del timeout", action="Acción a realizar (add o remove)")
async def timeout(interaction: discord.Interaction, user: discord.User, duration: int = None, reason: str = None, action: str = 'add'):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("No tienes permiso para usar este comando.", ephemeral=True)
        return

    guild = interaction.guild
    if not guild:
        await interaction.response.send_message("Este comando solo puede usarse en un servidor.", ephemeral=True)
        return

    member = guild.get_member(user.id)
    if not member:
        await interaction.response.send_message("No se pudo encontrar al usuario en este servidor.", ephemeral=True)
        return

    if action == 'add':
        if not duration or duration <= 0:
            await interaction.response.send_message("Debes especificar una duración válida para el timeout.", ephemeral=True)
            return
        
        try:
            end_time = datetime.now(timezone.utc) + timedelta(minutes=duration)
            await member.timeout(end_time, reason=reason)
            embed = discord.Embed(title="Timeout Aplicado", description=f"**Usuario:** {user}\n**Duración:** {duration} minutos\n**Razón:** {reason}", color=discord.Color.green())
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"Error al aplicar el timeout: {e}", ephemeral=True)
    
    elif action == 'remove':
        try:
            await member.timeout(None, reason="Timeout removido")
            embed = discord.Embed(title="Timeout Removido", description=f"**Usuario:** {user}", color=discord.Color.red())
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"Error al remover el timeout: {e}", ephemeral=True)
    else:
        await interaction.response.send_message("Acción no válida. Usa 'add' para añadir o 'remove' para quitar el timeout.", ephemeral=True)


@bot.tree.command(name="changebotuser", description="Cambia el apodo del bot en el servidor actual.")
@app_commands.describe(nickname="El nuevo apodo para el bot.")
async def changebotuser(interaction: discord.Interaction, nickname: str):
    # Verifica si el usuario tiene permisos de administrador
    if not any(role.permissions.administrator for role in interaction.user.roles):
        await interaction.response.send_message("No tienes permiso para usar este comando.", ephemeral=True)
        return

    bot_member = interaction.guild.get_member(bot.user.id)
    
    # Cambia el apodo del bot
    try:
        await bot_member.edit(nick=nickname)
        await interaction.response.send_message(f"El apodo del bot ha sido cambiado a: {nickname}")
    except discord.Forbidden:
        await interaction.response.send_message("No tengo permisos para cambiar el apodo del bot.")
    except discord.HTTPException as e:
        await interaction.response.send_message(f"Error al cambiar el apodo: {e}")



@bot.command(name="leave")
@commands.has_permissions(administrator=True)
async def leave(ctx):
    if not ctx.guild:
        await ctx.send("Este comando solo se puede usar en un servidor.")
        return

    await ctx.send("PythonBOT ha abandonado este servidor, buena suerte")
    await ctx.guild.leave()

@leave.error
async def leave_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("No tienes permiso para usar este comando.")

@bot.event
async def on_member_join(member):
    with sqlite3.connect('bienvenida.db') as db:
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bienvenida (
                id INTEGER PRIMARY KEY,
                servidor_id INTEGER, 
                estado TEXT,
                channel_id INTEGER,
                rol_id INTEGER
            )
        ''')
        cursor.execute('SELECT estado, channel_id, rol_id FROM bienvenida WHERE servidor_id = ?', (member.guild.id,))
        row = cursor.fetchone()

        if row is not None and row[0].lower() == 'habilitar':
            channel = bot.get_channel(row[1])
            new_role = member.guild.get_role(row[2])  # ID del rol de bienvenida

            await member.add_roles(new_role)

            embed = discord.Embed(
                title=f"¡Bienvenido {member.name}!", 
                description=(
                    f"Hola {member.mention}, bienvenido/a a {member.guild.name}!\n\n"
                    "Esperamos que disfrutes de tu estancia en nuestro servidor. Se te ha otorgado el rol de bienvenida.\n"
                    "Recuerda que debes leer las **reglas** en #📜reglas, para evitar conflictos.\n\n"
                    "**__¡No nos hacemos responsables del mal uso que le puedan dar a las herramientas de este servidor!__**"
                ), 
                color=discord.Color.random()
            )
            embed.set_thumbnail(url=member.avatar.url)
            await channel.send(f"{member.mention}", embed=embed)


@bot.tree.command(
    name="estado_bienvenida",
    description="Revisa el estado del canal de bienvenida",
)
async def estado_bienvenida(interaction):
    try:
        with sqlite3.connect('bienvenida.db') as db:
            cursor = db.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bienvenida (
                    id INTEGER PRIMARY KEY,
                    servidor_id INTEGER,
                    estado TEXT,
                    channel_id INTEGER,
                    rol_id INTEGER
                )
            ''')
            cursor.execute('SELECT estado, channel_id, rol_id FROM bienvenida WHERE servidor_id = ?', (interaction.guild.id,))
            row = cursor.fetchone()

            if row is None:
                await interaction.response.send_message("El estado del canal de bienvenida no está configurado.")
            else:
                estado = row[0]
                channel_id = row[1]
                role_id = row[2]
                message = (
                    f"El estado del canal de bienvenida es: {estado}\n"
                    f"Canal: <#{channel_id}>\n"
                    f"Rol: <@&{role_id}>"
                )
                await interaction.response.send_message(message)

    except Exception as e:
        await interaction.response.send_message(f"Ocurrió un error: {e}")
        return

@commands.has_permissions(administrator=True)
@bot.command(name='bardeo_nicorainbowmierdas')
async def bardeo_nicorainbowmierdas(ctx):
    mensaje_grande = ("Nico, la verdad es que eres un desastre. Cada vez que intentas hacer algo, "
                      "parece que solo logras empeorarlo. Eres como una tormenta de errores, "
                      "una avalancha de decisiones equivocadas. Tu capacidad para fallar es "
                      "impresionante, casi como si fuera un talento innato. ¿Recuerdas la última "
                      "vez que intentaste ayudar con algo? Fue como ver un espectáculo de comedia, "
                      "pero sin la parte graciosa. Si la incompetencia fuera un deporte, tendrías "
                      "todas las medallas de oro. Eres un arco iris de errores, una sinfonía de "
                      "fracasos. En serio, Nico, a veces me pregunto si lo haces a propósito para "
                      "ver hasta dónde puedes llegar con tu increíble habilidad para la ineptitud. "
                      "No hay un solo momento en el que no me sorprendas con un nuevo nivel de "
                      "desastre. Es casi como si estuvieras intentando ganar un premio al peor en "
                      "todo, y créeme, lo estás logrando. Tu falta de habilidad y sentido común es "
                      "sorprendente. Si hubiera un campeonato mundial de errores, estarías en el "
                      "podio cada vez. Nico, eres el maestro de los desastres, el rey de los "
                      "fracasos, el emperador de la ineptitud. No puedo imaginarme cómo sería un "
                      "día sin que cometieras un error garrafal. Sigue así, Nico, y quizás algún "
                      "día consigas batir tu propio récord de fracasos. En fin, solo quería que "
                      "supieras lo mucho que destacas, pero no por las razones que te gustaría.")
    
    await ctx.send(mensaje_grande)

@bot.tree.command(name="change_server_name", description="Cambia el nombre del servidor y la imagen (opcional).")
async def change_server_name(
    interaction: discord.Interaction, 
    new_name: str, 
    image: discord.Attachment = None
):
    # Verifica si el usuario tiene permisos de administrador
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("No tienes permisos suficientes para usar este comando.", ephemeral=True)
        return
    
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message("Este comando solo puede usarse en un servidor.")
        return
    
    try:
        # Cambia el nombre del servidor
        await guild.edit(name=new_name)
        
        # Opcionalmente cambia la imagen del servidor
        if image:
            # Verifica la extensión del archivo
            if image.content_type in ['image/jpeg', 'image/png']:
                # Descarga el archivo
                image_data = await image.read()
                await guild.edit(icon=image_data)
            else:
                await interaction.response.send_message("La imagen debe estar en formato JPEG o PNG.", ephemeral=True)
                return
        
        # Crea un embed para notificar el cambio
        embed = discord.Embed(
            title="¡Nombre del servidor cambiado!",
            description=f"El nombre del servidor ha sido cambiado a `{new_name}`.",
            color=discord.Color.green()
        )
        
        if image:
            embed.set_image(url=image.url)
        
        await interaction.response.send_message(embed=embed)
    except discord.Forbidden:
        await interaction.response.send_message("No tengo permisos para cambiar el nombre o la imagen del servidor.")
    except discord.HTTPException as e:
        await interaction.response.send_message(f"Ocurrió un error al intentar cambiar el nombre o la imagen: {e}")


MAX_FIELDS_PER_EMBED = 25

@bot.tree.command(name="help", description="Muestra todos los comandos disponibles.")
async def help_command(interaction: discord.Interaction):
    # Obtener todos los comandos de slash
    commands_list = bot.tree.get_commands()

    def create_embed(commands: list) -> discord.Embed:
        """Crea un embed con una lista de comandos"""
        embed = discord.Embed(
            title="Lista de Comandos",
            description="Aquí está la lista de comandos.",
            color=discord.Color.blue()
        )
        for cmd in commands:
            embed.add_field(
                name=f"/{cmd.name}",
                value=cmd.description or "Sin descripción",
                inline=True
            )
        return embed

    async def send_all_embeds(interaction: discord.Interaction, commands: list):
        """Envía múltiples embeds si hay más de 25 comandos"""
        embeds = []
        for i in range(0, len(commands), MAX_FIELDS_PER_EMBED):
            embeds.append(create_embed(commands[i:i+MAX_FIELDS_PER_EMBED]))

        for embed in embeds:
            await interaction.followup.send(embed=embed)

    # Enviar mensaje de "cargando" mientras se crean los embeds
    await interaction.response.send_message("Cargando la lista de comandos...")

    # Enviar todos los embeds
    await send_all_embeds(interaction, commands_list)

@bot.tree.command(name="rules", description="Displays the rules with their descriptions.")
@app_commands.checks.has_permissions(administrator=True)
async def rules(interaction: discord.Interaction,
                rule1: str = None, rule2: str = None, rule3: str = None,
                rule4: str = None, rule5: str = None, rule6: str = None,
                rule7: str = None, rule8: str = None, rule9: str = None,
                rule10: str = None, rule11: str = None, rule12: str = None,
                rule13: str = None, rule14: str = None, rule15: str = None):
    
    rules_list = [rule1, rule2, rule3, rule4, rule5, rule6, rule7, rule8, rule9, rule10, rule11, rule12, rule13, rule14, rule15]
    rules_list = [rule for rule in rules_list if rule is not None]

    embed = discord.Embed(title="Server Rules")

    for i, rule in enumerate(rules_list, 1):
        if '(' in rule and ')' in rule:
            rule_text, description = rule.split('(', 1)
            description = description.rstrip(')')
        else:
            rule_text, description = rule, ''
        
        embed.add_field(name=rule_text.strip(), value=description.strip() or "No description provided", inline=False)
    
    await interaction.response.send_message(embed=embed)

@rules.error
async def rules_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)

import discord
from discord.ext import commands
from datetime import datetime, timedelta, timezone

# Limitar a 5 minutos (en segundos)
TIMEOUT_DURATION = 5 * 60
STAFF_ID = 1138048154734960720  # Tu ID para recibir notificaciones

@bot.command()
@commands.has_permissions(administrator=True)
async def timeout(ctx, user_id: int, *, reason="No reason provided"):
    user = ctx.guild.get_member(user_id)
    if user:
        try:
            end_time = datetime.now(timezone.utc) + timedelta(seconds=TIMEOUT_DURATION)
            await user.timeout(end_time, reason=reason)
            await user.send(f'Has sido silenciado en {ctx.guild.name} por 5 minutos debido a: {reason}\n\nSi tienes algún problema con esta acción, no dudes en escribirle a un staff del servidor.')
            await ctx.send(f'Usuario {user} ha sido silenciado por 5 minutos debido a: {reason}')
            
            # Notificar al staff
            staff_user = await bot.fetch_user(STAFF_ID)
            if staff_user:
                await staff_user.send(f'El usuario {user} ha sido silenciado por 5 minutos debido a: {reason}')
        except Exception as e:
            await ctx.send(f'Error al intentar silenciar al usuario: {e}')
    else:
        await ctx.send('Usuario no encontrado.')

import discord
from discord.ext import commands

STAFF_ID = 1138048154734960720  # Tu ID para recibir notificaciones

@bot.command()
@commands.has_permissions(administrator=True)
async def ban(ctx, user_id: int, *, reason="No reason provided"):
    user = ctx.guild.get_member(user_id)
    if user:
        try:
            await user.send(f'Has sido baneado de {ctx.guild.name} por: {reason}\n\nSi tienes algún problema con esta acción, no dudes en escribirle a un staff del servidor.')
        except discord.Forbidden:
            pass
        try:
            await user.ban(reason=reason)
            await ctx.send(f'Usuario {user} ha sido baneado por: {reason}')
            
            # Notificar al staff
            staff_user = await bot.fetch_user(STAFF_ID)
            if staff_user:
                await staff_user.send(f'El usuario {user} ha sido baneado por: {reason}')
        except Exception as e:
            await ctx.send(f'Error al intentar banear al usuario: {e}')
    else:
        await ctx.send('Usuario no encontrado.')

import discord
from discord.ext import commands

STAFF_ID = 1138048154734960720  # Tu ID para recibir notificaciones

@bot.command()
async def kick(ctx, user_id: int, *, reason="No reason provided"):
    user = ctx.guild.get_member(user_id)
    if user:
        try:
            await user.send(f'Has sido expulsado de {ctx.guild.name} por: {reason}\n\nSi tienes algún problema con esta acción, no dudes en escribirle a un staff del servidor.')
        except discord.Forbidden:
            pass
        try:
            await user.kick(reason=reason)
            await ctx.send(f'Usuario {user} ha sido expulsado por: {reason}')
            
            # Notificar al staff
            staff_user = await bot.fetch_user(STAFF_ID)
            if staff_user:
                await staff_user.send(f'El usuario {user} ha sido expulsado por: {reason}')
        except Exception as e:
            await ctx.send(f'Error al intentar expulsar al usuario: {e}')
    else:
        await ctx.send('Usuario no encontrado.')

import discord
from discord.ext import commands
import random
import asyncio


@bot.command()
async def sorteo(ctx, cantidad: int, *identificadores: int):
    """Realiza un sorteo de miembros para roles o usuarios específicos."""
    if cantidad < 1 or cantidad > 3:
        await ctx.send("La cantidad de ganadores debe estar entre 1 y 3.")
        return

    participantes = []

    for id_ in identificadores:
        role = ctx.guild.get_role(id_)
        user = ctx.guild.get_member(id_)

        if role:
            miembros = [member for member in role.members if not member.bot]
            if miembros:
                participantes.extend(miembros)
        elif user:
            if not user.bot:
                participantes.append(user)
        else:
            await ctx.send(f"No se encontró el rol o el usuario con ID {id_}.")
            return

    if len(participantes) < cantidad:
        await ctx.send("No hay suficientes participantes para seleccionar el número de ganadores especificado.")
        return

    ganadores = random.sample(participantes, cantidad)
    bot.ganadores = ganadores  # Guardar los ganadores para usarlos más tarde

    # Crear un mensaje estético usando un embed
    nombres_ganadores = []
    for i, ganador in enumerate(ganadores, start=1):
        puesto = ""
        if i == 1:
            puesto = "🥇 Primer puesto"
        elif i == 2:
            puesto = "🥈 Segundo puesto"
        elif i == 3:
            puesto = "🥉 Tercer puesto"

        nombres_ganadores.append(f"{puesto} - {ganador.mention}")

    embed = discord.Embed(title="🎉 Resultado del Sorteo 🎉", description="\n".join(nombres_ganadores), color=discord.Color.green())
    embed.set_footer(text=f"Realizado por {ctx.author}")

    # Enviar el mensaje del sorteo
    sorteo_mensaje = await ctx.send(embed=embed)

    # Enviar mensaje de verificación al supervisor
    verificacion_mensaje = await ctx.send(f"{ctx.author.mention}, por favor verifica el sorteo y reacciona con ✅ si todo está correcto.")
    
    bot.verificacion_mensaje_id = verificacion_mensaje.id  # Guardar el ID del mensaje de verificación
    bot.sorteo_author_id = ctx.author.id  # Guardar el ID del autor del sorteo

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) == "✅" and reaction.message.id == verificacion_mensaje.id

    try:
        # Esperar la reacción del supervisor
        await bot.wait_for('reaction_add', timeout=300.0, check=check)
        
        # Borrar el mensaje de verificación
        await verificacion_mensaje.delete()

        # Enviar DM al supervisor para que personalice los mensajes para los ganadores
        for idx, ganador in enumerate(bot.ganadores, start=1):
            try:
                # Preguntar al supervisor qué mensaje enviar al ganador
                await ctx.author.send(f"Mensaje para el ganador del {idx}° puesto ({ganador.mention}):")
                
                def check_dm(msg):
                    return msg.author == ctx.author and isinstance(msg.channel, discord.DMChannel)

                # Esperar la respuesta del supervisor en su DM
                supervisor_msg = await bot.wait_for('message', check=check_dm)
                mensaje_personalizado = supervisor_msg.content

                # Enviar el mensaje personalizado al ganador
                await ganador.send(f"¡Felicidades! {ganador.mention} {mensaje_personalizado}")

            except discord.Forbidden:
                await ctx.send(f"No se pudo enviar un mensaje directo a {ganador.mention}.")

        # Notificar en el canal original que los mensajes fueron enviados
        await ctx.send("Sorteo verificado por el supervisor. Se ha enviado un DM a todos los ganadores, si teneis algun problema escribirle al supervisor del sorteo.")

    except asyncio.TimeoutError:
        await ctx.send("El supervisor no verificó los resultados a tiempo.")





@bot.command()
@commands.is_owner()
async def servidores(ctx):
    """Muestra los servidores en los que está presente el bot, el número de miembros en cada uno, y envía una invitación para cada uno."""
    mensaje = "Estoy en los siguientes servidores:\n"
    mensajes_enviados = 0
    
    for guild in bot.guilds:
        try:
            # Intentar crear una invitación en el canal general del servidor
            general_channel = discord.utils.get(guild.text_channels, name="general")
            if general_channel:
                invite = await general_channel.create_invite(max_age=3600, max_uses=1)  # Invitación válida por 1 hora y 1 uso
                mensaje += f"{guild.name} - {guild.member_count} miembros - Invitación: {invite.url}\n"
            else:
                mensaje += f"{guild.name} - {guild.member_count} miembros - No se pudo generar invitación\n"
        except discord.Forbidden:
            mensaje += f"{guild.name} - {guild.member_count} miembros - No tengo permiso para generar invitaciones\n"
        except Exception as e:
            mensaje += f"{guild.name} - {guild.member_count} miembros - Error: {e}\n"
        
        # Enviar el mensaje en fragmentos si excede el límite de 2000 caracteres
        while len(mensaje) > 2000:
            await ctx.send(mensaje[:2000])
            mensajes_enviados += 1
            mensaje = mensaje[2000:]
    
    # Enviar cualquier mensaje restante
    if mensaje:
        await ctx.send(mensaje)
        mensajes_enviados += 1
    
    # Enviar el conteo de mensajes enviados
    await ctx.send(f"El bot envió un total de {mensajes_enviados} mensajes.")



@bot.command(name="leave_servers")
@commands.is_owner()
async def leave_servers(ctx):
    try:
        await ctx.send("Saliendo de todos los servidores...")
        for guild in bot.guilds:
            await guild.leave()
            print(f"El bot ha salido del servidor: {guild.name} (ID: {guild.id})")
        await ctx.send("El bot ha salido de todos los servidores.")
    except Exception as e:
        print(f"Error al intentar salir de los servidores: {e}")
        await ctx.send("Ocurrió un error al intentar salir de los servidores.")

@bot.command(name="DM")
@commands.has_permissions(administrator=True)
async def dm(ctx, user_id: int, *, message: str):
    try:
        user = await bot.fetch_user(user_id)
        await user.send(message)
        await ctx.send(f"Mensaje enviado a {user.name}.")
    except Exception as e:
        print(f"Error al enviar el mensaje: {e}")
        await ctx.send("No se pudo enviar el mensaje. Verifica el ID del usuario o asegúrate de que el bot tiene permisos para enviar DMs.")

@bot.command(name="invite")
async def invite(ctx):
    try:
        # Reemplaza "YOUR_BOT_CLIENT_ID" con el ID del cliente de tu bot
        invite_link = "https://discord.com/oauth2/authorize?client_id=1265780332616220714&permissions=8&scope=bot%20applications.commands"
        
        # Envía el enlace al DM del usuario
        await ctx.author.send(f"¡Hola! Aquí tienes el enlace para invitarme a otros servidores:\n{invite_link}")
        
        # Responde en el canal para que el usuario revise sus DMs
        await ctx.send("Revisa tus DMs, te envié el enlace para invitarme a otros servidores. 🚀")
    except discord.Forbidden:
        # Si el bot no puede enviar DMs, notifica al usuario en el canal
        await ctx.send("No puedo enviarte un DM. Por favor, habilita tus mensajes directos para recibir el enlace. 🙏")
    except Exception as e:
        # Maneja cualquier otro error inesperado
        print(f"Error al enviar el enlace de invitación: {e}")
        await ctx.send("Ocurrió un error al intentar enviarte el enlace. Inténtalo de nuevo más tarde.")

import sqlite3

# Create or connect to the database
conn = sqlite3.connect("warnings.db")
cursor = conn.cursor()

# Create the table for warnings with guild_id to make it server-specific
cursor.execute("""
CREATE TABLE IF NOT EXISTS warnings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    guild_id INTEGER NOT NULL,
    reason TEXT NOT NULL,
    severity TEXT NOT NULL,
    moderator_id INTEGER NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()


# Function to add a warning to the database
def add_warning(user_id: int, guild_id: int, reason: str, severity: str, moderator_id: int):
    cursor.execute("""
    INSERT INTO warnings (user_id, guild_id, reason, severity, moderator_id)
    VALUES (?, ?, ?, ?, ?)
    """, (user_id, guild_id, reason, severity, moderator_id))
    conn.commit()


# Function to get all warnings for a user in a specific server
def get_warnings(user_id: int, guild_id: int):
    cursor.execute("""
    SELECT reason, severity, moderator_id, timestamp 
    FROM warnings 
    WHERE user_id = ? AND guild_id = ?
    """, (user_id, guild_id))
    return cursor.fetchall()


# Function to remove all warnings for a user in a specific server
def remove_warnings(user_id: int, guild_id: int):
    cursor.execute("""
    DELETE FROM warnings 
    WHERE user_id = ? AND guild_id = ?
    """, (user_id, guild_id))
    conn.commit()


# Slash command: Warn
@bot.tree.command(name="warn", description="Warn a user and record the warning.")
async def warn(
    interaction: discord.Interaction, 
    user: discord.Member, 
    reason: str, 
    severity: str
):
    """
    Warns a user and records the warning in the database.
    """
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("You do not have permission to warn users.", ephemeral=True)
        return

    severity = severity.lower()
    if severity not in ["low", "med", "higher"]:
        await interaction.response.send_message("Severity must be `Low`, `Med`, or `Higher`.", ephemeral=True)
        return

    # Add the warning to the database with guild_id
    add_warning(user.id, interaction.guild.id, reason, severity, interaction.user.id)

    # Severity colors
    severity_colors = {
        "low": discord.Color.green(),
        "med": discord.Color.gold(),
        "higher": discord.Color.red()
    }

    # Create embed
    embed = discord.Embed(
        title="⚠️ Warning Issued",
        color=severity_colors[severity]
    )
    embed.add_field(name="User", value=f"{user.mention} ({user.id})", inline=False)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Severity Level", value=severity.capitalize(), inline=False)
    embed.set_footer(text=f"Warned by {interaction.user.name}")

    await interaction.response.send_message(embed=embed)

    # Send DM to the user
    try:
        await user.send(embed=embed)
    except discord.Forbidden:
        await interaction.followup.send("Could not send a DM to the user. DMs are disabled.", ephemeral=True)


# Slash command: Warnings
@bot.tree.command(name="warnings", description="View all warnings of a user in this server.")
async def warnings(interaction: discord.Interaction, user: discord.Member):
    """
    View all warnings of a user in the current server.
    """
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("You do not have permission to view warnings.", ephemeral=True)
        return

    user_warnings = get_warnings(user.id, interaction.guild.id)

    if not user_warnings:
        await interaction.response.send_message(f"✅ {user.mention} has no warnings in this server.")
    else:
        embed = discord.Embed(
            title=f"⚠️ Warnings for {user.name}",
            color=discord.Color.orange()
        )

        for idx, (reason, severity, moderator_id, timestamp) in enumerate(user_warnings, start=1):
            embed.add_field(
                name=f"Warning #{idx}",
                value=f"**Reason:** {reason}\n**Severity:** {severity.capitalize()}\n**Moderator:** <@{moderator_id}>\n**Date:** {timestamp}",
                inline=False
            )

        await interaction.response.send_message(embed=embed)


# Slash command: Unwarn
@bot.tree.command(name="unwarn", description="Remove all warnings for a user in this server.")
async def unwarn(interaction: discord.Interaction, user: discord.Member):
    """
    Removes all warnings for a user in the current server.
    """
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("You do not have permission to remove warnings.", ephemeral=True)
        return

    # Remove warnings from the database for the current guild
    remove_warnings(user.id, interaction.guild.id)

    embed = discord.Embed(
        title="✅ Warnings Cleared",
        color=discord.Color.green()
    )
    embed.add_field(name="User", value=f"{user.mention} ({user.id})", inline=False)
    embed.add_field(name="Action", value="All warnings have been removed.", inline=False)
    embed.set_footer(text=f"Cleared by {interaction.user.name}")

    await interaction.response.send_message(embed=embed)


# Ejecutar el bot
bot.run(DISCORD_TOKEN)


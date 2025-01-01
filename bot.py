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

@bot.tree.command(name='8ball', description='Ask a question and you will receive an answer.')
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

@bot.tree.command(name='poll', description='Create a server-wide poll.')
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


from discord import app_commands
import discord
from datetime import datetime, timedelta, timezone

@bot.tree.command(name="timeout", description="Add or remove timeout for a user.")
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


@bot.tree.command(name="changebotuser", description="Changes the bot's nickname on the current server.")
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





@bot.tree.command(name="change_server_name", description="Change the server name and image (optional).")
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

@bot.tree.command(name="help", description="Displays all available commands.")
async def help_command(interaction: discord.Interaction):
    # Obtener todos los comandos de slash
    commands_list = bot.tree.get_commands()

    def create_embed(commands: list) -> discord.Embed:
        """Crea un embed con una lista de comandos"""
        embed = discord.Embed(
            title="📋Commands List",
            description="Here are the list of bot commands:",
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

import discord
from discord import app_commands
from discord.ext import commands
import sqlite3

# Crea la base de datos para guardar los reportes
def create_db(guild_id):
    conn = sqlite3.connect('reports.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS reports (
                    guild_id INTEGER,
                    user_id INTEGER,
                    reported_user_id INTEGER,
                    reason TEXT,
                    PRIMARY KEY (guild_id, user_id, reported_user_id))''')
    conn.commit()
    conn.close()

# Guarda los reportes en la base de datos
def save_log(guild_id, user_id, reported_user_id, reason):
    conn = sqlite3.connect('reports.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO reports (guild_id, user_id, reported_user_id, reason) VALUES (?, ?, ?, ?)", 
              (guild_id, user_id, reported_user_id, reason))
    conn.commit()
    conn.close()

# Comando para reportar a un usuario
@bot.tree.command(name="report", description="Report a member of the server.")
@app_commands.describe(user="The user you are reporting", reason="The reason for the report")
async def report(interaction: discord.Interaction, user: discord.User, reason: str):
    # Crear base de datos si no existe para el servidor
    create_db(interaction.guild.id)

    # Guardar el reporte en la base de datos
    save_log(interaction.guild.id, interaction.user.id, user.id, reason)

    # Crear el embed para enviar al canal de moderación
    embed = discord.Embed(
        title="User Report",
        description=f"A member has reported {user.mention}.",
        color=discord.Color.red()
    )
    embed.add_field(name="Reported User", value=user.mention, inline=False)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Reported by", value=interaction.user.mention, inline=False)
    embed.set_footer(text=f"Reported in {interaction.guild.name}", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)

    # Enviar el embed al canal de moderación
    mod_channel = discord.utils.get(interaction.guild.text_channels, name="reports")  # Asegúrate de tener este canal
    if mod_channel:
        await mod_channel.send(embed=embed)
    else:
        await interaction.response.send_message("The moderation channel is not set up.", ephemeral=True)

    # Responder solo una vez a la interacción
    if not interaction.response.is_done():
        await interaction.response.send_message(f"Thank you for reporting {user.mention}. The report has been sent to the moderators.", ephemeral=True)

# Comando para ver los logs de reportes
@bot.tree.command(name="logs", description="See the reports logs.")
async def logs(interaction: discord.Interaction):
    # Conectar a la base de datos y obtener los reportes
    conn = sqlite3.connect('reports.db')
    c = conn.cursor()
    c.execute("SELECT * FROM reports WHERE guild_id = ?", (interaction.guild.id,))
    reports = c.fetchall()
    conn.close()

    if not reports:
        await interaction.response.send_message("No reports found for this server.", ephemeral=True)
        return

    # Crear embed para mostrar los logs de reportes
    embed = discord.Embed(
        title="Reports Logs",
        description=f"Here are the reports for {interaction.guild.name}.",
        color=discord.Color.blue()
    )

    for report in reports:
        user = await interaction.guild.fetch_member(report[1])  # Usuario que hizo el reporte
        reported_user = await interaction.guild.fetch_member(report[2])  # Usuario reportado
        embed.add_field(
            name=f"Report by {user.display_name}",
            value=f"Reported: {reported_user.display_name}\nReason: {report[3]}",
            inline=False
        )

    await interaction.response.send_message(embed=embed)


# Ejecutar el bot
bot.run(DISCORD_TOKEN)
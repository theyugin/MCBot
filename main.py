import logging

from discord import errors

log_filename = 'log.txt'
logger = logging.getLogger('MCBot')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename=log_filename, encoding='utf-8', mode='w+')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

from utils import *
from discord.ext import commands
import os
import asyncio

bot_token = os.environ.get('MCBOT_TOKEN')
message_database = {}

client = commands.Bot(command_prefix=commands.when_mentioned_or("mcbot "))


async def message_updater():
    await client.wait_until_ready()
    while not client.is_closed():
        db = read_database()
        if len(db) > 0:
            for guild, channels in db.items():
                for channel, messages in channels.items():
                    for message in messages:
                        server_list = db[guild][channel][message]
                        output = ''
                        if len(server_list) > 0:
                            output = None
                            embed = status_message_generator(server_list)
                        else:
                            output = "No servers to monitor! Add some servers with `mcbot addserver` to be shown here."
                            embed = None
                        try:
                            msg = await client.get_guild(int(guild)).get_channel(int(channel)).fetch_message(
                                int(message))
                            await msg.edit(content=output, embed=embed)
                        except errors.NotFound:
                            db[guild][channel].pop(message)
                            remove_unused(db, guild, channel)
                            write_database(db)
                            logging.warning(f"MESSAGE NOT FOUND guild:{guild} channel:{channel} message:{message}")
        await asyncio.sleep(15)


@client.event
async def on_message_delete(message):
    guild, channel, id = str(message.guild.id), str(message.channel.id), str(message.id)
    if guild in message_database:
        if channel in message_database[guild]:
            if message in message_database[guild][channel]:
                message_database[guild][channel].pop(message)
                remove_unused(message_database, guild, channel)
                write_database(message_database)


@client.event
async def on_ready():
    global message_database
    message_database = read_database()
    logger.info(f"Connected as {client.user}")


@client.command("createmessage")
async def create_message(ctx):
    global message_database
    await ctx.message.delete()
    message = await ctx.send("New message created! Add some servers with `mcbot addserver` to be shown here.")
    logging.info(f"Message created in {message.guild.id}:{message.channel.id}:{message.id}")
    new_message = {str(message.guild.id): {str(message.channel.id): {str(message.id): []}}}
    message_database = deep_dict_merge(message_database, new_message)
    write_database(message_database)


@client.command("removemessage")
async def remove_message(ctx):
    global message_database
    cleanup = [ctx.message]
    if not str(ctx.message.guild.id) in message_database:
        await ctx.send("**No messages to delete in this guild!**", delete_after=5)
        await ctx.channel.delete_messages(cleanup)
        return
    else:
        message_list_string, associated_messages = generate_message_link_list(message_database, ctx, client)
        cleanup.append(
            await ctx.send("**Choose what message to delete (type cancel to cancel):**\n" + message_list_string))
        while True:
            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel

            user_response = await client.wait_for('message', check=check)
            if user_response.content == "cancel":
                ctx.channel.delete_messages(cleanup)
                return
            cleanup.append(user_response)
            message_number = user_response.content
            if message_number.isdigit():
                guild, channel, message = associated_messages[int(message_number) - 1]
                if int(message_number) > len(associated_messages) or int(message_number) < 1:
                    await user_response.delete()
                    cleanup.remove(user_response)
                    await ctx.send(content="Wrong message number! Try again.", delete_after=5)
                else:
                    message_database[guild][channel].pop(message)
                    remove_unused(message_database, guild, channel)
                    write_database(message_database)
                    await ctx.channel.delete_messages(cleanup)
                    msg = await client.get_guild(int(guild)).get_channel(int(channel)).fetch_message(int(message))
                    await msg.delete()
                    await ctx.send(f"Removed message #{message_number}!", delete_after=5)
                    return


@client.command("removeserver")
async def remove_server(ctx):
    global message_database
    cleanup = [ctx.message]
    if not str(ctx.message.guild.id) in message_database:
        await ctx.send("**No servers to delete in this guild!**", delete_after=5)
        await ctx.channel.delete_messages(cleanup)
    else:
        message_list_string, associated_messages = generate_message_link_list(message_database, ctx, client)
        cleanup.append(await ctx.send(
            "**Choose what message to delete from (type cancel to cancel Pepega):**\n" + message_list_string))
        while True:
            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel

            user_response = await client.wait_for('message', check=check)
            if user_response.content == "cancel":
                await ctx.channel.delete_messages(cleanup)
                return
            cleanup.append(user_response)
            message_number = user_response.content
            if message_number.isdigit():
                guild, channel, message = associated_messages[int(message_number) - 1]
                if int(message_number) > len(associated_messages) or int(message_number) < 1:
                    await user_response.delete()
                    cleanup.remove(user_response)
                    await ctx.send(content="Wrong message number! Try again.", delete_after=5)
                else:
                    if len(message_database[guild][channel][message]) == 0:
                        await ctx.send("No servers in this message! Try again.", delete_after=5)
                    else:
                        cleanup.append(await ctx.send(
                            "**What server do you want to remove from this message? Type it's address:**"))
                        while True:
                            user_response = await client.wait_for('message', check=check)
                            cleanup.append(user_response)
                            if user_response.content == "cancel":
                                await ctx.channel.delete_messages(cleanup)
                                return
                            if user_response.content in message_database[guild][channel][message]:
                                message_database[guild][channel][message].remove(user_response.content)
                                write_database(message_database)
                                await ctx.channel.delete_messages(cleanup)
                                await ctx.send(
                                    f"Removed server {user_response.content} from message #{message_number}!",
                                    delete_after=5)
                                return
                            else:
                                ctx.send("Wrong server address! Try again.", delete_after=5)

@client.command("addserver")
async def add_server(ctx):
    global message_database
    response = "**What message do you want to add your server to? (type cancel to cancel)**\n"
    cleanup = [ctx.message]
    message_list_string, associated_messages = generate_message_link_list(message_database, ctx, client)
    response += message_list_string
    cleanup.append(await ctx.send(response))
    if not str(ctx.message.guild.id) in message_database:
        await ctx.send("**No messages to add server to in this guild!**", delete_after=5)
        await ctx.channel.delete_messages(cleanup)
    else:
        while True:
            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel

            user_response = await client.wait_for('message', check=check)
            if user_response.content == "cancel":
                await ctx.channel.delete_messages(cleanup)
                return
            cleanup.append(user_response)
            if user_response.content.isdigit():
                message_number = int(user_response.content)
                if int(message_number) > len(associated_messages) or int(message_number) < 1:
                    await user_response.delete()
                    cleanup.remove(user_response)
                    await ctx.send(content="Wrong message number! Try again.", delete_after=5)
                else:
                    cleanup.append(await ctx.send("**Type server address to add to this message:**"))
                    user_response = await client.wait_for('message', check=check)
                    cleanup.append(user_response)
                    server_address = user_response.content
                    guild, channel, message = associated_messages[message_number - 1]
                    message_database[guild][channel][message].append(server_address)
                    await ctx.channel.delete_messages(cleanup)
                    await ctx.send(f"Added server {server_address} to #{message_number}!", delete_after=5)
                    write_database(message_database)
                    return


@client.command("messages")
async def messages(ctx):
    response = "**Links to all messages in this guild:**\n"
    message_list_string, _ = generate_message_link_list(message_database, ctx, client)
    response += message_list_string
    await ctx.message.delete()
    await ctx.send(response)


@client.command("ping")
async def ping(ctx):
    msg = await ctx.send('Pong!')
    logger.info(
        f"Ping sent in guild:{msg.guild.id}  in channel:{msg.channel.id} with message:{ctx.message.id} with response id:{msg.id}")


client.loop.create_task(message_updater())
client.run(bot_token)

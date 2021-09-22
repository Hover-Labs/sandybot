import asyncio
import functools
import os
import subprocess

import discord

client = discord.Client()
messages_lock = asyncio.Lock()
messages = {}

processing_lock = asyncio.Lock()

DISCORD_BOT_TOKEN = os.environ['DISCORD_BOT_TOKEN']

async def reset_sandbox(reaction):
    status_msg = await reaction.message.channel.send(":clock12: Bringing down the cluster...")
    print("Shutting down the cluster...")

    proc = await asyncio.create_subprocess_shell(
        'cd /root/bcdhub/ && make sandbox-down',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await proc.communicate()

    # print("Done! \n++= STDOUT =+++\n{}\n===============\n\n++= STDERR =+++\n{}\n===============".format(stdout, stderr))
    # await reaction.message.channel.send("Done!")
    # await reaction.message.channel.send("```{}```\n```{}```".format(stdout, stderr))

    await status_msg.edit(content=":clock3: Removing old snapshot data...")
    print("Removing old snapshot data...")

    proc = await asyncio.create_subprocess_shell(
        'rm -rf /var/lib/docker/volumes/bcdbox_bcdshare /var/lib/docker/volumes/bcdbox_db /var/lib/docker/volumes/bcdbox_esdata /var/lib/docker/volumes/bcdbox_flextesa /var/lib/docker/volumes/bcdbox_mqdata',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await proc.communicate()

    # print("Done! \n++= STDOUT =+++\n{}\n===============\n\n++= STDERR =+++\n{}\n===============".format(stdout, stderr))
    # await reaction.message.channel.send("Done!")
    # await reaction.message.channel.send("```{}```\n```{}```".format(stdout, stderr))

    await status_msg.edit(content=":clock6: Restoring Data...")
    print("Restoring data...")

    proc = await asyncio.create_subprocess_shell(
        'cd /root/sandbox-tools/ && rsync -ra sandbox-snapshots/ /var/lib/docker/volumes/',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await proc.communicate()

    await status_msg.edit(content=":clock9: Restarting the cluster...")
    print("Restarting things...")

    proc = await asyncio.create_subprocess_shell(
        'cd /root/bcdhub/ && timedatectl set-ntp false && timedatectl set-time "2021-09-22 04:20:00 UTC" && make flextesa-sandbox',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await proc.communicate()

    await status_msg.edit(content=":white_check_mark: Done!")

    # print("Done! \n++= STDOUT =+++\n{}\n===============\n\n++= STDERR =+++\n{}\n===============".format(stdout, stderr))
    # await reaction.message.channel.send("Done!")
    # await reaction.message.channel.send("```{}```\n```{}```".format(stdout, stderr))

async def remove_message(id, fulfilled=False):
    message = discord.utils.get(client.cached_messages, id=id)
    async with messages_lock:
        del messages[id]

    await message.reactions[0].remove(client.user)
    await message.reactions[1].remove(client.user)

    if fulfilled:
        await message.edit(content='~~' + message.content + '~~ On it!')
    else:
        await message.edit(content='~~' + message.content + '~~ Cancelled!')

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_reaction_add(reaction, user):
    if user == client.user:
        return

    # Random emotes from old messages
    if reaction.message.id not in messages:
        return

    if reaction.emoji == '❌':
        await remove_message(reaction.message.id)
        await reaction.message.channel.send("Ok, cancelling request!")
        processing_lock.release()

    elif reaction.emoji == '✅':
        await remove_message(reaction.message.id, fulfilled=True)
        await reaction.message.channel.send("Cleaning up the sandbox for <@!{}>!".format(user.id))

        await reset_sandbox(reaction)

        message = '''
Enjoy your freshly reset sandbox environment :). Things will take around 15s to become usable.

Kolibri Frontends:
**Kolibri Sandbox**: <https://sandbox.kolibri.finance/>
**KolibriDAO Sandbox**: <https://governance-sandbox.kolibri.finance/>
**Harbinger.live Sandbox**: <https://sandbox.harbinger.live/>

Environment Tools:
**Better-call.dev**: <https://bcd.hover.engineering>
**Node URL**: <https://sandbox.hover.engineering>

The sandbox is based on the Flextesa sandbox, and things are configured to work with the `alice` account which is well stocked with kDAO and tez for any needs you may have! 💰💸

Private key - `edsk3QoqBuvdamxouPhin7swCvkQNgq4jP5KZPbwWNnwdZpSpJiEbq`

Enjoy! <3
'''

        await reaction.message.channel.send(message)
        print("Finished! Releasing lock")

        processing_lock.release()

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!help'):
        await message.channel.send('''
<@!{}> Well howdy stranger! I'm Sandy the Sandybot and I'm designed to do one thing - refresh the Kolibri sandbox to a known good state!

To revert the sandbox to a snapshot, use the `!reset` command!      
'''.format(message.author.id))

    elif message.content.startswith('!reset'):
        if processing_lock.locked():
            await message.channel.send('There\'s currently a wipe in progress! Please try again later.')
            return

        await processing_lock.acquire()

        message = await message.channel.send('<@!{}> Are you sure?'.format(message.author.id))

        # Store this message for later
        async with messages_lock:
            messages[message.id] = message

        await message.add_reaction('✅')
        await message.add_reaction('❌')
        await asyncio.sleep(5)

        if message.id in messages:
            processing_lock.release()
            await message.reply('Cancelling this request!')
            await remove_message(message.id)

    elif any([member for member in message.mentions if member == client.user]):
        await message.channel.send('<@!{}> Sorry friend! No idea what you\'re talking about. Why not try the `!help` command?'.format(message.author.id))


client.run(DISCORD_BOT_TOKEN)

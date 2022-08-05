from sqlite3 import IntegrityError
import discord
import asyncio, aiosqlite 
import random, datetime
import wordle as w
import resources
from discord.ext import commands

intents = discord.Intents.all()
intents.message_content = True

wordles_in_progress = set()
timeout_percents = {}
blacklist_dict = {}
prefix = "~"
TOKEN = resources.TOKEN
  
#Initialize bot object and command prefix, delete default help command
bot = commands.Bot(command_prefix=prefix, help_command=None, intents=intents) 
bot.db = None

#Startup message
@bot.event
async def on_ready():
  if bot.db is None:
    bot.db = await aiosqlite.connect("discord_database.db")
  
  #Populate blacklist_dict with empty sets for each server, and also guild_sets
  guild_set = set()
  for guild in bot.guilds:
    guild_str = str(guild.id)
    guild_set.add(guild_str)
    blacklist_dict[guild_str] = set()

  #Removes all guilds from database that the bot isn't currently in
  async with bot.db.cursor() as cur1:
    await cur1.execute("SELECT guild_id FROM guilds")
    guild_list = await cur1.fetchall()
    for row in guild_list:
      if row[0] not in guild_set:
        async with bot.db.cursor() as cur2:
          await cur2.execute("DELETE FROM guilds WHERE guild_id = ?", [row[0]])
          await bot.db.commit()

  #ensures that all guilds are recorded beforehand (In case of bot getting added to/removed from a server while the bot is offline)
  for guild in bot.guilds:
    try:
      async with bot.db.cursor() as cursor:
        await cursor.execute("INSERT INTO guilds(guild_id) VALUES (?)", [str(guild.id)])
        await bot.db.commit()
    except IntegrityError:
      pass
  
  #Stores all timeout percents in a local dict so it doesn't have to retrieve from database every time
  async with bot.db.cursor() as cursor:
    await cursor.execute("SELECT guild_id, timeout_percent FROM guilds")
    guild_list = await cursor.fetchall()
    for tuple in guild_list:
      timeout_percents[tuple[0]] = tuple[1]

  #Stores all blacklisted phrase in a local dict-to-set  
  async with bot.db.cursor() as cursor:
    await cursor.execute("SELECT guild_id, phrase FROM blacklists")
    blacklist_list = await cursor.fetchall()
    for tuple in blacklist_list:
      blacklist_dict[tuple[0]].add(tuple[1])
  print(f'Login as {bot.user}, database up to date and local data stored')


#Populates guild table with new server information
@bot.event
async def on_guild_join(guild):
  try:
    async with bot.db.cursor() as cursor:
      await cursor.execute("INSERT INTO guilds(guild_id) VALUES (?)", [str(guild.id)])
    await bot.db.commit()
    print(f"New server added to database: '{guild.name}'")
  except IntegrityError:
    print(f"Server '{guild.name}' was attempted to be added, but already exists in database")

  timeout_percents[str(guild.id)] = 0
  await guild.system_channel.send("hi im new here")



#Removes server from guild table
@bot.event
async def on_guild_remove(guild):
  async with bot.db.cursor() as cursor:
    await cursor.execute("DELETE FROM guilds WHERE guild_id = ?", [str(guild.id)])
  await bot.db.commit()

  del timeout_percents[str(guild.id)]
  print(f"Server deleted from database: '{guild.name}'")


#General event to watch for blacklisted words and initiate the random timeout
@bot.event
async def on_message(message):
  if message.author == bot.user: return
  if message.channel.type == discord.ChannelType.private:
    await message.channel.send("I can't perform any commands in a direct message.")
    return
  await bot.process_commands(message)
  sender_is_admin = message.author.guild_permissions.administrator

  if bot.user in message.mentions:
    await message.channel.send("shut up bozo")
  
  if not sender_is_admin:
    message_fixed = message.content.lower()
    for phrase in blacklist_dict[str(message.guild.id)]:
      if phrase in message_fixed:
        await message.delete()
        return

  guild_id = str(message.guild.id)
  if random.random() < timeout_percents[guild_id]*0.01:
    if sender_is_admin:
      return
    minutes = 2
    duration = datetime.timedelta(minutes=minutes)
    await message.author.timeout_for(duration)
    await message.channel.send(f"{message.author.mention} was just randomly timed out for {minutes} minute(s).")

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~COMMANDS BELOW~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#Hidden currently, but checks if a given user has admin
'''
@bot.slash_command()
async def checkadmin(ctx, member: discord.Member):
  own =""
  if not member.guild_permissions.administrator: own = "not "
  await ctx.respond(f"That user **does {own}**have admin.")
'''


@bot.slash_command(name='bomb', description='Requires a user to say a phrase in order to avoid getting timed out.')
async def bomb(ctx, member: discord.Member, minutes: int, phrase: str):
  if ctx.channel.type == discord.ChannelType.private:
    await ctx.respond("I can't perform any commands in a direct message.")
    return
  if not ctx.author.guild_permissions.administrator:
    await ctx.respond(f"You don't have permission to use this command. Furthermore, you just tried to force {member.mention} to say \"**{phrase}**\". You should be ashamed of yourself.")
    return

  if member.guild_permissions.administrator:
    await ctx.respond("This user can't be timed out.")
    return

  max = 180
  if minutes > max:
    await ctx.respond(f"You cannot time out someone for more than {max} minutes with this command.")
    return
  
  countdown = 60
  def check(msg):
    return msg.author == member and msg.content == phrase
  
  await ctx.respond(f"User {member.mention} has had a bomb strapped to them. To disable it, they must type \'**{phrase}**\' exactly in the next {countdown} second(s). Otherwise, they'll be timed out for **{minutes} minute(s)**.")

  try:
    await bot.wait_for(event = 'message', check=check, timeout = countdown)
    await bot.send(f"The bomb has been defused! {member.mention} is safe...for now.")
  except asyncio.TimeoutError:
    duration = datetime.timedelta(minutes=minutes)
    await member.timeout_for(duration)
    await ctx.send(f"Time's up. The bomb exploded and {member.mention} has been timed out for {minutes} minute(s).")
  


@bot.command(name='botowner', description='Returns information about the owner of this bot.')
async def help(ctx):
  app_info = await bot.application_info()
  bot_owner = app_info.owner
  owner_embed = discord.Embed(title = f"{bot.user.name}'s owner is:", description=bot_owner)
  owner_embed.set_thumbnail(url=bot_owner.display_avatar.url)
  await ctx.send(embed = owner_embed)



@bot.command(name="blacklist", description = "Deals with blacklisted words and phrases in the server (Add words by following the command with '+', remove with '-').")
async def blacklist(ctx, *args):
  guild_str = str(ctx.guild.id)
  if not args:
    current_blacklist = blacklist_dict[guild_str]
    if not current_blacklist:
      await ctx.send("There are currently no words in the blacklist.")
      return
    blacklist_str = ""
    for phrase in current_blacklist:
      blacklist_str += f"{phrase}\n"
    await ctx.send(f"The following words and phrases have been blacklisted:\n{blacklist_str}")
    return
  
  if not ctx.author.guild_permissions.administrator:
    await ctx.send("You do not have permission to edit to the blacklist.")
    return

  if not (args[0] == "+" or args[0] == "-"):
    await ctx.send("Please enter a valid command.")
    return

  skipped_phrases = set()
  corrected_phrases = set()
  for phrase in args[1:]:
    phrase = phrase.lower()
    try:
      async with bot.db.cursor() as cursor:
        if args[0] == '+':
          await cursor.execute("INSERT INTO blacklists(guild_id, phrase) VALUES (?, ?)", (guild_str, phrase))
          blacklist_dict[guild_str].add(phrase)
          corrected_phrases.add(phrase)
        else:
          await cursor.execute("DELETE FROM blacklists WHERE guild_id = ? AND phrase = ?", (guild_str, phrase))
          blacklist_dict[guild_str].remove(phrase)
          corrected_phrases.add(phrase)
        await bot.db.commit()
        
    except Exception as e:
      skipped_phrases.add(phrase)
      print(f"User {ctx.author} attempted to edit the phrase '{phrase}' to the blacklist of server '{ctx.guild}' but failed, issue: {e}")
  
  difference_set = skipped_phrases.difference(corrected_phrases)
  if not difference_set:
    await ctx.send("Phrases dealt with successfully.")
  else:
    phrases_str = ""
    for phrase in difference_set:
      phrases_str += f"{phrase}\n"
    await ctx.send(f"The following phrases could not be dealt with:\n{phrases_str}")



@bot.command(name='randomtimeout', description="Controls the frequency of random timeouts in the server.")
async def randomtimeout(ctx, *args):
  if not args:
    await ctx.send(f"Currently, members of this server have a {timeout_percents[str(ctx.guild.id)]}% chance of randomly getting timed out.")
    return
  
  if not ctx.author.guild_permissions.administrator:
    await ctx.send(f"You do not have permission to update the frequency.")
    return

  try:
    percent = float(args[0])
  except Exception:
    await ctx.send(f"To change the frequency, please format your message like so: {prefix}{ctx.command.qualified_name} *(percent value here between 0 and 100)*")
    return
  
  if percent > 100 or percent < 0:
    await ctx.send(f"Please set the frequency within 0% to 100%.")
    return

  rounded_percent = round(float(args[0]), 4)
  rounded_msg = ""
  if percent != rounded_percent: rounded_msg = " (rounded to nearest ten-thousandth)"
  
  async with bot.db.cursor() as cursor:
    await cursor.execute("Update guilds SET timeout_percent = ? where guild_id = ?", (rounded_percent, str(ctx.guild.id)))
    await bot.db.commit()
  timeout_percents[str(ctx.guild.id)] = rounded_percent
  await ctx.send(f"Timeout frequency successfully changed to {rounded_percent}%{rounded_msg}.")



@bot.command(name='help', description='Returns a list of available commands for this bot.')
async def help(ctx):
  help_string = "**Available commands** (Slash commands not included):\n"
  for command in bot.commands:
    help_string += f"{prefix}{command.name} - {command.description}\n"
  await ctx.send(help_string)



@bot.command(name='wordlemulti', description='Plays a version of Wordle with multiplayer added.')
async def wordlemulti(ctx, *args):
  global wordles_in_progress
  quit_cmd = "quit"

  if ctx.channel.id in wordles_in_progress:
    await ctx.send(f"A Wordle game is already in progress in this text channel. Please complete the game or end it with {prefix}{quit_cmd}.")
    return

  #get number of wins needed
  try:
    wins_needed = int(args[0]) if args else 2
  except Exception:
    await ctx.send("Please enter a valid number of wins needed.")
    return

  #Add it to wordles_in_progress
  wordles_in_progress.add(ctx.channel.id)

  #Set up a timer message to get the users reacting to the message.
  timer = 10
  react_msg = await ctx.send(f"React to this message to play Wordle Multiplayer (First to {wins_needed}). You have {timer} second(s) to join.")
  await react_msg.add_reaction("🔤")
  while timer >= 0:
    await react_msg.edit(content = f"React to this message to play Wordle Multiplayer (First to {wins_needed}). You have {timer} second(s) to join.")
    await asyncio.sleep(1)
    timer -= 1
  cache_msg = discord.utils.get(bot.cached_messages, id = react_msg.id)
  reactions = cache_msg.reactions

  #Get the set of players playing Wordle (without the bot)
  player_set = set()
  for reaction in reactions:
    async for user in reaction.users():
      player_set.add(user)
  player_set.remove(bot.user)

  #Converts into list
  player_list = list(player_set)

  #Check to see if there are enough players
  if len(player_list) <= 0:
    await ctx.send("Not enough players for Wordle Multiplayer.")
    wordles_in_progress.remove(ctx.channel.id)
    return

  #~~~~~~~~~~~~~~~~~~SETUP PHASE~~~~~~~~~~~~~~~~~~
  adaptable_board_length = 6 if len(player_list) <= 3 else len(player_list) * 2

  #create dict of user ids for keeping track of wins 
  player_dict = {}
  for player in player_list:
    player_dict[player.id] = 0
  
  #Keeps track of round num
  num_rounds = 1

  print(f"User {ctx.author} began a Wordle Multiplayer game in \"{ctx.guild}/{ctx.channel}\".")
  #~~~~~~~~~~~~~~~~~~ROUND LOOP~~~~~~~~~~~~~~~~~~
  while True:  
    #Prints the scoreboard
    scoreboard = f"__Scoreboard (first to {wins_needed} wins)__\n"
    for counter, player in enumerate(player_set):
      scoreboard += f"{player.name}: {player_dict[player.id]}\n"
      '''
      if counter == len(player_list) - 1: break
      scoreboard += ", "
      '''
    await ctx.send(scoreboard)
    await asyncio.sleep(2)

    #Shuffles list
    random.shuffle(player_list)
    
    #Get the turn order and print
    player_order = "**Player Order**: "
    for i in range(len(player_list)):
      player_order += player_list[i].name
      if i == len(player_list) - 1: break
      player_order += " -> "
    
    await ctx.send(player_order)
    await asyncio.sleep(2)

    curr_i = 0
  
    #check to avoid other channels, the bot's messages, and commands, non-same-length words, AND ONLY THE CURRENT PLAYER PLAYING
    def check(msg):
      guess_len = len(msg.content.strip()) == len(game.answer) or msg.content == prefix + quit_cmd
      current_player = msg.author.id == player_list[curr_i].id
      same_channel = msg.channel.id == ctx.channel.id
      not_bot = not msg.author == bot.user
      not_cmd = True
      for command in bot.commands:
        if msg.content == prefix + command.name:
          not_cmd = False
          break
      return guess_len and current_player and same_channel and not_bot and not_cmd

    #initialize game
    game = w.Wordle(random.choice(w.WordSelector.answer_words_set), adaptable_board_length)

    #logs the game
    print(f"The answer for this round is {game.answer}.")

    round_still_going = True
    #~~~~~~~~~~~~~~~~~~TURN LOOP~~~~~~~~~~~~~~~~~~
    while game.curr_turn < game.turns and round_still_going:

      play_timer = 120
      await ctx.send(f"It's currently {player_list[curr_i].mention}'s turn. You have {play_timer} seconds, no countdown (Invalid guesses still count).")

      game_embed = discord.Embed(
        title = f"Wordle {game.curr_turn + 1}/6 - Round {num_rounds}",
        description = game.hint_board_to_string() + "\n" + game.used_board_to_string(),
        color = discord.Color.blue()
      )
      await ctx.send(embed = game_embed)

      #~~~~~~~~~~~~~~~~~~WAITING FOR MESSAGE SECTION~~~~~~~~~~~~~~~~~~
      try:
        response = await bot.wait_for(event = 'message', check=check, timeout = play_timer)
      except asyncio.TimeoutError:
        await ctx.send("Time's up.")
        break

      guess = response.content
      #exit command
      if guess == prefix + quit_cmd:
        await ctx.send(f"Current Wordle game has ended. The word was ||**{game.answer}**||.")
        wordles_in_progress.remove(ctx.channel.id)
        return

      try:
        game.make_guess(guess)
      except Exception as err:
        await ctx.send(err)
      
      #game winning state
      if guess == game.answer:
        player_dict[player_list[curr_i].id] += 1
        
        #True winning state
        await ctx.send(f"{player_list[curr_i].mention} wins the round. The word was **{game.answer}**. Number of attempts: {game.curr_turn}")

        if player_dict[player_list[curr_i].id] == wins_needed:
          await ctx.send(f"**<@{player_list[curr_i].id}> wins the game!**")
          wordles_in_progress.remove(ctx.channel.id)
          return
        round_still_going = False

      #Rotates through each player
      curr_i = curr_i + 1 if curr_i != len(player_list) - 1 else 0

    #game losing state
    if guess != game.answer: await ctx.send(f"No one wins the round. The word was **{game.answer}**")

    #increase round num
    num_rounds += 1
    await asyncio.sleep(2)
  

@bot.command(name='wordle', description='Plays a single Wordle game.')
async def wordle(ctx):
  #adds current channel to wordle in progress set
  global wordles_in_progress
  quit_cmd = "quit"

  if ctx.channel.id in wordles_in_progress:
    await ctx.send(f"A Wordle game is already in progress in this text channel. Please complete the game or end it with {prefix}{quit_cmd}.")
    return
  wordles_in_progress.add(ctx.channel.id)
  
  #check to avoid other channels, the bot's messages, commands, and non-same-length words
  def same_channel_not_bot_not_cmd(msg):
    guess_len = len(msg.content.strip()) == len(game.answer) or msg.content == prefix + quit_cmd
    same_channel = msg.channel.id == ctx.channel.id
    not_bot = not msg.author == bot.user
    not_cmd = True
    for command in bot.commands:
      if msg.content == prefix + command.name:
        not_cmd = False
        break
    return guess_len and same_channel and not_bot and not_cmd

  #initialize game
  game = w.Wordle(random.choice(w.WordSelector.answer_words_set))
  print(f"User {ctx.author} began a Wordle game in \"{ctx.guild}/{ctx.channel}\". The answer is {game.answer}.")

  #loop to run game board
  while game.curr_turn < game.turns:
    game_embed = discord.Embed(
      title = f"Wordle {game.curr_turn + 1}/6",
      description = game.hint_board_to_string() + "\n" + game.used_board_to_string(),
      color = discord.Color.blue()
    )
    await ctx.send(embed = game_embed)

    #loop for the answer
    while True:
      response = await bot.wait_for('message', check=same_channel_not_bot_not_cmd)
      guess = response.content

      #exit command
      if guess == prefix + quit_cmd:
        await ctx.send(f"Current Wordle game has ended. The word was ||**{game.answer}**||.")
        wordles_in_progress.remove(ctx.channel.id)
        return

      try:
        game.make_guess(guess)
        #game winning state
        if guess == game.answer:
          await ctx.send(f"Correct!! The word was **{game.answer}**. Number of attempts: {game.curr_turn}")
          wordles_in_progress.remove(ctx.channel.id)
          return
        break
      except Exception as err:
        await ctx.send(err)
      
      
      
      

  #game losing state
  await ctx.send(f"You lose. The word was **{game.answer}**")
  wordles_in_progress.remove(ctx.channel.id)

bot.run(TOKEN)
import discord
import asyncio
import random
import wordle as w
import resources
from discord.ext import commands

wordles_in_progress = set()
prefix = "~"

TOKEN = resources.TOKEN
  
#Initialize bot object and command prefix, delete default help command
bot = commands.Bot(command_prefix=prefix, help_command=None)

#Startup message
@bot.event
async def on_ready():
    print('Login as {0.user}'.format(bot))

@bot.command(name='help', brief='Returns a list of available commands for this bot.')
async def help(ctx):
  help_string = "**Available commands**:\n"
  for command in bot.commands:
    help_string += f"{prefix}{command.name} - {command.brief}\n"
  await ctx.send(help_string)


@bot.command(name='wordlemulti', brief='Plays a version of Wordle with multiplayer added.')
async def wordlemulti(ctx):
  global wordles_in_progress
  quit_cmd = "quit"

  if ctx.channel.id in wordles_in_progress:
    await ctx.send(f"A Wordle game is already in progress in this text channel. Please complete the game or end it with {prefix}{quit_cmd}.")
    return

  #Add it to wordles_in_progress
  wordles_in_progress.add(ctx.channel.id)

  #Set up a timer message to get the users reacting to the message.
  timer = 10
  react_msg = await ctx.send(f"React to this message to play Wordle Multiplayer. You have {timer} second(s) to join.")
  await react_msg.add_reaction("🔤")
  while timer >= 0:
    await react_msg.edit(content = f"React to this message to play Wordle Multiplayer. You have {timer} second(s) to join.")
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
  wins_needed = 2
  player_dict = {}
  for player in player_list:
    player_dict[player.id] = 0
  
  #Keeps track of round num
  num_rounds = 1

  print(f"User {ctx.author} began a Wordle Multiplayer game in \"{ctx.guild}/{ctx.channel}\".")
  #~~~~~~~~~~~~~~~~~~ROUND LOOP~~~~~~~~~~~~~~~~~~
  while True:  
    #Prints the scoreboard
    scoreboard = f"**Scoreboard** (first to {wins_needed} wins): "
    for counter, player in enumerate(player_set):
      scoreboard += f"{player.name}: {player_dict[player.id]} wins"
      if counter == len(player_list) - 1: break
      scoreboard += ", "
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
      await ctx.send(f"It's currently {player_list[curr_i].mention}'s turn. You have {play_timer} seconds, no countdown.")

      game_embed = discord.Embed(
        title = f"Wordle {game.curr_turn + 1}/6 - Round {num_rounds}",
        description = game.hint_board_to_string() + "\n" + game.used_board_to_string(),
        color = discord.Color.blue()
      )
      await ctx.send(embed = game_embed)

      user_has_not_played = True
      #~~~~~~~~~~~~~~~~~~WAITING FOR MESSAGE LOOP~~~~~~~~~~~~~~~~~~
      while user_has_not_played:

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
          user_has_not_played = False
        except Exception as err:
          await ctx.send(err)
          continue

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
  

@bot.command(name='wordle', brief='Plays a single Wordle game.')
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
        break
      except Exception as err:
        await ctx.send(err)
      

    #game winning state
    if guess == game.answer:
      await ctx.send(f"Correct!! The word was **{game.answer}**. Number of attempts: {game.curr_turn}")
      wordles_in_progress.remove(ctx.channel.id)
      return

  #game losing state
  await ctx.send(f"You lose. The word was **{game.answer}**")
  wordles_in_progress.remove(ctx.channel.id)


bot.run(TOKEN)


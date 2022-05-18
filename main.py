import os
import discord
import random
import resources
import re

from discord.ext import commands

wordleInProgress = False
wordleAttempt = -1
wordleLocation = ''
hintBoard = []
usedLetters = []
currentWord = ''

TOKEN = resources.TOKEN

allowedWordsFile = open("allowedwords.txt", "r")
allowedWordsList = allowedWordsFile.read()


def addRegionalIndicator(letter):
  return ":regional_indicator_" + letter + ":"

  
#Converts hints to correct string format
def hintsToString(hints):
    hintString = ""

    for i in range(len(hints)):
      if hints[i] == "_":
        hintString +="\\"
      
      hintString = hintString + hints[i] + " "
      
      if ((i-4) % 5 == 0):
        hintString += "\n"

    return hintString

#Converts used letters list to correct string format
def usedLettersToString(letters):
    lettersString = ""

    for i in range(len(letters)):
      currLetterCheck = re.sub(r'[^a-zA-Z]', '', letters[i]).lower()
      lettersString = lettersString + letters[i] + " "

    return lettersString


def generateBoard(wordleAttempt, hintBoard, usedLetters):
  boardEmbed = discord.Embed(
    title = "Wordle {0}/6".format(wordleAttempt),
    description = hintsToString(hintBoard) + "\n" + usedLettersToString(usedLetters),
    color = discord.Color.blue()
    )
  return boardEmbed

  
#Initialize bot object and command prefix
bot = commands.Bot(command_prefix='!')

#Startup message
@bot.event
async def on_ready():
    print('Login as {0.user}'.format(bot))


#Event to check all messages sent in the server
@bot.event
async def on_message(message):

  global wordleLocation
  global wordleInProgress
  global wordleAttempt
  global hintBoard
  global usedLetters
  global currentWord
  
  msg = message.content
  
  if message.author == bot.user:
    return

  #Moderates chat during Wordle game in progress
  if wordleInProgress and message.channel == wordleLocation:

    guess = msg.lower()
    #Several checks to prevent an invalid guess from being passed
    if not guess.isalpha():
      await message.channel.send("Guess must only contain English letters.")
    elif len(guess) != 5:
      await message.channel.send("Invalid length.")
    elif not (guess in allowedWordsList):
      await message.channel.send("Not in word list.")
    else:

      #Updates hint board based on current guess
      for i in range(5):
        if guess[i] == currentWord[i]:
          hintBoard[i + ((wordleAttempt-1)*5)] = currentWord[i].upper()
        elif guess[i] in currentWord:
            hintBoard[i + ((wordleAttempt-1)*5)] = guess[i].lower() 
        else:
          hintBoard[i + ((wordleAttempt-1)*5)] = "_"

        if not (guess[i] in usedLetters):
                usedLetters.append(guess[i])

      '''
      testmsg = ""
      for i in range(5):
        if hintBoard[i + ((wordleAttempt-1)*5)] == "_":
          testmsg += "\\"
        testmsg += hintBoard[i + ((wordleAttempt-1)*5)]

      await message.channel.send("Before: " + testmsg)
      '''
          
      #Does a second loop to fix "yellow" hints (right letter, wrong position)
      #This accounts for the yellow hint overlap issues
      for i in range(5):
        currLetter = guess[i]

        #Checks if the current hint is yellow
        if hintBoard[i + ((wordleAttempt-1)*5)].islower():
          
          
          correctLetterFreq = 0
          for j in range(5):
            #Ignore green hints when counting 
            if currentWord[j] == currLetter and not hintBoard[j + ((wordleAttempt-1)*5)].isupper():
              correctLetterFreq += 1

          
          #await message.channel.send("Letter: {a}\ncorrectLetterFreq: {b}".format(a = guess[i], b = correctLetterFreq))
          
          prevLetterFreq = 0
          for j in range(i+1):
            #Ignore green hints when counting 
            if guess[j] == currLetter and not hintBoard[j + ((wordleAttempt-1)*5)].isupper():
              prevLetterFreq += 1

          #await message.channel.send("prevLetterFreq: {}".format(prevLetterFreq))
         
          #If all prev yellow hints of this letter already match to a correct letter,
          #reset the hint back to empty
          if prevLetterFreq > correctLetterFreq:
            hintBoard[i + ((wordleAttempt-1)*5)] = "_"

        

      #Completes the game if the guess is correct
      if guess == currentWord:
        await message.channel.send("Correct!! The word was **{word}**. Number of attempts: {attempt}".format(word = currentWord, attempt = wordleAttempt))
        wordleInProgress = False
      else:
        
        wordleAttempt += 1

        #Breaks out of the game if the player goes over attempt limit
        if wordleAttempt >= 7:
          await message.channel.send("You lose. The word was **{}**".format(currentWord))
          wordleInProgress = False
        else:

          #Otherwise, reprint the game board again

          #embed.set_footer(text = hintsToString(usedLetters, False),  icon_url = embed.Empty)
          
          await message.channel.send(embed = generateBoard(wordleAttempt, hintBoard, usedLetters))



          
  #extra little feature
  if msg == "L":
    await message.channel.send('+ ratio')
    
  await bot.process_commands(message)



@bot.command()
async def quitwordle(ctx):
  global wordleLocation
  global wordleInProgress
  global currentWord

  if wordleInProgress:
    wordleInProgress = False
    await ctx.send("Current Wordle game has ended. The word was ||**{}**||.".format(currentWord))
  else: 
    await ctx.send("There is no Wordle game in progress. Begin one by typing !wordle.")
    


@bot.command()
async def wordle(ctx):

  global wordleLocation
  global wordleInProgress
  global wordleAttempt
  global hintBoard
  global usedLetters
  global currentWord
  
  if not wordleInProgress:
    
    wordleInProgress = True
    wordleLocation = ctx.channel
    wordleAttempt = 1
    
    hintBoard = []
    for i in range(30):
      hintBoard.append("_")

    '''
    usedLetters = ["~~Q~~", "W", "E", "R", "T", "Y", "U", "I", "O", "P",
                  "A", "S", "D", "F", "G", "H", "J", "K", "L",
                  "Z", "X", "C", "V", "B", "N", "M"]
    '''
    
    
    usedLetters = []
    

    with open("answers.txt", "r") as f:
      currentWord = random.choice(f.read().splitlines()).lower()


    #await ctx.send("The current word is {}".format(currentWord))

    
    
    await ctx.send(embed = generateBoard(wordleAttempt, hintBoard, usedLetters))
    
  else:
    await ctx.send("A Wordle game is already in progress.")

bot.run(TOKEN)
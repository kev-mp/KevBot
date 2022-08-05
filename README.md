# KevBot

A simple Discord bot written in Python utilizing the Pycord API. It offers several server management features, such as being able to blacklist words and timeout members unless they say a certain phrase. It also allows users to play Wordle in Discord, both alone and against other members.

## Getting Started

First, you need to install the required python libraries in order to get the bot working. After downloading the project package and exporting it to a folder, open the directory in the command prompt and run the line below. This will ensure that you have necessary dependencies to run the bot.

```
pip install -r requirements.txt
```

In order to use it with your own Discord bot, you need to replace the placeholder text in `resources.py` with the token of your bot. Navigate to the profile of your bot application in the Discord Developer Portal, and generate a token and copy it. Then, open the `resources.py` file and paste the token (make sure the token is in the quotation marks i.e. it's entered as a `string`).

```python
#Place your Discord Bot token below.
TOKEN = 'Your token here'
```

Finally, you need to initialize the `discord_database.db` file to store server data. To do so, run the `initdb.py` python file with `python initdb.py`. This should fill in the necessary data.

With that, your bot is ready to run! Just run `main.py` in your command prompt with `python main.py`. After a few seconds, a startup message should appear. To stop the bot, do Ctrl + C on the command prompt window, or just close it altogether.

## Commands

>Note: The default prefix for KevBot is '~'. The ability to change KevBot's command prefix will be added in the future.

### Non-Slash Commands

`help` - Displays all the non-slash commands for the bot.

`botowner` - Shows information about the owner of the bot.

`blacklist` - Shows all blacklisted words and phrases for the server. Messages with blacklisted words will automatically be deleted. Administrators can add words to the blacklist by appending the command with a plus sign (+) and as many words and phrases as necessary. For example, `~blacklist + blacklisted_word_1 blacklisted_word_2`. Likewise, administrators can delete them by using a minus sign (-) instead.

>Tip: If you want to add phrases to the blacklist, you just have to surround the phrase with quotation marks.

`randomtimeout` - Displays the percentage that users will be randomly timed out for in the current server. The default for every server is set to 0%. Administrators can change it using the same command and entering the percentage in the same message.

`wordle` - Starts up a Wordle game in the current text channel. Any user can join the instance of this game.

`wordlemulti` - Starts up a Wordle Multiplayer game in the current text channel, where players race each other to guess the word first. The default win condition is 2 rounds, but users can change it by adding the desired amount at the end of the command.

### Slash Commands

`bomb [member] [minutes] [phrase]` - An administrator-only command that prompts a selected `member` to say a certain `phrase` within a short duration. If the member fails to state this phrase in the given time, they will be timed out for a given number of `minutes`.

## Troubleshooting
It's important to note that this bot was designed using Python 3, so if something's not working, it might be because you're using an earlier Python version that may be incompatible.

If you encounter any other issues, let me know! You can reach out to me using the social media linked to my GitHub profile, or use the `botowner` command to obtain my Discord profile and message me there.
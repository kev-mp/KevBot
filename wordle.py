class WordSelector:
    #Initialize set for allowed word lookup in O(1) time
    allowed_words_set = set()
    with open("allowedwords.txt", "r") as file:
        for line in file:
            allowed_words_set.add(line.strip())

    answer_words_set = []
    with open("answers.txt", "r") as file:
        for line in file:
            answer_words_set.append(line.strip())
        
class Wordle:
    def __init__(self, answer, turns=6):
        self.in_progress = True
        self.win = False
        self.answer = answer
        self.length = len(answer)
        self.turns = turns
        self.curr_turn = 0
        self.hint_board = [[]] * turns
        self.used_board = {'q': -1, 'w': -1, 'e': -1, 'r': -1, 't': -1, 'y': -1, 'u': -1, 'i': -1, 'o': -1, 'p': -1,
        'a': -1, 's': -1, 'd': -1, 'f': -1, 'g': -1, 'h': -1, 'j': -1, 'k': -1, 'l': -1, 
        'z': -1, 'x': -1, 'c': -1, 'v': -1, 'b': -1, 'n': -1, 'm': -1 }

    def make_guess(self, guess):
        if not self.in_progress: raise Exception("Game already completed.")

        guess = guess.lower()
        if self.length != len(guess): raise ValueError("Invalid length of guess.")
        if not guess.isalpha(): raise ValueError("Guess must only contain English letters.")
        #If I wanna expand this for other word lengths then i gotta fix this check
        if guess not in WordSelector.allowed_words_set: raise ValueError("Guess must be a real word.")
        if self.curr_turn == self.turns: raise IndexError

        curr_board = []
        for i in range(self.length):
            if guess[i] == self.answer[i]:
                curr_board.append((self.answer[i], 2))
            elif guess[i] in self.answer:
                curr_board.append((guess[i], 1))
            else:
                curr_board.append((guess[i], 0))

        for i in range(self.length):
            curr_letter = guess[i]

            if curr_board[i][1] == 1:
                
                correct_letter_freq = 0
                for j in range(self.length):
                    if self.answer[j] == curr_letter and not curr_board[j][1] == 2:
                        correct_letter_freq += 1
                
                prev_letter_freq = 0
                for j in range (i + 1):
                    if guess[j] == curr_letter and not curr_board[j][1] == 2:
                        prev_letter_freq += 1
                
                if prev_letter_freq > correct_letter_freq:
                    curr_board[i] = (curr_board[i][0], 0)
        
        self.add_to_used(curr_board)

        self.hint_board[self.curr_turn] = curr_board    
        self.curr_turn += 1

        
    
    def add_to_used(self, board):
        for letter, val in board:
            if val > self.used_board[letter]: self.used_board[letter] = val
    
    def hint_board_to_string(self) -> str:
        res = ""
        for hint in self.hint_board:

            if hint == []:
                res += "\_ " * self.length
                res += "\n"
                continue
            
            for letter_tuple in hint:
                if letter_tuple[1] == 2:
                    res += "**" + letter_tuple[0].upper() + "**"
                elif letter_tuple[1] == 1:
                    res += letter_tuple[0]
                else: 
                    res += "\_"
                res += " "
            res += "\n"
        
        res = res.upper()
        return res
    
    def used_board_to_string(self):
        res = ""
        for letter, value in self.used_board.items():
            if value == -1:
                res += letter
            elif value == 0:
                res += "~~" + letter + "~~"
            elif value == 1:
                res += letter.upper()
            else: res += "**" + letter.upper() + "**"

            if letter == "p" or letter == "l": res += "\n"
            res += " "
        
        return res



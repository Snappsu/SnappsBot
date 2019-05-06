import random


print("Generating story...")

animals = ["Dog", "Cat", "Lizard", "Snake", "Fox"]
characters = []
STORY = ""
def newCharacter():
    print("Adding new character...")
    charAdded = False
    while charAdded == False:
        newChar = animals[random.randint(0,len(animals)-1)]
        print("Attempting to add " + newChar + "...")
        if newChar not in characters:
            characters.append(newChar)
            print("Added " + newChar + "!")
            charAdded = True
        else:
            print(newChar + "not added; already in cast!")

def listChoose(items):
    print("Choosing between " + str(items))
    temp = random.randint(0,len(items)-1)
    print ("Choose " + str(items[temp]))
    return items[temp]

def intro():
    print("Writing introduction...")
    global STORY 
    STORY = str((listChoose(["Once upon a time, ", "A long time ago, "])))
    temp = listChoose([1, 2, 3 ])
    if temp == 1:
        newCharacter()
        STORY += "there was a " + characters[0] + "."
    elif temp == 2:
        newCharacter()
        newCharacter()
        STORY += "there was a " + characters[0] + " and a " + characters[1] + "."
    elif temp == 3:
        newCharacter()
        newCharacter()
        newCharacter()
        STORY += "there was a " + characters[0] + ", a " + characters[1] + ", and a " + characters[2] + "."

def events

# Story starts here
intro()

print(STORY)
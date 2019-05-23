import io
import asyncio
import os
import time
import datetime
import re
import requests
import random
import readline
import csv
import urllib.request
import urllib3
import _thread

from PIL import Image
from slackclient import SlackClient
from multiprocessing import Process
from threading import Thread

# KEYS AND PASSWORDS
SlackBotKey = open("keys/SlackBotKey.txt", "r").read()
UnsplashBotKey = open("keys/UnsplashBotKey.txt", "r").read()
JiraBotKey = open("keys/JiraBotKey.txt", "r").read()
SplunkUsername = open("keys/SplunkUsername.txt", "r").read()
SplunkPassword = open("keys/SplunkPassword.txt", "r").read()

slack_client = SlackClient(SlackBotKey) # instantiate Slack client
SnappsBot_id = None # starterbot's user ID in Slack: value is assigned after the bot starts up

# Constants
RTM_READ_DELAY = 1 # 1 second delay between reading from RTM
EXAMPLE_COMMAND = "help"
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"
JIRA_PROJECT_LIST = [] 
if JIRA_PROJECT_LIST == []: # if the list is empty... 
    try: # try get list from Jira API
        S = requests.Session()
        URL = "https://jira.belkin.com/rest/api/2/project/"
        HEADER = {
                'Authorization':JiraBotKey,
                'Content-Type':"application/json", # request data as json
            }
        R = S.get(url=URL, headers=HEADER)
        DATA = R.json() # convert response to json format
        for ndx, member in enumerate(DATA): # for each project in the list... 
            JIRA_PROJECT_LIST.append(DATA[ndx]['key'].lower()) # add it to the project list
    except: # if it can't get to the API...
        print("Can't connect to Jira!")
print(JIRA_PROJECT_LIST) # for debugging

def getSplunkSession(): # gets an authorization key from Splunk
    print("Fetching session key...")
    try:  # try to reach the splunk login API
        S = requests.Session()
        URL = "https://belkin.splunkcloud.com:8089/services/auth/login/"
        HEADERS = {
        "Content-Type": "application/x-www-form-urlencoded", # send data as unencoded form
        }
        PAYLOAD = {
        'username':SplunkUsername,
        'password':SplunkPassword,
        }
        PARAMS = {
        'output_mode':"json", # get data as json
        }
        R = S.post(url=URL, params=PARAMS, data=PAYLOAD, headers=HEADERS, verify=False)
        DATA = R.json() # convert response to json format
        print("Session key fetched: "+DATA['sessionKey'])
        return DATA['sessionKey'] # return the auth ID
    except: # if it can't get to the API...
        print("Can't connect to Splunk; related commands disabled.")
        return "N/A"

def getCloudStatus(): 
    print("Fetching current cloud status...")
    try:  # try to reach the splunk login API
        S = requests.Session() # form a request to the Splunk API
        URL = "https://belkin.splunkcloud.com:8089/services/search/jobs/"
        HEADERS = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": "Splunk "+getSplunkSession(), # gets auth id
        }
        PAYLOAD = {
        'search':'| inputlookup cloudUnavailableMonitor.csv', # gets the bikeshare.csv from splunck
        }
        PARAMS = {
        'output_mode':"json", # ask for response to be a json
        }
        R = S.post(url=URL, params=PARAMS, data=PAYLOAD, headers=HEADERS, verify=False) # create the search via post
        # DATA will post the search and return the search id
        DATA = R.json() # convert the response to json
        try:
            S = requests.Session()
            URL = "https://belkin.splunkcloud.com:8089/services/search/jobs/"+str(DATA['sid']) # gets information search id
            HEADERS = {
            "Authorization": "Splunk "+getSplunkSession(), # gets auth id
            }
            PARAMS = {
            'output_mode':"json", # ask for response to be a json
            }
            R = S.get(url=URL, params=PARAMS, headers=HEADERS, verify=False) # gets information about the search
            # DATA2 will have the information about the search
            DATA2 = R.json() # convert the response to json
            while DATA2['entry'][0]['content']['dispatchState'] != "DONE": # while the search is not complete
                time.sleep(1) # wait 1 second
                R = S.get(url=URL, params=PARAMS, headers=HEADERS, verify=False) # check search status
                DATA2 = R.json() # convert the response to json
            try:
                S = requests.Session() 
                URL = "https://belkin.splunkcloud.com:8089/services/search/jobs/"+str(DATA['sid'])+"/results/"
                HEADERS = {
                "Authorization": "Splunk "+getSplunkSession(), # gets auth id
                }
                PARAMS = {
                'output_mode':"json", # ask for response to be a json
                }
                R = S.get(url=URL, params=PARAMS, headers=HEADERS, verify=False)
                DATA3 = R.json()
                print(DATA3)
                BLOCKS=[
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "Cloud Status Report!"
                            }
                        },
                        {
                            "type": "context",
                            "elements": [
                                {
                                    "type": "mrkdwn",
                                    "text": "*Status:* " + str(DATA3['results'][0]['alert3']) 
                                }
                            ]
                        },
                        {
                            "type": "context",
                            "elements": [
                                {
                                    "type": "mrkdwn",
                                    "text": "*Users:* " + str(DATA3['results'][0]['users']) 
                                }
                            ]
                        },
                        {
                            "type": "context",
                            "elements": [
                                {
                                    "type": "mrkdwn",
                                    "text": "*User errors:* " + str(DATA3['results'][0]['cloudErrorUsers']) 
                                }
                            ]
                        }
                    ]
                slack_client.api_call( # post all the results as a reply to the message
                "chat.postMessage",
                channel="CH0RMF9C6",
                blocks=BLOCKS
                )
                # DATA3 will post the search and return the search id
            except: # if it can't get to the API...
                print("Can't connect to Splunk; related commands disabled.")
                return "N/A"
        except: # if it can't get to the API...
            print("Can't connect to Splunk; related commands disabled.")
            return "N/A"
    except: # if it can't get to the API...
        print("Can't connect to Splunk; related commands disabled.")
        return "N/A"
    # time.sleep(1800) # wait 30 min

def dogFacts(): # gets a random line from 'dogFacts.txt'
    dogFacts = urllib.request.urlopen("https://raw.githubusercontent.com/Snappsu/SnappsBot/master/dogFacts.txt") # gets the list of dog facts (hosted on GitHub to get the most recent facts)
    lines = dogFacts.readlines() # gets each line of the file
    facts = [] # for holding the facts
    totalLines = 0 # for iteration and lenght finding
    for line in lines: # for each line in the file...
        facts.append(line.decode("utf-8").replace('\n', '')) # appends the line to the end of facts[]
        totalLines = totalLines + 1 # add one to total number of lines
    randomNum = random.randrange(0, totalLines) # picks a number from 0 to the total number of lines found
    return facts[randomNum] # returns a random fact as a string

def findJiraProject(text, channel): # finds Jira project in string. This should only be reading incoming messages from Slack
    # I feel like something in here is redundant, but it works as is
    try:
        if any(word in text.lower() for word in JIRA_PROJECT_LIST): # for each word in the message and if that word in the message is a Jira project
            print("JIRA Project spotted!")
            jiraProjectTargeted = False # for while loop
            while jiraProjectTargeted == False: # while jira project is not targeted...
                for member in JIRA_PROJECT_LIST: # for each project in the Jira project list...
                    if member in text.lower(): # if the project is in the message 
                        if member == "test": # if the project is 'test'
                            # ignore the the word
                            print("Project is " + member.upper() + ", ignoring.")
                            jiraProjectTargeted = True # end while loop
                        else: # otherwise...
                            print("Project is " + member.upper())
                            jiraProjectTargeted = True # end while loop
                            print("Word found at " + str(text.find(member)))
                            jiraIssues = re.findall("(\w+-\d+)", text) # get all the issues in the message (using regEx)
                            print(jiraIssues)
                if jiraIssues: # if Jira issure are found...
                    i = 0 # for iteration
                    while i < len(jiraIssues): # while not every issue is posted...
                        slack_client.api_call("chat.postMessage",channel=channel, text="Jira issue found! https://jira.belkin.com/browse/"+jiraIssues[i]) #print the issue
                        i += 1 # move on to the next one
    except: # if anything goes wrong...
        return None # return nothing

def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None, None.
    """

    for event in slack_events: # for every event that happens in slack...
        if event["type"] == "message" and not "subtype" in event: # if the event is a message event...
            user_id, message, ts = parse_direct_mention(event["text"]) # get message information via parse_direct_mention()
            if user_id == SnappsBot_id:  # if bot is mentioned ...
                print("I was mentioned by "+ event["user"] +" in channel " + event["channel"]) # for logging
                print("Full message: " + event["text"]) # For logging
                if event["text"] == ("<@"+user_id+">"): # if a user just mentions the bot...
                    slack_client.api_call("chat.postMessage",channel=event["channel"], text=WhatIsSnappsBot()) # post response of WhatIsSnappsBot() to channel
                else: 
                    return message, event["channel"], event["ts"] # contninue
            elif str(user_id) not in event["text"]: # if bot is not mentioned...
                findJiraProject(event["text"],event["channel"]) # search for Jira project in message
            elif event["text"] == "congrats" or event["text"] == "congratulations": # if the message only says "congrats" or another permutation...
                with open('partyDog.jpg', 'rb') as f: # get the partyDog.jpg image as read bytes
                    slack_client.api_call("files.upload", # uses slack's files.upload API to send the picture
                    channels=event["channel"],
                    filename='partyDog.jpg',
                    title='Party time!',
                    initial_comment='Good job!',
                    file=io.BytesIO(f.read())
                    )
                return None, None, None # don't send anything
    return None, None, None # don't send anything

def WhatIsSnappsBot():
    # This should return a small summary of what SnappsBot is
    return "Oh hey, that's me!" 

def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message, the third group contains the message thread (which is unused here)
    return (matches.group(1), matches.group(2).strip(), None) if matches else (None, None, None)

def handle_command(command, channel, ts):
    print("Command: " + command) # For logging
    """
        Executes bot command if the command is known
    """
    # Default response is help text for the user
    default_response = "I'm not sure what you mean... Try `help` and I'll try to help."

    # Finds and executes the given command, filling in response
    response = None

    # -=== Add Commands Here ===- 

    # Silly Commands
    if command.lower().startswith("do nothing"):
        response = "On it!"
    if command.lower().startswith("do something"):
        response = "I'll try my best!"
    if command.lower().startswith("sit"):
        response = "_sits_"
    if command.lower().startswith("speak"):
        response = dogFacts() # gets random dog fact from dogFacts
    if command.lower() ==  "take a selfie" or command.lower() ==  "selfie":
        slack_client.api_call("chat.postMessage",channel=channel, text="Give me a sec...")
        S = requests.Session()
        URL = "https://api.unsplash.com/photos/random"
        PARAMS = {
        'query':"dog",
        'count':"1",
        'client_id':UnsplashBotKey
        }
        R = S.get(url=URL, params=PARAMS)
        DATA = R.json()
        if DATA:
            S = requests.Session()
            URL = DATA[0]['links']['download_location'] # triggers download event for Unsplash
            PARAMS = {
            'client_id':UnsplashBotKey
            }
            R = S.get(url=URL, params=PARAMS)
            DATA2 = R.json()
            with urllib.request.urlopen(DATA2['url']) as url: # gets image from Unsplash's download URL
                with open('temp.jpg', 'wb') as f: 
                    f.write(url.read()) # writes image to temp.jpg
                    with open('temp.jpg', 'rb') as f: # gets temp.jpg
                        slack_client.api_call("files.upload", # uses slack's files.upload api
                        channels=channel,
                        filename='Cute Doggo.jpg',
                        file=io.BytesIO(f.read())
                        )
                        response = "This picture was by taken by "+ DATA[0]['user']['first_name'] + " " + DATA[0]['user']['last_name'] + " on Unsplash: " + DATA[0]['user']['links']['html'] + "\nDo you like it?"
        else:
            response = "Sorry, I'm not really feeling it at the moment."

    # Informative Commands
    if command.lower().startswith("help"):
        response = "Here's my resume: https://snappsu.github.io/SnappsBot/" # returns github website

        # Wikipedia Search
    if command.lower().startswith("tell me about yourself"):
        response = "Here's my resume: https://snappsu.github.io/SnappsBot/" # returns github website    
    elif command.lower().startswith("tell me about"):
        try:
            # Uses the wikipedia api to return the first search result of the query.
            S = requests.Session()
            URL = "https://en.wikipedia.org/w/api.php"
            SEARCHPAGE = command.lstrip(command[0:13]) # removes "tell me about" from the front of the command
            PARAMS = {
            'action':"query",
            'list':"search",
            'srsearch': SEARCHPAGE,
            'format':"json"
            }
            R = S.get(url=URL, params=PARAMS)
            DATA = R.json()
            if DATA:
                if DATA['query']['searchinfo']['totalhits'] != 0:
                    PAGEID = DATA['query']['search'][0]['pageid']
                    response = "Here's what I got: https://en.wikipedia.org/?curid="+str(PAGEID)+""
                else:
                    response = "I couldn't find anything, sorry! Try something more specific."
        except ValueError:
            response = "I couldn't find anything, sorry!"
    # Jira Commands
    if command.lower().startswith("jira"):
        temp = command.lstrip(command[0:5]) # removes "jira " from the front of the command
        # Get project key link command
        if temp.startswith("sum"): # if the next part of the command is "sum"...
            try:
                temp = temp.lstrip(temp[0:4]) # removes "sum " from the front of the command
                response = temp
                S = requests.Session() # forms a request to the Jira API
                URL = "https://jira.belkin.com/rest/api/2/issue/"+str(temp)+""
                HEADER = {
                'Authorization':JiraBotKey,
                'Content-Type':"application/json", 
                }
                R = S.get(url=URL, headers=HEADER) # sends GET request
                DATA = R.json() # converts response to json
                if 'priority' not in DATA['fields']: # if the priority tag is not found...
                    DATA['fields']['priority'] = None # add it
                if DATA['fields']['priority'] == None: # if the priority tag is empty...
                    DATA['fields']['priority']= {'name':"N/A"} # set it to "N/A"
                if DATA['fields']['assignee'] == None: # if the assignee tag is empty...
                    DATA['fields']['assignee']= {'name':"Unassigned",'emailAddress':'N/A'} # say it is unassigned
                if DATA:
                    slack_client.api_call( # post message to slack
                        "chat.postMessage",
                        channel=channel,
                        text="Here we go.",
                        blocks=[
                            {
                                "type": "section",
                                "text": { 
                                    "type": "mrkdwn",
                                    "text": "Here's a summary of "+DATA['key']+"." # gets the issue key
                                }
                            },
                            {
                                "type": "divider"
                            },
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": "*<https://jira.belkin.com/browse/"+DATA['key']+"|"+DATA['key']+">*\n"+DATA['fields']['summary']+"" # gets the issue url and name
                                }
                            },
                            {
                                "type": "section",
                                "fields": [
                                    {
                                        "type": "mrkdwn",
                                        "text": "*Status:*\n"+DATA['fields']['status']['name']+"" # gets the issue status
                                    },
                                    {
                                        "type": "mrkdwn",
                                        "text": "*Type:*\n"+DATA['fields']['issuetype']['name']+"" # gets the issue type
                                    },                                
                                    {
                                        "type": "mrkdwn",
                                        "text": "*Assignee:*\n"+DATA['fields']['assignee']['name']+" <mailto:"+DATA['fields']['assignee']['emailAddress']+"|[✉]>" # gets the issue assignee
                                    },
                                    {
                                        "type": "mrkdwn",
                                        "text": "*Reporter:*\n"+DATA['fields']['reporter']['name']+" <mailto:"+DATA['fields']['reporter']['emailAddress']+"|[✉]>" # gets the issue reported
                                    },                                    
                                    {
                                        "type": "mrkdwn",
                                        "text": "*Priority:*\n"+DATA['fields']['priority']['name']+"" # gets the issue priority
                                    },                                    
                                    {
                                        "type": "mrkdwn",
                                        "text": "*Component(s):*\n<"+DATA['fields']['components'][0]['self']+"|"+DATA['fields']['components'][0]['name']+">" # gets the issue components
                                    }
                                ]
                            },
                            {
                                "type": "divider"
                            },
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": "<https://jira.belkin.com/browse/"+DATA['key']+"|[Link to Issue]>" # gets the issue url again
                                }
                            }
                        ]
                    )
                    response = "I hope that helps!" # lets the user know the command is done
            except ValueError: # if the command couldn't be completed
                print ("Error with command, the issue probably wasn't found")
                response = "I couldn't find anything, sorry!" # lets the user know there was an error
        if temp.startswith("search"): # if the next part of the command is search...
            temp = command.lstrip(temp[0:6]) # removes "search " from the front of the temp
            terms = re.findall("([A-z]\w+\s*=\s*[A-z]\w+(?:\.\w+)*)", temp) # gets all the arguments from the message using regEx
            query = "" # blank query to fill
            i = 0 # for iteration
            for x in terms: # for each term...
                i += 1
                query += x # adds term to query
                if i < len(terms): # if i is less than to total number of terms...
                    query += " AND " # add "AND" to the query
                print(query) # for debugging
            query = query.replace(" ", "%20") # replace spaces with url friendly code
            query = query.replace("=", "%3D") # replace = with url friendly code
            S = requests.Session() # set up request for Jira search API
            URL = "https://jira.belkin.com/rest/api/2/search/?jql=" +query+ "&startAt=0&maxResults=10&fields=summary"
            HEADER = {
                'Authorization':JiraBotKey,
                'Content-Type':"application/json", 
            }
            R = S.get(url=URL, headers=HEADER)
            DATA = R.json()
            BLOCKS=[
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "I've searched through JIRA and these are what I found."
                            }
                        },
                        {
                            "type": "context",
                            "elements": [
                                {
                                    "type": "mrkdwn",
                                    "text": "*Total Results:* " + str(DATA['total']) + " | *Showing:* " + str(DATA['maxResults']) +"" # gets the total number of results found
                                }
                            ]
                        }
                    ]
            total = DATA['maxResults'] # total is how many issue blocks is posted
            if total > DATA['total']: # if total is less than total of issues found...
                total = DATA['total'] # make the total = the total results found
            for i in range(total): # for every number before the total
                BLOCKS.append({ # add a divider
                                "type": "divider"
                            })
                BLOCKS.append({ # add a search result
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": "<https://jira.belkin.com/browse/" + DATA['issues'][i]['key'] + "|" + DATA['issues'][i]['key'] + ">\n" + DATA['issues'][i]['fields']['summary']+"" # gets issue key and its url
                                }
                            })
            slack_client.api_call( # post all the results as a reply to the message
                "chat.postMessage",
                channel=channel,
                thread_ts =ts,
                text="Search complete!",
                blocks=BLOCKS
            )
            response = "Done! Check the replies." # lets the user know the bot is done
    # Debug Commands
    if command.lower().startswith("debug"):
            # Uptime command
        if "uptime" in command: # if uptime is found in the command
            response = "I've been up for about " + str(round(time.time() - startTime)) + " seconds!" # Subtracts current time by start time and prints it
    # Splunk Commands
    if command.lower().startswith("splunk"):
            # Uptime command
        if "search" in command: 
            try:
                S = requests.Session() # form a request to the Splunk API
                URL = "https://belkin.splunkcloud.com:8089/services/search/jobs/"
                HEADERS = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": "Splunk "+getSplunkSession(), # gets auth id
                }
                PAYLOAD = {
                'search':'| inputlookup bikeshare.csv', # gets the bikeshare.csv from splunck
                }
                PARAMS = {
                'output_mode':"json", # ask for response to be a json
                }
                R = S.post(url=URL, params=PARAMS, data=PAYLOAD, headers=HEADERS, verify=False) # create the search via post
                # DATA will post the search and return the search id
                DATA = R.json() # convert the response to json
                try:
                    maxResult = 5
                    page = 1
                    S = requests.Session()
                    URL = "https://belkin.splunkcloud.com:8089/services/search/jobs/"+str(DATA['sid']) # gets information search id
                    HEADERS = {
                    "Authorization": "Splunk "+getSplunkSession(), # gets auth id
                    }
                    PARAMS = {
                    'output_mode':"json", # ask for response to be a json
                    }
                    R = S.get(url=URL, params=PARAMS, headers=HEADERS, verify=False) # gets information about the search
                    # DATA2 will have the information about the search
                    DATA2 = R.json() # convert the response to json
                    while DATA2['entry'][0]['content']['dispatchState'] != "DONE": # while the search is not complete
                        time.sleep(1) # wait 1 second
                        R = S.get(url=URL, params=PARAMS, headers=HEADERS, verify=False) # check search status
                        DATA2 = R.json() # convert the response to json
                    try:
                        S = requests.Session() 
                        URL = "https://belkin.splunkcloud.com:8089/services/search/jobs/"+str(DATA['sid'])+"/results/"
                        HEADERS = {
                        "Authorization": "Splunk "+getSplunkSession(), # gets auth id
                        }
                        PARAMS = {
                        'output_mode':"json", # ask for response to be a json
                        }
                        R = S.get(url=URL, params=PARAMS, headers=HEADERS, verify=False)
                        DATA3 = R.json()
                        # DATA3 will post the search and return the search id
                        BLOCKS =[
                            {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "Here's what I got from Splunk!\n<https://belkin.splunkcloud.com/en-US/app/search/search?sid="+DATA['sid']+">"
                                }
                            },
                            {
                            "type": "context",
                            "elements": [
                                {
                                "type": "mrkdwn",
                                "text": "*Total hits:* "+str(DATA2['entry'][0]['content']['resultCount'])+" | *Page:* "+ str(page) +" ("+str((page-1)*maxResult+1)+"-"+str(maxResult * page)+")"
                                }
                                ]
                            }
                        ]
                        
                        for i in range(maxResult):
                            BLOCKS.append({
                                "type": "divider"
                            })
                            BLOCKS.append({
                                'type': "section",
                                'fields': [
                                    {
                                    'type': "mrkdwn",
                                    'text': "*Bike ID:* "+str(DATA3['results'][i]['bike_id'])
                                    }
                                ]})
                            BLOCKS.append({
                                'type': "section",
                                'fields': [
                                    {
                                    'type': "mrkdwn",
                                    'text': "*Member Type:* "+str(DATA3['results'][i]['member_type'])
                                    },
                                    {
                                    'type': "mrkdwn",
                                    'text': "*Start Station:* "+str(DATA3['results'][i]['start_station'])
                                    },
                                    {
                                    'type': "mrkdwn",
                                    'text': "*Date:* "+str(DATA3['results'][i]['date_wday'])+" at "+str(DATA3['results'][i]['date_hour'])+"00"
                                    },
                                    {
                                    'type': "mrkdwn",
                                    'text': "*Duration:* "+str(DATA3['results'][i]['duration_ms'])+"ms"
                                    }                                 
                                ]})
                            BLOCKS.append({
                                "type": "context",
                                "elements": [
                                    {
                                    "type": "plain_text",
                                    "emoji": True,
                                    "text": "⏱ Timestamp: "+str(DATA3["results"][i]["timestamp"])+""
                                    }
                                ]}) 
                        try:
                            slack_client.api_call(
                            "chat.postMessage",
                            channel= channel,
                            thread_ts = ts,
                            text="Search complete!",
                            blocks=BLOCKS
                            )
                            response = "Splunk search created: check the thread."
                        except:
                            response = "Posting failed :<"
                    except:
                        response = "Search failed :<"
                except:
                    print("No response from Splunk.")
                    response = "No response from Splunk. :<"
            except:
                print("Can't connect to Splunk.")
                response = "Can't connect to Splunk. :<"
            
    
    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response or default_response,
        unfurl_media = "true",
    )

# Async Testing
CloudeUpdateQueue = 0
def periodic(x):
    while True:
        getCloudStatus()
        time.sleep(x)

    return None

def getCommand():
    command, channel, ts = parse_bot_commands(slack_client.rtm_read())
    if command:
        handle_command(command, channel, ts)
    time.sleep(RTM_READ_DELAY)
    return None

def start_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

new_loop = asyncio.new_event_loop()
t = Thread(target=start_loop, args=(new_loop,))
t.start()    

# Start of Program


startTime = time.time()
if __name__ == "__main__": 
    if slack_client.rtm_connect(with_team_state=False): # checks if bot connects to slack
        print("SnappsBot connected and running!")
        # Read bot's user ID by calling Web API method `auth.test`
        SnappsBot_id = slack_client.api_call("auth.test")["user_id"]
        new_loop.call_soon_threadsafe(periodic, 3000)

        while True:
            getCommand()
    else:
        print("Connection failed. Exception traceback printed above.")
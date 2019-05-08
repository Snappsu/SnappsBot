import io
import os
import time
import re
import requests
import random
import readline
import urllib.request
import urllib3
from PIL import Image
from slackclient import SlackClient

# instantiate Slack client
SlackBotKey = open("keys/SlackBotKey.txt", "r").read()
UnsplashBotKey = open("keys/UnsplashBotKey.txt", "r").read()
JiraBotKey = open("keys/JiraBotKey.txt", "r").read()
SplunkUsername = open("keys/SplunkUsername.txt", "r").read()
SplunkPassword = open("keys/SplunkPassword.txt", "r").read()
slack_client = SlackClient(SlackBotKey)
# starterbot's user ID in Slack: value is assigned after the bot starts up
SnappsBot_id = None

# constants
RTM_READ_DELAY = 1 # 1 second delay between reading from RTM
EXAMPLE_COMMAND = "help"
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"
JIRA_PROJECT_LIST = []
if JIRA_PROJECT_LIST == []:
    try:
        S = requests.Session()
        URL = "https://jira.belkin.com/rest/api/2/project/"
        HEADER = {
        }
        R = S.get(url=URL, headers=HEADER)
        DATA = R.json()
        for ndx, member in enumerate(DATA):
            JIRA_PROJECT_LIST.append(DATA[ndx]['key'].lower())
    except:
        print("Can't connect to Jira; related commands disabled.")
print(JIRA_PROJECT_LIST) 

def getSplunkSession():
    print("Fetching session key...")
    try:
        S = requests.Session()
        URL = "https://belkin.splunkcloud.com:8089/services/auth/login/"
        HEADERS = {
        "Content-Type": "application/x-www-form-urlencoded",
        }
        PAYLOAD = {
        'username':SplunkUsername,
        'password':SplunkPassword,
        }
        PARAMS = {
        'output_mode':"json",
        }
        R = S.post(url=URL, params=PARAMS, data=PAYLOAD, headers=HEADERS, verify=False)
        DATA = R.json()
        print("Session key fetched: "+DATA['sessionKey'])
        return DATA['sessionKey']
    except:
        print("Can't connect to Splunk; related commands disabled.")
        return "N/A"

def dogFacts():
    dogFacts = urllib.request.urlopen("https://raw.githubusercontent.com/Snappsu/SnappsBot/master/dogFacts.txt") # A list of dog facts
    lines = dogFacts.readlines() #gets each line of the file
    facts = []
    totalLines = 0
    for line in lines:     
        facts.append(line.decode("utf-8").replace('\n', '')) #appends each line to the end of facts[]
        totalLines = totalLines + 1 #adds total number of lines
    randomNum = random.randrange(0, totalLines) #creates a range from 0 to the total number of lines
    return facts[randomNum] #returns a random fact as a string

def findJiraProject(text, channel):
    if any(word in text.lower() for word in JIRA_PROJECT_LIST): 
        print("JIRA Project spotted!")
        jiraProjectTargeted = False
        while jiraProjectTargeted == False:
            for member in JIRA_PROJECT_LIST:
                if member in text.lower():
                    if member == "test":
                        print("Project is " + member.upper() + ", ignoring.")
                        jiraProjectTargeted = True
                    else:    
                        print("Project is " + member.upper())
                        jiraProjectTargeted = True
                        print("Word found at " + str(text.find(member)))
                        jiraIssues = re.findall("(\w+-\d+)", text)
                        print(jiraIssues)
            if jiraIssues:
                i = 0
                while i < len(jiraIssues):
                    slack_client.api_call("chat.postMessage",channel=channel, text="Jira issue found! https://jira.belkin.com/browse/"+jiraIssues[i])
                    i += 1 

    return None
def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """

    for event in slack_events:
        print(event)
        if event["type"] == "message" and not "subtype" in event:
            # if bot is mentioned 
            user_id, message, ts = parse_direct_mention(event["text"])
            if user_id == SnappsBot_id:
                print("I was mentioned by "+ event["user"] +" in channel " + event["channel"]) # for logging
                print("Full message: " + event["text"]) # For logging
                if event["text"] == ("<@"+user_id+">"):
                    slack_client.api_call("chat.postMessage",channel=event["channel"], text=WhatIsSnappsBot())
                else:
                    return message, event["channel"], event["ts"]
            elif str(user_id) not in event["text"]: 
                #search for Jira Project
                findJiraProject(event["text"],event["channel"])
            # if congrats is said
            elif event["text"] == "congrats" or event["text"] == "congratulations": # in the event that a message is sent and it say "congrats"
                with open('partyDog.jpg', 'rb') as f:
                    slack_client.api_call("files.upload", # uses slack's files.upload api
                    channels=event["channel"],
                    filename='partyDog.jpg',
                    title='Party time!',
                    initial_comment='Good job!',
                    file=io.BytesIO(f.read())
                    )
                return None, None, None
    return None, None, None

def WhatIsSnappsBot():
    return "Oh hey, that's me!"

def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
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
        # Help Commands
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
        if temp.startswith("sum"): 
            try:
                temp = temp.lstrip(temp[0:4]) # removes "sum " from the front of the command
                response = temp
                S = requests.Session()
                URL = "https://jira.belkin.com/rest/api/2/issue/"+str(temp)+""
                HEADER = {
                'Authorization':JiraBotKey,
                'Content-Type':"application/json", 
                }
                R = S.get(url=URL, headers=HEADER)
                DATA = R.json()
                if 'priority' not in DATA['fields']:
                    DATA['fields']['priority'] = None
                if DATA['fields']['priority'] == None:
                    DATA['fields']['priority']= {'name':"N/A"}
                if DATA['fields']['assignee'] == None:
                    DATA['fields']['assignee']= {'name':"Unassigned",'emailAddress':'N/A'}
                if DATA:
                    slack_client.api_call(
                        "chat.postMessage",
                        channel=channel,
                        text="Here we go.",
                        blocks=[
                            {
                                "type": "section",
                                "text": { 
                                    "type": "mrkdwn",
                                    "text": "Here's a summary of "+DATA['key']+"."
                                }
                            },
                            {
                                "type": "divider"
                            },
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": "*<https://jira.belkin.com/browse/"+DATA['key']+"|"+DATA['key']+">*\n"+DATA['fields']['summary']+""
                                }
                            },
                            {
                                "type": "section",
                                "fields": [
                                    {
                                        "type": "mrkdwn",
                                        "text": "*Status:*\n"+DATA['fields']['status']['name']+""
                                    },
                                    {
                                        "type": "mrkdwn",
                                        "text": "*Type:*\n"+DATA['fields']['issuetype']['name']+""
                                    },                                
                                    {
                                        "type": "mrkdwn",
                                        "text": "*Assignee:*\n"+DATA['fields']['assignee']['name']+" <mailto:"+DATA['fields']['assignee']['emailAddress']+"|[✉]>"
                                    },
                                    {
                                        "type": "mrkdwn",
                                        "text": "*Reporter:*\n"+DATA['fields']['reporter']['name']+" <mailto:"+DATA['fields']['reporter']['emailAddress']+"|[✉]>"
                                    },                                    
                                    {
                                        "type": "mrkdwn",
                                        "text": "*Priority:*\n"+DATA['fields']['priority']['name']+""
                                    },                                    
                                    {
                                        "type": "mrkdwn",
                                        "text": "*Component(s):*\n<"+DATA['fields']['components'][0]['self']+"|"+DATA['fields']['components'][0]['name']+">"
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
                                    "text": "<https://jira.belkin.com/browse/"+DATA['key']+"|[Link to Issue]>"
                                }
                            }
                        ]
                    )
                    response = "I hope that helps!"
            except ValueError:
                print ("Error with command, the issue probably wasn't found")
                response = "I couldn't find anything, sorry!"
        if temp.startswith("search"):
            temp = command.lstrip(temp[0:6]) # removes "search " from the front of the temp
            terms = re.findall("([A-z]\w+\s*=\s*[A-z]\w+(?:\.\w+)*)", temp)
            query = ""
            i = 0
            for x in terms:
                i += 1
                query += x
                if i < len(terms):
                    query += " AND "
                print(query)
            query = query.replace(" ", "%20")
            query = query.replace("=", "%3D")
            S = requests.Session()
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
                                    "text": "*Total Results:* " + str(DATA['total']) + " | *Showing:* " + str(DATA['maxResults']) +""
                                }
                            ]
                        }
                    ]
            total = DATA['maxResults']
            if total > DATA['total']:
                total = DATA['total']
            for i in range(total):
                BLOCKS.append({
                                "type": "divider"
                            })
                BLOCKS.append({
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": "<https://jira.belkin.com/browse/" + DATA['issues'][i]['key'] + "|" + DATA['issues'][i]['key'] + ">\n" + DATA['issues'][i]['fields']['summary']+""
                                }
                            })
            slack_client.api_call(
                "chat.postMessage",
                channel=channel,
                thread_ts =ts,
                text="Search complete!",
                blocks=BLOCKS
            )
            response = "Done! Check the replies."
    # Debug Commands
    if command.lower().startswith("debug"):
            # Uptime command
        if "uptime" in command: 
            response = "I've been up for about " + str(round(time.time() - startTime)) + " seconds!" # Subtracts current time by start time.
    
    # Splunk Commands
    if command.lower().startswith("splunk"):
            # Uptime command
        if "search" in command: 
            try:
                S = requests.Session()
                URL = "https://belkin.splunkcloud.com:8089/services/search/jobs/"
                HEADERS = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": "Splunk "+getSplunkSession(),
                }
                PAYLOAD = {
                'search':'search index=mint sourcetype="mint:event" earliest=-30m@m',
                }
                PARAMS = {
                'output_mode':"json",
                }
                R = S.post(url=URL, params=PARAMS, data=PAYLOAD, headers=HEADERS, verify=False)
                DATA = R.json()
                print(DATA)
                print(DATA['sid'])
                try:
                    S = requests.Session()
                    URL = "https://belkin.splunkcloud.com:8089/services/search/jobs/"+str(DATA['sid'])
                    HEADERS = {
                    "Authorization": "Splunk "+getSplunkSession(),
                    }
                    PARAMS = {
                    'output_mode':"json",
                    }

                    R = S.get(url=URL, params=PARAMS, headers=HEADERS, verify=False)
                    DATA2 = R.json()
                    while DATA2['entry'][0]['content']['dispatchState'] != "DONE":
                        time.sleep(.5)
                        R = S.get(url=URL, params=PARAMS, headers=HEADERS, verify=False)
                        DATA2 = R.json()
                    print(DATA2)
                    BLOCKS =[
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "*Total hits:* "+str(DATA2['entry'][0]['content']['resultCount'])
                            }
                        }]
                    slack_client.api_call(
                        "chat.postMessage",
                        channel= channel,
                        thread_ts = ts,
                        text="Search complete!",
                        blocks=BLOCKS
                    )
                    response = "Splunk search created: check the thread."
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

startTime = time.time()

if __name__ == "__main__": 
    if slack_client.rtm_connect(with_team_state=False): # checks if bot connects to slack
        print("SnappsBot connected and running!")
        # Read bot's user ID by calling Web API method `auth.test`
        SnappsBot_id = slack_client.api_call("auth.test")["user_id"]
        while True: # while true loop, keeps bot running
            command, channel, ts = parse_bot_commands(slack_client.rtm_read())
            if command:
                handle_command(command, channel, ts)
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")
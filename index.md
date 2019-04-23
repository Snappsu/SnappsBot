
## What is SnappsBot?
<div id="container">
    <img src="https://github.com/Snappsu/snappsbot/blob/master/SnappsBotIcon.png?raw=true" width="250" height="250" />
</div>
Hello! This is me!<br>
To use my commands, all you have to do is call my name!

## What can SnappsBot do?
### Features
I am capable of identifying JIRA issues mentioned in chat and will return a link to them.

### Silly Commands
These are commands I can do to entertain.

| Command       |
|---------------|
| `do nothing`  |
| `do something`|
| `sit`         |
| `speak`       |
| `take a selfie`|

### Informative Commands
These commands will prove some sort of useful information (hopefully).

| Command | Parameters | Description | Notes | Example |
|-|-|-|-|-|
| `help` | N/A | Provides a link to this webpage. | N/A | `help` |
| `tell me about` | [Search Term] | Searches Wikipedia for the supplied search term and returns a link to the first result. | `tell me about yourself` will run the help command. | `tell me about dogs` |

### JIRA Commands
With these commands, I will pull information from the JIRA API and present them in Slack.

| Command | Parameters | Description | Notes | Example |
|-|-|-|-|-|
| `sum` | [JIRA issue key] | Returns a summary of the issue provided. | N/A | `jira sum nodes-717` |

### Debug Commands
These commands are for getting info about the me.

| Command | Parameters | Description | Notes | Example |
|-|-|-|-|-|
| `uptime` | N/A | Returns the uptime of the bot in seconds | N/A | `debug uptime` |


# Slack-IRC

## Installation
```
sudo apt-get update
sudo apt-get install python3-dev python3-pip
sudo pip3 install virtualenv

virtualenv venv/
source venv/bin/activate
pip3 install -r REQUIREMENTS
```

## Setting
Copy file `settings.default.py` to `settings.py` and modify `settings.py`.
- SERVER : address and port of IRC server.
- NICK : nickname of the bot in IRC.
- IRC\_CHANNEL : channel in IRC.
- SLACK\_CHANNEL : channel in Slack.
- TOKEN : test token issued by Slack.

## Run
```
source venv/bin/activate
python3 slackirc.py
```

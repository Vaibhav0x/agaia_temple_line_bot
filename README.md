# Agaia Temple Flow

This is flow for the Agaia Temple 3 day flow

## Setup
Create line bussiness account and in messaging api create and get the channel secret and create channel access token

## Agaia Temple Flow Project Setup

```bash
git clone https://github.com/Vaibhav0x/agaia_temple_line_bot.git
cd agaia_temple_line_bot
```
### Environment
create `.env` file into you project root directory

```bash
CHANNEL_SECRET=channel_secret_key
CHANNEL_ACCESS_TOKEN=channel_access_token
```

Add you secret credentials here.

### Installation
Create virtual environment for the python 3.9 preferable
```bash
py -3.9 -m venv venv

#Activate venv

.venv\Scripts\activate  #windows

source venv/bin/activate   #linux
```

Install dependencies for the project

```bash
pip install -r requirements.txt
```

### Run the Project

```bash
python app.py
```

### Run ngrok for the local project flow check
```bash
ngrok http 5000
```

Add ngrok url 
Eg: https://ngrok.........ig.io
into the webhook url:
Eg: https://ngrok........ig.io/callback

Now verify from your Line account after adding the webhook on line messaging api.

## BOss now your project ready just send the message of the main account owner and get the response.

Developed by vaibhav raj


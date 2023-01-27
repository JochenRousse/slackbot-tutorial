import os
import schedule
import time
import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import pandas as pd
import urllib.parse
from datetime import datetime

logging.basicConfig(level=logging.DEBUG)


def nearest(items, pivot):
    return min(item for item in items if item[0] > pivot)


def get_user_from_gsheet():
    SHEET_ID = ''
    SHEET_NAME = 'Planning de passage'

    url_safe = urllib.parse.quote_plus(SHEET_NAME)
    url = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={url_safe}'
    df = pd.read_csv(url)
    df = df.reset_index()

    datetimes = []
    for index, row in df.iterrows():
        datetimes.append([datetime.strptime(row['Date'], '%d/%m/%Y'), index])

    nextrex = nearest(datetimes, datetime.now())
    return df.iloc[[nextrex[1]]]['Membre #1'].to_string(header=False, index=False)


def get_user_id(slack_client, channel, next_for_rex):
    channel_list = slack_client.conversations_list()['channels']
    channel = list(filter(lambda c: c['name'] == channel, channel_list))[0]

    response = slack_client.conversations_members(channel=channel['id'])
    user_ids = response["members"]

    users_data = slack_client.users_list()

    userid = ""

    if users_data['ok']:
        users_list = users_data['members']

        users = filter(lambda u: u['id'] in user_ids, users_list)

        for user in users:
            if user['real_name'].upper() == next_for_rex.upper():
                userid = user['id']
    else:
        print("Rate limited")

    return userid


def send_message(slack_client, msg):
    try:
        slack_client.chat_postMessage(
            channel='#test-chat-bot',
            text=msg
        )
    except SlackApiError as e:
        logging.error('Request to Slack API Failed: {}.'.format(e.response.status_code))
        logging.error(e.response)


if __name__ == "__main__":
    CHANNEL_NAME = 'test-chat-bot'
    SLACK_BOT_TOKEN = ""
    slack_client = WebClient(SLACK_BOT_TOKEN)
    logging.debug("authorized slack client")

    next_for_rex = get_user_from_gsheet()
    user_id = get_user_id(slack_client, CHANNEL_NAME, next_for_rex)

    msg = "Cette semaine, <@" + user_id + "> aura le plaisir de nous présenter son rex !"
    schedule.every(3).seconds.do(lambda: send_message(slack_client, msg))

    # schedule.every().monday.at("09:00").do(lambda: sendMessage(slack_client, msg))
    logging.info("entering loop")

    while True:
        schedule.run_pending()
        time.sleep(5)

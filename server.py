import os
import json
import logging
import pandas as pd
import urllib.parse
from datetime import datetime

from flask import Flask, request, make_response, Response

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.signature import SignatureVerifier

from slashCommand import Slash

logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)


def get_next_rex_date_from_gsheet(person):
    SHEET_ID = ''
    SHEET_NAME = 'Planning de passage'

    url_safe = urllib.parse.quote_plus(SHEET_NAME)
    url = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={url_safe}'
    df = pd.read_csv(url)
    df = df.reset_index()

    rows = df.loc[df['Membre #1'].str.upper() == person.upper()]

    if rows.empty:
        return None
    else:
        date = rows.iloc[-1]['Date']
        if datetime.strptime(date, '%d/%m/%Y') > datetime.now():
            return date
        else:
            return None


@app.route("/slack/t-rex", methods=["POST"])
def command():
    if not verifier.is_valid_request(request.get_data(), request.headers):
        return make_response("invalid request", 403)
    info = request.form

    try:
        result = slack_client.users_info(user=info["user_id"])
    except SlackApiError as e:
        logging.error("Error fetching conversations: {}".format(e))

    date = get_next_rex_date_from_gsheet(result['user']['real_name'])

    if date is None:
        commander = Slash("Ton prochain REX n'a pas encore été planifié")
    else:
        commander = Slash("Ton prochain REX est prévu pour le " + date)

    logging.info(commander.getMessage())

    try:
        im_id = slack_client.conversations_open(users=info["user_id"])["channel"]["id"]
        response = slack_client.chat_postMessage(
            channel=im_id,
            text=commander.getMessage()
        )
    except SlackApiError as e:
        logging.error('Request to Slack API Failed: {}.'.format(e.response.status_code))
        logging.error(e.response)
        return make_response("", e.response.status_code)

    return make_response("", 200)


# Start the Flask server
if __name__ == "__main__":
    SLACK_BOT_TOKEN = ""
    SLACK_SIGNATURE = "e9fc03ec158b1f79675e49a8c29a7518"
    slack_client = WebClient(SLACK_BOT_TOKEN)
    verifier = SignatureVerifier(SLACK_SIGNATURE)

    app.run()

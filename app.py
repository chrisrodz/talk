# ---------------
# Imports
# ---------------

from __future__ import with_statement   # Only necessary for Python 2.5
import os
import json
from flask import Flask, request, redirect
from twilio.rest import TwilioRestClient
import twilio.twiml
from urllib import quote_plus
import requests

# ---------------
# Init
# ---------------
app = Flask(__name__)
 
callers = {
    "+17875663317": "Christian",
    "+17879413774": "X",
    "+17874629666": "Abimael"
}

lang1 = "es"
lang2 = "en"
caller1 = ""
caller2 = ""
text1 = ""
text2 = ""
yandex_key = os.environ.get('YANDEX_API_KEY', '')

# ---------------
# Helpers
# ---------------

def translate_text(phrase, from_lang='en', dest_lang='es'):
  url = "https://translate.yandex.net/api/v1.5/tr.json/translate?key=%s&lang=%s-%s&text=%s" % (yandex_key, from_lang, dest_lang, quote_plus(phrase))
  translation = requests.get(url)
  return json.loads(translation.content)['text'][0]

def call_number(number):
  account = os.environ.get('TWILIO_SID', '')
  token = os.environ.get('TWILIO_TOKEN', '')
  twilio_number = os.environ.get('TWILIO_NUMBER', '')
  ngrok_url = os.environ.get('TWILIO_NGROK', '')
  client = TwilioRestClient(account, token)

  call = client.calls.create(to = number,
                            from_ = twilio_number,
                            url = ngrok_url + "/new")
  return call.sid
 
# ---------------
# Routes
# ---------------

@app.route("/", methods=['GET', 'POST'])
def hello():
    from_number = request.values.get('From', None)
    if from_number in callers:
        caller = callers[from_number]
    else:
        caller = "Monkey"
 
    resp = twilio.twiml.Response()
    # Greet the caller by name
    resp.say("Hello " + caller)
 
    # Gather digits.
    with resp.gather(numDigits=10, action="/handle-key", method="POST") as g:
        g.say("""Enter a new number to call with the other twilio number.""")
 
    return str(resp)

@app.route('/new', methods=['GET', 'POST'])
def new():
  resp = twilio.twiml.Response()
  resp.say("Hello, my love. You are awesome.")
  return str(resp)

@app.route('/say', methods=['GET', 'POST'])
def say():
  resp = twilio.twiml.Response()
  callid = request.values.get('CallSid', '')
  global text1
  global text2

  if caller1 == callid and text1 != "":
    if lang1 != lang2:
      text1 = translate_text(text1, lang2, lang1)
    resp.say(text1, language=lang1)
    text1 = ""
  elif caller2 == callid and text2 != "":
    if lang1 != lang2:
      text2 = translate_text(text1, lang1, lang2)
    resp.say(text2, language=lang2)
    text2 = ""
  else:
    resp.redirect(url="/wait")
  return str(resp)

@app.route('/wait', methods=['GET', 'POST'])
def wait():
  print "wait"
  return "wait"

@app.route('/record', methods=['GET', 'POST'])
def record():
  print "record"
  return "record"


### Tutorial methods
@app.route("/handle-key", methods=['GET', 'POST'])
def handle_key():
    """Handle key press from a user."""
 
    digit_pressed = request.values.get('Digits', None)
    resp = twilio.twiml.Response()
    resp.say("Calling " + digit_pressed)

    called_res = call_number(digit_pressed)
    resp.say("Call id is " + called_res)

    return str(resp)

    # if digit_pressed == "1":
    #     resp = twilio.twiml.Response()
    #     # Dial (310) 555-1212 - connect that number to the incoming caller.
    #     resp.dial("+13105551212")
    #     # If the dial fails:
    #     resp.say("The call failed, or the remote party hung up. Goodbye.")
 
    #     return str(resp)
 
    # elif digit_pressed == "2":
    #     resp = twilio.twiml.Response()
    #     resp.say("Record your monkey howl after the tone.")
    #     resp.record(maxLength="5", action="/handle-recording", transcribe="true", transcribeCallback="/handle-transcribed", timeout="2")
    #     return str(resp)
 
    # # If the caller pressed anything but 1, redirect them to the homepage.
    # else:
    #     return redirect("/")

@app.route("/handle-recording", methods=['GET', 'POST'])
def handle_recording():
    """Play back the caller's recording."""
 
    recording_url = request.values.get("RecordingUrl", None)
    print recording_url
    resp = twilio.twiml.Response()
    resp.say("Goodbye.")
    return str(resp)

@app.route("/handle-transcribed", methods=['GET', 'POST'])
def handle_transcribed():
  """Print the transcribed text and say it back to the user"""
  text = request.values.get('TranscriptionText')
  print text
  return str(text)

 
if __name__ == "__main__":
    app.run(debug=True)
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

lang1 = "en"
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
                            url = ngrok_url + "/call")
  return call.sid
 
# ---------------
# Routes
# ---------------

@app.route("/", methods=['GET', 'POST'])
def hello():
    print request.values
    global caller1
    caller1 = request.values.get('CallSid', None)
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

@app.route('/say', methods=['GET', 'POST'])
def say():
  resp = twilio.twiml.Response()
  callid = request.values.get('CallSid', None)
  global text1
  global text2

  if caller1 == callid:
    if text1:
      # if lang1 != lang2:
      #   text1 = translate_text(text1, lang2, lang1)
      resp.say(text1, language=lang1)
      text1 = ""
  elif caller2 == callid:
    if text2:
      # if lang1 != lang2:
      #   text2 = translate_text(text1, lang1, lang2)
      resp.say(text2, language=lang2)
      text2 = ""

  resp.redirect("/wait")
  return str(resp)

@app.route('/wait', methods=['GET', 'POST'])
def wait():
  resp = twilio.twiml.Response()
  resp.say('Hello')
  if (request.values.get('CallSid', None) == caller1):
    # if text empty -> /say
    if text1 != "": 
      resp.redirect('/say')
    # <gather> -> record 
    elif text1 == "":
      with resp.gather(numDigits=1, action="/record", method="POST", timeout=5) as g:
        g.say("""Press one to start your message.""")
      resp.redirect('/wait')
  elif(request.values.get('CallSid', None) == caller2):
    if text2 != "":
      print "Nos fuimos pa say"
      resp.redirect('/say')
    # <gather> -> record 
    elif text2 == "":
      with resp.gather(numDigits="1", action="/record", method="POST", timeout="5") as g:
        g.say("""Press one to start your message.""")    
      resp.redirect('/wait')
  print "wait"
  return str(resp)

@app.route('/record', methods=['GET', 'POST'])
def record():
  print "record"
  digit_pressed = request.values.get('Digits', None)
  resp = twilio.twiml.Response()
  if digit_pressed == "1":
    caller = request.values.get('CallSid', None)

    resp.say("Say you message after the tone.")

    # record
    resp.record(timeout="2" , action="/wait")

    if(caller == caller1):
      print "Caller 1 metiendole"
      handle_transcribed("1")

    elif(caller == caller2):
      print "Caller 2 charriando"
      handle_transcribed("2")

    return str(resp)

  # if caller din't pressed anithing redirect 
  else:
    print "Nadie hablo. Estan charriando"
    resp.redirect('/wait')
    return str(resp)

@app.route('/call', methods=['GET', 'POST'])
def call():
  resp = twilio.twiml.Response()
  global caller2
  caller2 = request.values.get('CallSid', None)
  resp.redirect('/wait')
  return str(resp)

@app.route("/handle-key", methods=['GET', 'POST'])
def handle_key():
    """Handle key press from a user."""
 
    digit_pressed = request.values.get('Digits', None)
    resp = twilio.twiml.Response()
    resp.say("Calling new number.")

    called_res = call_number(digit_pressed)
    resp.redirect('/wait')
    return str(resp)


@app.route("/handle-transcribed", methods=['GET', 'POST'])
def handle_transcribed(caller):
  """Print the transcribed text and say it back to the user"""
  print "Handle transcribeeeeo"
  if caller == "1":
    global text2
    text2 = "Caller 1 spoke"

  elif caller == "2":
    global text1
    text1 = "Caller 1 spoke"

if __name__ == "__main__":
    app.run(debug=True)
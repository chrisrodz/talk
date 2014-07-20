# -*- coding: utf-8 -*-

# ---------------
# Imports
# ---------------

from __future__ import with_statement, unicode_literals   # Only necessary for Python 2.5
import os
import json
from flask import Flask, request, redirect
from twilio.rest import TwilioRestClient
import twilio.twiml
from twilio.util import TwilioCapability
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

lang1 = ""
lang2 = ""
caller1 = ""
caller2 = ""
text1 = list()
text2 = list()
yandex_key = os.environ.get('YANDEX_API_KEY', '')
att_key = os.environ.get('ATT_KEY', '')

account = os.environ.get('TWILIO_SID', '')
token   = os.environ.get('TWILIO_TOKEN', '')
client  = TwilioRestClient(account, token)

# ---------------
# Helpers
# ---------------

def speech_to_text(speech_url, lang=None):
  data = requests.get(speech_url)
  headers = {
    "Authorization": "Bearer " + att_key,
    "Content-Length": data.headers['content-length'],
    "Content-Type": "audio/x-wav",
    "X-SpeechContext": "Generic",
    "Connection": "keep-alive",
  }
  if lang == 'es':
    headers["Content-Language"] = "es-US"
  text = requests.post("https://api.att.com/speech/v3/speechToText", headers=headers, data=data.content)
  print text.content
  att_data = json.loads(text.content)
  try:
    return json.loads(text.content)[u'Recognition'][u'NBest'][0][u'ResultText']
  except KeyError:
    return "Error"

def translate_text(phrase, from_lang='en', dest_lang='es'):
  url = "https://translate.yandex.net/api/v1.5/tr.json/translate?key=%s&lang=%s-%s&text=%s" % (yandex_key, from_lang, dest_lang, quote_plus(phrase.encode('utf8')))
  translation = requests.get(url)
  return json.loads(translation.content)['text'][0]

def call_number(number):
  global client
  twilio_number = os.environ.get('TWILIO_NUMBER', '')
  call = client.calls.create(to = number,
                            from_ = twilio_number,
                            url = "http://langutalk.herokuapp.com/call")
  return call.sid
 
# ---------------
# Routes
# ---------------

@app.route("/", methods=['GET', 'POST'])
def hello():
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
    with resp.gather(numDigits=1, action="/setlang", method="POST") as g:
      g.say("For English, press one.")
      g.say('Para Español, presione dos', language='es')
 
    return str(resp)

@app.route("/setlang", methods=['GET', 'POST'])
def setlang():
  resp = twilio.twiml.Response()
  callid = request.values.get('CallSid', None)
  digit_pressed = request.values.get('Digits', None)

  if callid == caller1:
    global lang1
    if digit_pressed == "1":
      lang1 = "en"
      message = "Enter a new number to call with the other twilio number."
    elif digit_pressed == "2":
      lang1 = "es"
      message = "Ingrese un número telefónico para llamar."
    with resp.gather(numDigits=10, action="/handle-key", method="POST") as g:
      g.say(message, language=lang1)

  elif callid == caller2:
    global lang2
    if digit_pressed == "1":
      lang2 = "en"
      message = "Press one anytime to respond with a message"
    elif digit_pressed == "2":
      lang2 = "es"
      message = "Presione uno en cualquier momento para responder con un mensaje."
    resp.say(message, language=lang2)

  resp.redirect('/wait')
  return str(resp)

@app.route('/say', methods=['GET', 'POST'])
def say():
  resp = twilio.twiml.Response()
  callid = request.values.get('CallSid', None)
  global text1
  global text2

  if caller1 == callid:
    if len(text1) > 0:
      if lang1 != lang2:
        text = translate_text(text1.pop(0), lang2, lang1)
      resp.say(text, language=lang1)
  elif caller2 == callid:
    if len(text2) > 0:
      if lang1 != lang2:
        text = translate_text(text2.pop(0), lang1, lang2)
      resp.say(text, language=lang2)

  resp.redirect("/wait")
  return str(resp)

@app.route('/wait', methods=['GET', 'POST'])
def wait():
  resp = twilio.twiml.Response()
  sid = request.values.get('CallSid', None)
  print text1
  print text2
  if sid == caller1:
    if len(text1) != 0: 
      resp.redirect('/say')
    elif len(text1) == 0:
      resp.gather(numDigits="1", action="/record", method="POST", timeout="5")
  elif sid == caller2:
    if len(text2) != 0:
      resp.redirect('/say')
    elif len(text2) == 0:
      resp.gather(numDigits="1", action="/record", method="POST", timeout="5")
  resp.redirect('/wait')
  return str(resp)

@app.route('/record', methods=['GET', 'POST'])
def record():
  digit_pressed = request.values.get('Digits', None)
  resp = twilio.twiml.Response()
  if digit_pressed == "1":
    caller = request.values.get('CallSid', None)

    # record
    resp.record(timeout="2" , action="/transcribe", maxLength="3")

    return str(resp)

  # if caller din't pressed anithing redirect 
  else:
    resp.redirect('/wait')
    return str(resp)

@app.route('/transcribe', methods=['GET', 'POST'])
def transcribe():
  resp = twilio.twiml.Response()
  recording = request.values.get('RecordingUrl', None)

  callid = request.values.get('CallSid', None)
  if callid == caller1:
    transcribed = speech_to_text(recording, lang1)
    global text2
    text2.append(transcribed)

    if lang1 == 'en':
      message = "Message has been sent"
    elif lang1 == 'es':
      message = "El mensaje se ha enviado"
    resp.say(message, language=lang1)

  elif callid == caller2:
    transcribed = speech_to_text(recording, lang2)
    global text1
    text1.append(transcribed)

    if lang2 == 'en':
      message = "Message has been sent"
    elif lang2 == 'es':
      message = "El mensaje se ha enviado"
    resp.say(message, language=lang2)

  resp.redirect('/wait')
  return str(resp)

@app.route('/call', methods=['GET', 'POST'])
def call():
  resp = twilio.twiml.Response()
  with resp.gather(numDigits=1, action="/setlang", method="POST") as g:
    g.say("For English, press one.")
    g.say('Para Español, presione dos', language='es')
  return str(resp)

@app.route("/handle-key", methods=['GET', 'POST'])
def handle_key():
    digit_pressed = request.values.get('Digits', None)
    resp = twilio.twiml.Response()
    called_res = call_number(digit_pressed)
    if lang1 == 'en':
      message1 = "Calling new number"
      message2 = "Press one anytime to respond with a message"
    elif lang1 == 'es':
      message1 = "Llamando el número nuevo"
      message2 = "Presione uno en cualquier momento para responder con un mensaje"

    resp.say(message1, language=lang1)
    resp.pause(length="5")
    resp.say(message2, language=lang1)
    global caller2
    caller2 = called_res
    resp.redirect('/wait')
    return str(resp)

@app.route('/capability', methods=['GET', 'POST'])
def capability():
  global token
  global account
  capability = TwilioCapability(account, token)
  capability.allow_client_outgoing("APe4454b16035e7e581dd3a0863d7ea465")
  token = capability.generate()
  print token
  return str(token)

if __name__ == '__main__':
  app.run(debug=True)

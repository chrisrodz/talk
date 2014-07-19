from __future__ import with_statement   # Only necessary for Python 2.5

import os
from flask import Flask, request, redirect

from twilio.rest import TwilioRestClient
import twilio.twiml
 
app = Flask(__name__)
 
callers = {
    "+17875663317": "Christian",
    "+17879413774": "X"
}

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
 
@app.route("/", methods=['GET', 'POST'])
def hello_monkey():
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
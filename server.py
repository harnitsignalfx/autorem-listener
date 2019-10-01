from flask import Flask, request
import json
import requests
import os
import writeFile
import sys
import signalfx



app = Flask(__name__)

if 'SF_TOKEN' in os.environ:
    print (os.environ['SF_TOKEN'])
else:
    print ('SF_TOKEN env variable not found')
    sys.exit(0)

filepath = '/arlogs/userlist'

realm = 'us0'

if 'REALM' in os.environ:
    realm = os.environ['REALM']

endpoint = 'https://ingest.'+realm+'.signalfx.com'

token = os.environ['SF_TOKEN']

sfx = signalfx.SignalFx(ingest_endpoint=endpoint).ingest(token)


@app.route('/healthz')
def health():
    sfx.send(
        counters=[
          {
            'metric': 'autorem-listener.heartbeat',
            'value': 1
          }])
    return "OK"



@app.route('/health', methods=['POST'])
def healthCheck():
    '''Sends dummy event'''
    
    sfx.send_event(
        event_type='Health Check',
        properties={
            'status': 'OK'})

    return "OK"

@app.route('/health/<string:username>', methods=['POST'])
def healthCheckWithUser(username):
    
    #headers = {'X-SF-TOKEN' : os.environ['SF_TOKEN'],'Content-Type' : 'application/json'}
    headers = {'X-SF-TOKEN' : token,'Content-Type' : 'application/json'}
    print('Received Health Check for - ',username)


    sfx.send_event(
        event_type='Health Check',
        properties={
            'status': 'OK',
            'user': username})

    return "OK" 

@app.route('/write', methods=['POST'])
def write():
    
    data = json.loads(request.data.decode('utf-8'))
    if ('messageBody' in data) and ('status' in data):
      if not (data['status'].lower()=='anomalous'):  
        # ..Do nothing.. the alert is back to normal
        return "OK"

      if not data['messageBody']:
        print('Empty message Body, returning..')
        return "OK"  
        
      body = data['messageBody'].split(" ")
      if 'Rollback' == body[1]:
        username = body[3]
        writeFile.modifyFile(filepath,username,'rollback')

        sfx.send_event(
        event_type='Automated Rollback initiated',
        properties={
            'user': username})

      elif 'Deployment' == body[1]:
        username = body[3]
        writeFile.modifyFile(filepath,username,'deploy')

        sfx.send_event(
        event_type='Automated Deployment initiated',
        properties={
            'user': username})
    
    return "OK"

@app.route('/write/<string:username>/<int:batchsize>', methods=['POST'])
def writeSize(username,batchsize):
    
    print('Received - ',username,' ',batchsize)
    if batchsize > 30000:
      writeFile.modifyFile(filepath,username,'bcanary')
    else:
      writeFile.modifyFile(filepath,username,'gcanary')

    sfx.send_event(
        event_type='canary push event',
        properties={
            'user': username})

    return "OK"    



if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=6000)
    finally:
        sfx.stop()

import requests
import os
import json
import tempfile
import time

"""

The Fofum class encapsulates feefie events. It can be used to create events,
listen on events fire events.

"""

PHANTOM_PATH = '/bin/phantomjs'
FEEFIE_SERVER_URL = "http://www.feefie.com/command"
#FEEFIE_SERVER_URL = "http://feefie980522.appspot.com/command"

CHANNEL_JS="""
        var page = require('webpage').create();
        page.open('%s?action=subscribe&hash=%s&html=1',function() {
        loopfn = function() {
            var title = page.evaluate(function () {
                return eCount+'###'+payload.data;
            });
            console.log(title);
            setTimeout(loopfn,1000);
        };
        setTimeout(loopfn,1000);
        });
        
"""

class FofumException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)
        

class Fofum:
    _client_id=''
    def run_action(self, action, hash='', message='',title=''):
        event = json.dumps({'title':title})
        params = {'action':action,'hash':hash,'payload':message,'u':self.user,'event':event,'client_id'=_client_id}
        return requests.get(FEEFIE_SERVER_URL, params=params)

    def make(self, title):
        ret_string = self.run_action('add',title=title)
        try:
            ret_dict = json.loads(ret_string.text)
            if (ret_dict['status']!=0):
                raise FofumException('Error creating event. Server error.')
            else:
                try:
                    self.hash = ret_dict['hash']
                except KeyError:
                    raise FofumException('Error creating event. Did not get event spec.')
        except:
            raise FofumException('Error creating event. Malformed response: %s'%ret_string.text)

    def subscribe(self):
        ret_string = self.run_action('subscribe', hash=self.hash)
        try:
            ret_dict = json.loads(ret_string.text)
            if (ret_dict['status']!=0):
                raise FofumException('Error creating event. Server error.')
            else:
                try:
                    self.token = ret_dict['token']
                    _client_id = ret_dict['client_id']
                except KeyError:
                    raise FofumException('Error fetching token. Did not get token spec')
        except:
            raise FofumException('Error subscribing to event. Malformed response %s'%ret_string.text)

    def fire(self, payload='""'):
        self.run_action('fire',hash=self.hash,message=payload)

    def listen(self):
        channel_js = CHANNEL_JS%(FEEFIE_SERVER_URL, self.hash)
        f = tempfile.NamedTemporaryFile('w')
        f.write(channel_js)
        f.flush()
        cmdline = '%s %s'%(PHANTOM_PATH, f.name)
        conn = os.popen(cmdline)
        self.series = 0
        
        while True:
            msg = conn.readline()
            if ('###' in msg):
                status,payload = msg.split('###')
                status = int(status)
                if (status>self.series):
                    self.series = status
                    if (self.callback):
                        self.callback(payload)
                elif (status<0):
                    break
        # Returns when connection breaks. Caller needs to resubscribe, relisten
        return    

    # This method creates/looks up an event, subscribes to it, listens and reconnects if necessary.
    def listen_for_event(self, event_name, callback):
        self.callback = callback
        hash = self.make(event_name)

        stamp = time.time() 
        while (True):
            self.subscribe()
            self.listen()
            interval = time.time() - stamp
            if (interval < 5.0):
                # Too fast, wait
                time.sleep(5.0 - interval)
                

    def __init__(self,user='',hash=None,client_id=''):
        _client_id = client_id
        # Check phantomjs dependency
        if (not os.access(PHANTOM_PATH,0)):
            raise FofumException('Phantomjs not installed.')
        self.user = user



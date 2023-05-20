import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer


class CallConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        # Response to client that we are connected
        self.send(text_data=json.dumps({
            'type': 'connection',
            'data': {
                'message': "Connected"
            }
        }))

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.my_name,
            self.channel_name
        )

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        rtc_type = text_data_json['type']

        if rtc_type == 'login':
            name = text_data_json['data']['name']
            # we will use this as room name as well
            self.my_name = name

            async_to_sync(self.channel_layer.group_add)(
                self.my_name,
                self.channel_name
            )

        elif rtc_type == 'call':
            name = text_data_json['data']['name']
            print(self.my_name, "is calling", name)
            # notify the callee we sent an event to the group name
            # their ground name is the name
            async_to_sync(self.channel_layer.group_send)(
                name, {
                    'type': 'call_received',
                    'data': {
                        'caller': self.my_name,
                        'rtcMessage': text_data_json['data']['rtcMessage']
                    }
                }
            )

        elif rtc_type == 'answer_call':
            # receive call from someone now notify the calling user
            # we can notify to the group with the caller name
            caller = text_data_json['data']['caller']

            async_to_sync(self.channel_layer.group_send)(
                caller, {
                    'type': 'call_answered',
                    'data': {
                        'rtcMessage': text_data_json['data']['rtcMessage']
                    }
                }
            )

        elif rtc_type == 'stop_call':
            otheruser = text_data_json['data']['name']

            async_to_sync(self.channel_layer.group_send)(
                otheruser, {
                    'type': 'call_stopped',
                    'data': {
                        'rtcMessage': text_data_json['data']['rtcMessage']
                    }
                }
            )

        elif rtc_type == 'ICEcandidate':
            user = text_data_json['data']['user']

            async_to_sync(self.channel_layer.group_send)(
                user, {
                    'type': 'ICEcandidate',
                    'data': {
                        'rtcMessage': text_data_json['data']['rtcMessage']
                    }
                }
            )


    def call_received(self, event):
        print('Call received by ', self.my_name)
        self.send(text_data=json.dumps({
            'type': 'call_received',
            'data': event['data']
        }))

    def call_answered(self, event):
        print(self.my_name, "'s call answered")
        self.send(text_data=json.dumps({
            'type': 'call_answered',
            'data': event['data']
        }))

    def call_stopped(self, event):
        print(self.my_name, "'s call stopped")
        self.send(text_data=json.dumps({
            'type': 'call_stopped',
            'data': event['data']
        }))


    def ICEcandidate(self, event):
        self.send(text_data=json.dumps({
            'type': 'ICEcandidate',
            'data': event['data']
        }))



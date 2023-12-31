import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer


class CallConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        self.send(text_data=json.dumps({
            'type': 'connection',
            'data': {
                'message': "Connected"
            }
        }))

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.my_name,
            self.channel_name
        )

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        rtc_type = text_data_json['type']

        if rtc_type == 'login':
            name = text_data_json['data']['name']
            self.my_name = name

            async_to_sync(self.channel_layer.group_add)(
                self.my_name,
                self.channel_name
            )

        elif rtc_type == 'call':
            name = text_data_json['data']['name']
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
            other_user = text_data_json['data']['name']

            async_to_sync(self.channel_layer.group_send)(
                other_user, {
                    'type': 'call_stopped',
                    'data': {
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
        self.send(text_data=json.dumps({
            'type': 'call_received',
            'data': event['data']
        }))

    def call_answered(self, event):
        self.send(text_data=json.dumps({
            'type': 'call_answered',
            'data': event['data']
        }))

    def call_stopped(self, event):
        self.send(text_data=json.dumps({
            'type': 'call_stopped',
            'data': event['data']
        }))

    def ICEcandidate(self, event):
        self.send(text_data=json.dumps({
            'type': 'ICEcandidate',
            'data': event['data']
        }))

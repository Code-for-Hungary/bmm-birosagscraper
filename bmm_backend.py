import requests
import logging


class BmmBackend:

    def __init__(self, backend_url, generator_id) -> None:

        if backend_url.endswith('/'):
            self.backendURL = backend_url[:-1]
        else:
            self.backendURL = backend_url

        self.generatorID = generator_id

    def get_events(self, api_key):

        try:
            response = requests.get(f"{self.backendURL}/api/events/bygenerator/{self.generatorID}?api_key={api_key}")
            response = response.json()
            return response
        except Exception as e:
            logging.exception('Az eseményeket nem tudom lekérdezni a backendtől.')
            raise e

    def notify_event(self, event_uuid, content, api_key):

        notification_data = {
            'uuid': self.generatorID,
            'eventUuid': event_uuid,
            'content': content
        }
        try:
            response = requests.post(f"{self.backendURL}/api/events/notify/{event_uuid}?api_key={api_key}", data=notification_data)
            return response
        except Exception as e:
            logging.exception('A backend értesítése nem sikerült.')
            raise e

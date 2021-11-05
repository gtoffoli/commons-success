
from django.apps import AppConfig
import commons

class SuccessConfig(AppConfig):
    name = 'success'

    def ready(self):
        import commons.signal_handlers

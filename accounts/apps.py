from django.apps import AppConfig

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        pass  # Remove or comment out the signals import if you don't need it
        # import accounts.signals  # Uncomment this if you create the signals.py file later
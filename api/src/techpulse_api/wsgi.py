"""WSGI entry point pour gunicorn en production.

Commande : gunicorn techpulse_api.wsgi:app
"""

from techpulse_api.app import create_app

app = create_app()

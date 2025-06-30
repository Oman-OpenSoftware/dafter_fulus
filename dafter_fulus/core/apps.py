"""
Django app configuration for Money Tracker.
"""

from django.apps import AppConfig


class MoneyTrackerAppConfig(AppConfig):
    """Configuration for the Money Tracker app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'money_tracker_app'
    verbose_name = 'Money Tracker'
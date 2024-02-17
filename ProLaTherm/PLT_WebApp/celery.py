from __future__ import absolute_import
import os
from celery import Celery
from django.conf import settings
from celery.schedules import crontab


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PLT_WebApp.settings')

app = Celery('PLT_WebApp')

app.conf.update(timezone = 'Europe/Berlin')

app.conf.beat_schedule = {
    'delete-old-requests-everday-at-3am': {
        'task': 'WebApp.tasks.delete_old_user_requests',
        'schedule': crontab(hour=3, minute=00),
    }
    
}

app.autodiscover_tasks()


app.config_from_object('django.conf:settings')


app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

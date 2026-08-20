#!/usr/bin/env bash
set -o errexit
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py shell -c "
import os
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

site, _ = Site.objects.get_or_create(id=1, defaults={'domain': 'buildai.acoderm.uz', 'name': 'BuildAI'})
if site.domain != 'buildai.acoderm.uz':
    site.domain = 'buildai.acoderm.uz'
    site.name = 'BuildAI'
    site.save()

if not SocialApp.objects.filter(provider='google').exists():
    app = SocialApp.objects.create(provider='google', name='Google', client_id=os.environ.get('GOOGLE_CLIENT_ID',''), secret=os.environ.get('GOOGLE_CLIENT_SECRET',''))
    app.sites.add(site)
print('Done')
"

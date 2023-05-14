import datetime
import json
import os
from django.conf import settings
from django.forms import ValidationError
import environ
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from allauth.socialaccount.models import SocialToken
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
import requests

environ.Env.read_env()
env = environ.Env()

def  homepage(request):
    if request.user.is_authenticated:
        access_token = SocialToken.objects.get(
            account__user=request.user,
            account__provider='google',
            token=request.user.social_auth.get(provider='google-oauth2').extra_data['access_token']
        )
        credentials = Credentials.from_authorized_user_info(access_token=access_token)
        request.session['google_auth'] = credentials.to_authorized_user_info()
        return render(request=request, template_name='home.html',)
    else: 
        return redirect('account_login')

def  create_event_page(request):
    if request.user.is_authenticated:
        return  render(request=request, template_name= 'create_event.html',)
    else: 
        return redirect('account_login')

@csrf_exempt
def create_event(request):
    if request.method == 'POST':
        attendee_email = request.POST.get('attendee_email')
        attendee_name = request.POST.get('attendee_name')
        start_time = datetime.datetime.strptime(request.POST.get('start_time'), '%Y-%m-%dT%H:%M')
        end_time = datetime.datetime.strptime(request.POST.get('end_time'), '%Y-%m-%dT%H:%M')

        google_auth = request.session.get('google_auth')
        api_key = env('GOOGLE_API_KEY')

        if google_auth and api_key:            
            credentials = Credentials.from_authorized_user_info(google_auth)
            service = build('calendar', 'v3', credentials=credentials, developerKey=api_key)

        event = {
            'summary': 'Meeting with {}'.format(attendee_name),
            'location': 'Virtual',
            'description': 'Meeting with {} at {}.'.format(attendee_name, start_time.strftime('%m/%d/%Y %I:%M %p')),
            'start': {
                'dateTime': start_time.strftime('%Y-%m-%dT%H:%M:%S'),
                'timeZone': 'America/Los_Angeles',
            },
            'end': {
                'dateTime': end_time.strftime('%Y-%m-%dT%H:%M:%S'),
                'timeZone': 'America/Los_Angeles',
            },
            'attendees': [
                {'email': attendee_email},
            ],
            'reminders': {
                'useDefault': True,
            },
        }
        event = service.events().insert(calendarId='primary', body=event).execute()
        
        # Create Google Meeting
        conference_request = {
            'requestId': 'random-id',
            'conferenceSolutionKey': {
                'type': 'hangoutsMeet'
            },
            'status': {
                'statusCode': 'success'
            }
        }
        conference = service.events().createConference(calendarId='primary', eventId=event['id'], body=conference_request).execute()
        conference_id = conference['conferenceData']['entryPoints'][0]['uri']
        
        # Return JSON response with Google Meeting link
        response_data = {'google_meeting_link': conference_id}
        return JsonResponse(response_data, status=200)
    else:
        return JsonResponse({'error': 'Invalid request method.'}, status=405)

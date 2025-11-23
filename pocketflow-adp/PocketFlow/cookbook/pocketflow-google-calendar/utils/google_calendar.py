from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os.path
import os
import pickle
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

CALENDAR_ID = os.getenv('GOOGLE_CALENDAR_ID')
GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
TIMEZONE = os.getenv('TIMEZONE')

SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service():
    """Gets the authenticated Google Calendar service."""
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                GOOGLE_APPLICATION_CREDENTIALS, SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('calendar', 'v3', credentials=creds)

def create_event(summary, description, start_time, end_time, timezone=TIMEZONE):
    """Creates a new event in Google Calendar."""
    service = get_calendar_service()
    
    event = {
        'summary': summary,
        'description': description,
        'start': {
            'dateTime': start_time.isoformat(),
            'timeZone': timezone,
        },
        'end': {
            'dateTime': end_time.isoformat(),
            'timeZone': timezone,
        },
    }

    event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
    return event

def list_events(days=7):
    """Lists events for the next X days."""
    service = get_calendar_service()
    
    now = datetime.utcnow()
    time_min = now.isoformat() + 'Z'
    time_max = (now + timedelta(days=days)).isoformat() + 'Z'

    events_result = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    return events_result.get('items', [])

def create_custom_calendar(calendar_name, description=""):
    """Creates a new custom calendar in Google Calendar."""
    service = get_calendar_service()
    
    calendar = {
        'summary': calendar_name,
        'description': description,
        'timeZone': TIMEZONE
    }

    created_calendar = service.calendars().insert(body=calendar).execute()
    return created_calendar

def list_calendar_lists():
    """Lists all available calendars for the user."""
    service = get_calendar_service()
    
    calendar_list = service.calendarList().list().execute()
    return calendar_list.get('items', []) 
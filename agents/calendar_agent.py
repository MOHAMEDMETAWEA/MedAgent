"""
Google Calendar Scheduling Agent.
Handles secure OAuth2 scheduling with date parsing and availability checks.
"""
import os.path
import datetime
import dateparser
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from .state import AgentState
from config import settings
import logging

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/calendar']

class CalendarAgent:
    """
    Manages Google Calendar appointments.
    """
    def __init__(self):
        self.creds = None
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Google Calendar API using OAuth2."""
        try:
            if settings.CALENDAR_TOKEN_FILE.exists():
                self.creds = Credentials.from_authorized_user_file(str(settings.CALENDAR_TOKEN_FILE), SCOPES)
            
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    if settings.CALENDAR_CREDENTIALS_FILE.exists():
                        flow = InstalledAppFlow.from_client_secrets_file(
                            str(settings.CALENDAR_CREDENTIALS_FILE), SCOPES)
                        self.creds = flow.run_local_server(port=0)
                    else:
                        logger.warning("Calendar credentials.json not found. Calendar features disabled.")
                        return

                # Save the credentials for the next run
                with open(settings.CALENDAR_TOKEN_FILE, 'w') as token:
                    token.write(self.creds.to_json())

            self.service = build('calendar', 'v3', credentials=self.creds)
            logger.info("Calendar API authenticated successfully.")

        except Exception as e:
            logger.error(f"Calendar authentication failed: {e}")
            self.service = None

    def process(self, state: AgentState):
        print("--- CALENDAR AGENT: SCHEDULING ---")
        user_input = state.get('messages', [])[-1].content
        patient_info = state.get('patient_info', {})
        urgency = patient_info.get('urgency', 'LOW')

        # Safety Check: Do not schedule if Emergency
        if urgency == 'EMERGENCY':
            return {
                "final_response": "I cannot schedule an appointment because this appears to be a medical emergency. Please call emergency services immediately.",
                "next_step": "end"
            }

        if not self.service:
            return {
                "final_response": "Calendar scheduling is currently unavailable (authentication failed). Please contact support.",
                "next_step": "end"
            }

        # Simplified Parsing (In production, use an LLM extraction step)
        # Extract date/time from user_input
        dt = dateparser.parse(user_input, settings={'PREFER_DATES_FROM': 'future'})
        
        if not dt:
             return {
                "final_response": "I couldn't understand the date and time. Please specify exactly when you'd like the appointment (e.g., 'tomorrow at 3pm').",
                "next_step": "end"
            }
        
        # Check if in past
        if dt < datetime.datetime.now():
             return {
                "final_response": "I cannot schedule appointments in the past. Please choose a future time.",
                "next_step": "end"
            }

        try:
            # Check availability (Occupied?)
            time_min = dt.isoformat() + 'Z'
            time_max = (dt + datetime.timedelta(minutes=30)).isoformat() + 'Z' # 30 min slot
            
            events_result = self.service.events().list(calendarId='primary', timeMin=time_min,
                                                    timeMax=time_max, singleEvents=True,
                                                    orderBy='startTime').execute()
            events = events_result.get('items', [])

            if events:
                 return {
                    "final_response": f"You already have an event at {dt.strftime('%Y-%m-%d %H:%M')}. Please choose a different time.",
                    "next_step": "end"
                }

            # Create Event
            event = {
                'summary': 'Medical Appointment (MedAgent)',
                'location': 'Online / Clinic',
                'description': f'Appointment scheduled via MedAgent.\nUrgency: {urgency}',
                'start': {
                    'dateTime': dt.isoformat(),
                    'timeZone': 'UTC', # Default to UTC for simplicity, should extract user TZ
                },
                'end': {
                    'dateTime': (dt + datetime.timedelta(minutes=30)).isoformat(),
                    'timeZone': 'UTC',
                },
            }

            event = self.service.events().insert(calendarId='primary', body=event).execute()
            
            return {
                "final_response": f"Appointment confirmed!\nTitle: {event.get('summary')}\nLink: {event.get('htmlLink')}\nTime: {dt.strftime('%Y-%m-%d %H:%M')}",
                "next_step": "end"
            }

        except HttpError as error:
            logger.error(f"An error occurred: {error}")
            return {
                "final_response": "Failed to access Google Calendar API.",
                "next_step": "end"
            }

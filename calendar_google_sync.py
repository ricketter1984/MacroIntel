#!/usr/bin/env python3
"""
MacroIntel Google Calendar Sync Module
Syncs FMP economic calendar events to Google Calendar with OAuth 2.0 authentication
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from pathlib import Path
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Validate FMP_API_KEY is loaded
assert os.getenv("FMP_API_KEY"), "FMP_API_KEY is not set in environment!"

# Configure stdout encoding for Unicode support
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Google Calendar API imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False

class GoogleCalendarSync:
    """Syncs FMP economic calendar events to Google Calendar."""
    
    def __init__(self, config_dir: str = "config", logs_dir: str = "logs"):
        """Initialize the Google Calendar sync engine."""
        
        self.config_dir = Path(config_dir)
        self.logs_dir = Path(logs_dir)
        self.credentials_file = self.config_dir / "credentials.json"
        self.token_file = self.config_dir / "token.json"
        self.events_log = self.logs_dir / "calendar_events_log.json"
        
        # Google Calendar settings
        self.scopes = ['https://www.googleapis.com/auth/calendar']
        self.calendar_name = 'MacroIntel Economic Events'
        self.calendar_id = None
        self.service = None
        
        # FMP API settings
        self.fmp_api_key = os.getenv("FMP_API_KEY")
        
        # Important economic indicators to filter for
        self.important_indicators = {
            'CPI', 'FOMC', 'GDP', 'NFP', 'PPI', 'PMI', 'EIA',
            'Interest Rate', 'Inflation', 'Employment', 'Retail Sales',
            'Manufacturing', 'Consumer Confidence', 'Trade Balance',
            'Current Account', 'Industrial Production', 'Housing',
            'Fed', 'Central Bank', 'Unemployment', 'Core CPI'
        }
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Create directories
        self.config_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        
        # Track processed events to avoid duplicates
        self.processed_events = set()
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.logs_dir / 'calendar_sync.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        return logging.getLogger(__name__)

    def authenticate_google_calendar(self) -> bool:
        """Authenticate with Google Calendar API using OAuth 2.0."""
        
        if not GOOGLE_API_AVAILABLE:
            self.logger.error("ERROR: Google API libraries not available. Install with: pip install google-auth google-auth-oauthlib google-api-python-client")
            return False
        
        if not self.credentials_file.exists():
            self.logger.error(f"ERROR: credentials.json not found at {self.credentials_file}")
            self.logger.error("HELP: Download credentials.json from Google Cloud Console and place in config/")
            return False
        
        creds = None
        
        # Check if token file exists and load existing credentials
        if self.token_file.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(self.token_file), self.scopes)
                self.logger.info("AUTH: Loaded existing credentials from token file")
            except Exception as e:
                self.logger.warning(f"WARNING: Could not load existing token: {e}")
        
        # If there are no valid credentials available, request authorization
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    self.logger.info("AUTH: Refreshed expired credentials")
                except Exception as e:
                    self.logger.warning(f"WARNING: Could not refresh credentials: {e}")
                    creds = None
            
            if not creds:
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.credentials_file), self.scopes)
                    creds = flow.run_local_server(port=0)
                    self.logger.info("AUTH: Completed OAuth 2.0 flow")
                except Exception as e:
                    self.logger.error(f"ERROR: OAuth 2.0 authentication failed: {e}")
                    return False
        
        # Save credentials for next run
        try:
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
            self.logger.info(f"AUTH: Saved credentials to {self.token_file}")
        except Exception as e:
            self.logger.warning(f"WARNING: Could not save credentials: {e}")
        
        # Build the service
        try:
            self.service = build('calendar', 'v3', credentials=creds)
            self.logger.info("SUCCESS: Google Calendar API service initialized")
            return True
        except Exception as e:
            self.logger.error(f"ERROR: Failed to build Google Calendar service: {e}")
            return False

    def find_or_create_calendar(self) -> bool:
        """Find or create the MacroIntel Economic Events calendar."""
        
        if not self.service:
            self.logger.error("ERROR: Google Calendar service not initialized")
            return False
        
        try:
            # List existing calendars
            calendar_list = self.service.calendarList().list().execute()
            calendars = calendar_list.get('items', [])
            
            # Look for existing MacroIntel calendar
            for calendar in calendars:
                if calendar.get('summary') == self.calendar_name:
                    self.calendar_id = calendar['id']
                    self.logger.info(f"FOUND: MacroIntel calendar exists with ID: {self.calendar_id}")
                    return True
            
            # Create new calendar if not found
            calendar_body = {
                'summary': self.calendar_name,
                'description': 'Automated economic events calendar synced from FMP API',
                'timeZone': 'America/New_York'
            }
            
            created_calendar = self.service.calendars().insert(body=calendar_body).execute()
            self.calendar_id = created_calendar['id']
            
            self.logger.info(f"CREATED: New MacroIntel calendar with ID: {self.calendar_id}")
            return True
            
        except HttpError as e:
            self.logger.error(f"ERROR: Google Calendar API error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"ERROR: Failed to find/create calendar: {e}")
            return False

    def fetch_fmp_economic_events(self, days_forward: int = 7) -> List[Dict]:
        """Fetch economic events from FMP API for the next N days."""
        
        if not self.fmp_api_key:
            self.logger.error("ERROR: FMP_API_KEY not found in environment variables")
            return []
        
        try:
            today = datetime.now().date()
            end_date = today + timedelta(days=days_forward)
            
            url = "https://financialmodelingprep.com/api/v3/economic_calendar"
            params = {
                'from': today.strftime('%Y-%m-%d'),
                'to': end_date.strftime('%Y-%m-%d'),
                'apikey': self.fmp_api_key
            }
            
            self.logger.info(f"API: Fetching events from {today} to {end_date}")
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if isinstance(data, list):
                self.logger.info(f"SUCCESS: Retrieved {len(data)} events from FMP API")
                return data
            else:
                self.logger.warning("WARNING: Unexpected response format from FMP API")
                return []
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"ERROR: FMP API request failed: {e}")
            return []
        except Exception as e:
            self.logger.error(f"ERROR: Failed to fetch FMP events: {e}")
            return []

    def filter_important_events(self, events: List[Dict]) -> List[Dict]:
        """Filter events by importance and relevance."""
        
        filtered_events = []
        
        for event in events:
            try:
                event_name = event.get('event', '').lower()
                country = event.get('country', '').upper()
                impact = event.get('impact', '').lower()
                
                # Check if event matches important indicators
                is_important = any(indicator.lower() in event_name for indicator in self.important_indicators)
                
                # Include high impact events regardless
                is_high_impact = impact == 'high'
                
                # Include major country events (US, EU, UK, JP, CN)
                is_major_country = country in ['US', 'EU', 'UK', 'JP', 'CN', 'DE', 'FR']
                
                if is_important or is_high_impact or (is_major_country and impact == 'medium'):
                    filtered_events.append(event)
                    
            except Exception as e:
                self.logger.warning(f"WARNING: Error filtering event: {e}")
                continue
        
        self.logger.info(f"FILTER: {len(filtered_events)} important events out of {len(events)} total")
        return filtered_events

    def create_event_key(self, event: Dict) -> str:
        """Create a unique key for an event to detect duplicates."""
        
        try:
            date = event.get('date', '')
            time = event.get('time', '')
            event_name = event.get('event', '')
            country = event.get('country', '')
            
            # Create key from date, time, event name, and country
            key = f"{date}_{time}_{event_name}_{country}".replace(' ', '_').lower()
            return key
            
        except Exception as e:
            self.logger.warning(f"WARNING: Error creating event key: {e}")
            return f"unknown_{datetime.now().timestamp()}"

    def parse_event_datetime(self, event: Dict) -> Optional[datetime]:
        """Parse event date and time into datetime object."""
        
        try:
            date_str = event.get('date', '')
            time_str = event.get('time', '')
            
            if not date_str:
                return None
            
            # Parse different date formats from FMP API
            event_datetime = None
            
            # Try different parsing strategies
            try:
                # Strategy 1: Full datetime string "2025-07-22 04:00:00"
                if ' ' in date_str and ':' in date_str:
                    event_datetime = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                
                # Strategy 2: ISO format "2025-07-22T04:00:00"
                elif 'T' in date_str:
                    # Remove timezone info if present
                    clean_date = date_str.split('T')[0] + 'T' + date_str.split('T')[1].split('+')[0].split('-')[0]
                    if clean_date.count(':') == 2:
                        event_datetime = datetime.strptime(clean_date, '%Y-%m-%dT%H:%M:%S')
                    else:
                        event_datetime = datetime.strptime(date_str.split('T')[0], '%Y-%m-%d')
                        event_datetime = event_datetime.replace(hour=14, minute=30)
                
                # Strategy 3: Date only "2025-07-22"
                elif '-' in date_str and len(date_str) == 10:
                    event_datetime = datetime.strptime(date_str, '%Y-%m-%d')
                    event_datetime = event_datetime.replace(hour=14, minute=30)
                
                # Strategy 4: Try to extract date part from any string
                else:
                    # Try to find date pattern in string
                    import re
                    date_pattern = r'(\d{4}-\d{2}-\d{2})'
                    match = re.search(date_pattern, date_str)
                    if match:
                        event_datetime = datetime.strptime(match.group(1), '%Y-%m-%d')
                        event_datetime = event_datetime.replace(hour=14, minute=30)
                        
            except ValueError as e:
                self.logger.debug(f"Date parsing failed for '{date_str}': {e}")
                return None
            
            # If we still don't have a datetime, try fallback parsing
            if not event_datetime:
                try:
                    # Last resort: try to parse just the date part
                    date_part = date_str.split(' ')[0].split('T')[0]
                    event_datetime = datetime.strptime(date_part, '%Y-%m-%d')
                    event_datetime = event_datetime.replace(hour=14, minute=30)
                except ValueError:
                    return None
            
            # Override with separate time field if available and valid
            if time_str and time_str != 'N/A' and time_str.strip():
                try:
                    # Handle different time formats
                    if ':' in time_str:
                        time_parts = time_str.split(':')
                        hour = int(time_parts[0])
                        minute = int(time_parts[1]) if len(time_parts) > 1 else 0
                        # Replace the time portion
                        event_datetime = event_datetime.replace(hour=hour, minute=minute)
                except (ValueError, IndexError):
                    # Keep the datetime from date parsing if time parsing fails
                    pass
            
            return event_datetime
            
        except Exception as e:
            self.logger.warning(f"WARNING: Error parsing event datetime for '{date_str}': {e}")
            return None

    def create_google_calendar_event(self, event: Dict) -> bool:
        """Create a Google Calendar event from FMP event data."""
        
        if not self.service or not self.calendar_id:
            self.logger.error("ERROR: Google Calendar service or calendar ID not available")
            return False
        
        try:
            # Parse event datetime
            event_datetime = self.parse_event_datetime(event)
            if not event_datetime:
                self.logger.warning(f"WARNING: Could not parse datetime for event: {event.get('event')}")
                return False
            
            # Check for duplicates
            event_key = self.create_event_key(event)
            if event_key in self.processed_events:
                self.logger.debug(f"SKIP: Duplicate event detected: {event.get('event')}")
                return False
            
            # Create event title
            event_name = event.get('event', 'Economic Event')
            country = event.get('country', 'Unknown')
            impact = event.get('impact', 'Low').capitalize()
            title = f"[{event_name}] - {country} - {impact}"
            
            # Create event description
            description_parts = [
                f"Economic Event: {event_name}",
                f"Country: {country}",
                f"Impact Level: {impact}",
                f"Currency: {event.get('currency', 'N/A')}"
            ]
            
            # Add value information if available
            actual = event.get('actual', '')
            estimate = event.get('estimate', '')
            previous = event.get('previous', '')
            
            if actual or estimate or previous:
                description_parts.append("")
                description_parts.append("Values:")
                if actual:
                    description_parts.append(f"  Actual: {actual}")
                if estimate:
                    description_parts.append(f"  Estimate: {estimate}")
                if previous:
                    description_parts.append(f"  Previous: {previous}")
            
            description_parts.append("")
            description_parts.append("Source: Financial Modeling Prep API")
            description_parts.append("Synced by MacroIntel Calendar Sync")
            
            description = "\n".join(description_parts)
            
            # Create calendar event body
            end_datetime = event_datetime + timedelta(minutes=30)  # 30-minute events
            
            calendar_event = {
                'summary': title,
                'description': description,
                'start': {
                    'dateTime': event_datetime.isoformat(),
                    'timeZone': 'America/New_York',
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': 'America/New_York',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 15},
                    ],
                },
            }
            
            # Insert event into calendar
            created_event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=calendar_event
            ).execute()
            
            # Mark as processed
            self.processed_events.add(event_key)
            
            self.logger.info(f"CREATED: {title} on {event_datetime.strftime('%Y-%m-%d %H:%M')}")
            return True
            
        except HttpError as e:
            self.logger.error(f"ERROR: Google Calendar API error creating event: {e}")
            return False
        except Exception as e:
            self.logger.error(f"ERROR: Failed to create calendar event: {e}")
            return False

    def load_existing_events_log(self) -> Set[str]:
        """Load previously processed events from log file."""
        
        try:
            if self.events_log.exists():
                with open(self.events_log, 'r') as f:
                    log_data = json.load(f)
                    
                processed_keys = set()
                for entry in log_data.get('events', []):
                    event_key = entry.get('event_key', '')
                    if event_key:
                        processed_keys.add(event_key)
                
                self.logger.info(f"LOADED: {len(processed_keys)} previously processed events")
                return processed_keys
            else:
                self.logger.info("LOG: No existing events log found")
                return set()
                
        except Exception as e:
            self.logger.error(f"ERROR: Failed to load events log: {e}")
            return set()

    def save_events_log(self, synced_events: List[Dict]) -> bool:
        """Save synced events to log file."""
        
        try:
            # Load existing log data
            log_data = {'events': [], 'sync_history': []}
            if self.events_log.exists():
                try:
                    with open(self.events_log, 'r') as f:
                        log_data = json.load(f)
                except Exception:
                    pass
            
            # Add new sync session
            sync_session = {
                'timestamp': datetime.now().isoformat(),
                'events_synced': len(synced_events),
                'events': []
            }
            
            # Add individual events
            for event in synced_events:
                event_key = self.create_event_key(event)
                event_log = {
                    'event_key': event_key,
                    'event_name': event.get('event', ''),
                    'country': event.get('country', ''),
                    'date': event.get('date', ''),
                    'time': event.get('time', ''),
                    'impact': event.get('impact', ''),
                    'synced_at': datetime.now().isoformat()
                }
                
                sync_session['events'].append(event_log)
                
                # Add to main events list if not already present
                if not any(e.get('event_key') == event_key for e in log_data['events']):
                    log_data['events'].append(event_log)
            
            # Add sync session to history
            log_data['sync_history'].append(sync_session)
            
            # Keep only last 100 sync sessions
            if len(log_data['sync_history']) > 100:
                log_data['sync_history'] = log_data['sync_history'][-100:]
            
            # Save to file
            with open(self.events_log, 'w') as f:
                json.dump(log_data, f, indent=2)
            
            self.logger.info(f"LOG: Saved {len(synced_events)} events to {self.events_log}")
            return True
            
        except Exception as e:
            self.logger.error(f"ERROR: Failed to save events log: {e}")
            return False

    def sync_calendar(self, days_forward: int = 7) -> bool:
        """Main sync function to sync FMP events to Google Calendar."""
        
        try:
            self.logger.info("SYNC: Starting MacroIntel calendar sync...")
            
            # Check dependencies
            if not GOOGLE_API_AVAILABLE:
                self.logger.error("ERROR: Google API libraries not available")
                return False
            
            # Authenticate with Google Calendar
            if not self.authenticate_google_calendar():
                self.logger.error("ERROR: Google Calendar authentication failed")
                return False
            
            # Find or create calendar
            if not self.find_or_create_calendar():
                self.logger.error("ERROR: Failed to find/create MacroIntel calendar")
                return False
            
            # Load previously processed events
            self.processed_events = self.load_existing_events_log()
            
            # Fetch events from FMP
            raw_events = self.fetch_fmp_economic_events(days_forward)
            if not raw_events:
                self.logger.warning("WARNING: No events fetched from FMP API")
                return False
            
            # Filter important events
            important_events = self.filter_important_events(raw_events)
            if not important_events:
                self.logger.warning("WARNING: No important events found after filtering")
                return False
            
            # Sync events to Google Calendar
            synced_count = 0
            synced_events = []
            
            for event in important_events:
                if self.create_google_calendar_event(event):
                    synced_count += 1
                    synced_events.append(event)
            
            # Save events log
            if synced_events:
                self.save_events_log(synced_events)
            
            # Log summary
            self.logger.info("SUMMARY: Calendar sync completed")
            self.logger.info(f"  Total FMP events: {len(raw_events)}")
            self.logger.info(f"  Important events: {len(important_events)}")
            self.logger.info(f"  Events synced: {synced_count}")
            self.logger.info(f"  Events skipped: {len(important_events) - synced_count}")
            
            if synced_count == 0:
                self.logger.warning("WARNING: No new events were synced to calendar")
                return False
            
            self.logger.info("SUCCESS: Calendar sync completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"ERROR: Calendar sync failed: {e}")
            return False

def main():
    """Main CLI entry point."""
    
    parser = argparse.ArgumentParser(description="MacroIntel Google Calendar Sync")
    parser.add_argument("--sync", action="store_true", help="Sync FMP economic events to Google Calendar")
    parser.add_argument("--days", type=int, default=7, help="Number of days forward to sync (default: 7)")
    parser.add_argument("--test", action="store_true", help="Test authentication without syncing")
    
    args = parser.parse_args()
    
    # Initialize sync engine
    sync_engine = GoogleCalendarSync()
    
    if args.test:
        print("TEST: Testing Google Calendar authentication...")
        
        if sync_engine.authenticate_google_calendar():
            print("SUCCESS: Google Calendar authentication successful")
            
            if sync_engine.find_or_create_calendar():
                print(f"SUCCESS: MacroIntel calendar ready (ID: {sync_engine.calendar_id})")
            else:
                print("ERROR: Failed to find/create MacroIntel calendar")
        else:
            print("ERROR: Google Calendar authentication failed")
    
    elif args.sync:
        print("SYNC: Starting MacroIntel calendar sync...")
        
        success = sync_engine.sync_calendar(days_forward=args.days)
        
        if success:
            print("SUCCESS: Calendar sync completed successfully")
        else:
            print("ERROR: Calendar sync failed - check logs for details")
            sys.exit(1)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 
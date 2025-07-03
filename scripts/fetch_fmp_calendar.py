#!/usr/bin/env python3
"""
FMP Economic Calendar Fetcher Script

This script fetches economic calendar data from Financial Modeling Prep API.
Designed to be called by the API dispatcher in an isolated environment.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv(dotenv_path=project_root / "config" / ".env")

def fetch_fmp_calendar():
    """Fetch economic calendar data from FMP API."""
    try:
        from utils.api_clients import fetch_fmp_calendar
        
        print("Fetching FMP economic calendar data...")
        
        # Fetch calendar data for next 7 days
        end_date = datetime.now() + timedelta(days=7)
        calendar_data = fetch_fmp_calendar(
            from_date=datetime.now().strftime("%Y-%m-%d"),
            to_date=end_date.strftime("%Y-%m-%d")
        )
        
        if calendar_data and len(calendar_data) > 0:
            # Process and categorize events
            processed_events = []
            high_impact_events = []
            medium_impact_events = []
            
            for event in calendar_data:
                processed_event = {
                    "event": event.get("event", "Unknown"),
                    "date": event.get("date", ""),
                    "time": event.get("time", ""),
                    "country": event.get("country", ""),
                    "currency": event.get("currency", ""),
                    "impact": event.get("impact", "Low"),
                    "actual": event.get("actual", ""),
                    "forecast": event.get("forecast", ""),
                    "previous": event.get("previous", "")
                }
                processed_events.append(processed_event)
                
                if processed_event["impact"] == "High":
                    high_impact_events.append(processed_event)
                elif processed_event["impact"] == "Medium":
                    medium_impact_events.append(processed_event)
            
            print(f"Successfully fetched {len(processed_events)} economic events")
            print(f"  High impact: {len(high_impact_events)}")
            print(f"  Medium impact: {len(medium_impact_events)}")
            print(f"  Low impact: {len(processed_events) - len(high_impact_events) - len(medium_impact_events)}")
            
            # Save to output directory
            output_dir = project_root / "output"
            output_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"fmp_calendar_{timestamp}.json"
            
            result_data = {
                "success": True,
                "total_events": len(processed_events),
                "high_impact_events": high_impact_events,
                "medium_impact_events": medium_impact_events,
                "all_events": processed_events,
                "timestamp": datetime.now().isoformat(),
                "source": "fmp_calendar"
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2, default=str)
            
            print(f"Calendar data saved to: {output_file}")
            
            return result_data
            
        else:
            error_msg = "No calendar data retrieved"
            print(f"{error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "timestamp": datetime.now().isoformat(),
                "source": "fmp_calendar"
            }
            
    except ImportError as e:
        error_msg = f"Import error: {e}"
        print(f"{error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "timestamp": datetime.now().isoformat(),
            "source": "fmp_calendar"
        }
    except Exception as e:
        error_msg = f"Error fetching FMP calendar: {e}"
        print(f"{error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "timestamp": datetime.now().isoformat(),
            "source": "fmp_calendar"
        }

def main():
    """Main function to execute the calendar fetching."""
    print("Fetching FMP Economic Calendar Data...")
    print(f"Project root: {project_root}")
    print(f"Python executable: {sys.executable}")
    
    # Check API key
    api_key = os.getenv("FMP_API_KEY")
    if not api_key:
        print("FMP_API_KEY not found in environment variables")
        sys.exit(1)
    
    # Fetch calendar
    result = fetch_fmp_calendar()
    
    # Print result
    print(f"\nCalendar fetch completed successfully!")
    print(json.dumps(result, indent=2))
    
    # Exit with appropriate code
    if result["success"]:
        sys.exit(0)
    else:
        print(f"Calendar fetch failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)

if __name__ == "__main__":
    main()

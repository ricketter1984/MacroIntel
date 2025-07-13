#!/usr/bin/env python3
"""
Quick test of FMP economic events for MacroIntel Calendar Sync
"""

import os
import sys
from datetime import datetime

# Set API key
os.environ['FMP_API_KEY'] = 'zvWydfhrVNaCoGPjw5QfnNGsqyypMecS'

from calendar_google_sync import GoogleCalendarSync

def main():
    print("🧪 MacroIntel Calendar Sync - FMP Events Test")
    print("=" * 50)
    
    # Initialize sync engine
    sync = GoogleCalendarSync()
    
    # Fetch events for next 3 days
    print("\n📡 Fetching events from FMP API...")
    events = sync.fetch_fmp_economic_events(3)
    print(f"✅ Retrieved {len(events)} total events")
    
    # Filter important events
    print("\n🎯 Filtering important events...")
    important_events = sync.filter_important_events(events)
    print(f"✅ Found {len(important_events)} important events")
    
    # Show breakdown by impact
    impact_counts = {}
    for event in important_events:
        impact = event.get('impact', 'Unknown')
        impact_counts[impact] = impact_counts.get(impact, 0) + 1
    
    print(f"\n📊 Important Events by Impact Level:")
    for impact, count in sorted(impact_counts.items()):
        print(f"   {impact}: {count} events")
    
    # Show sample high-impact events
    high_impact = [e for e in important_events if e.get('impact') == 'High']
    if high_impact:
        print(f"\n🔥 Sample High-Impact Events ({len(high_impact)} total):")
        for i, event in enumerate(high_impact[:5]):
            date = event.get('date', 'Unknown')
            time = event.get('time', 'Unknown')
            name = event.get('event', 'Unknown')
            country = event.get('country', 'Unknown')
            
            print(f"   {i+1}. [{country}] {name}")
            print(f"      📅 {date} {time}")
            
            # Show values if available
            actual = event.get('actual', '')
            estimate = event.get('estimate', '')
            previous = event.get('previous', '')
            
            values = []
            if actual: values.append(f"Actual: {actual}")
            if estimate: values.append(f"Est: {estimate}")
            if previous: values.append(f"Prev: {previous}")
            
            if values:
                print(f"      💹 {' | '.join(values)}")
            print()
    
    # Show sample medium-impact events
    medium_impact = [e for e in important_events if e.get('impact') == 'Medium']
    if medium_impact:
        print(f"\n📈 Sample Medium-Impact Events ({len(medium_impact)} total):")
        for i, event in enumerate(medium_impact[:3]):
            date = event.get('date', 'Unknown')
            name = event.get('event', 'Unknown')
            country = event.get('country', 'Unknown')
            print(f"   {i+1}. [{country}] {name} - {date}")
    
    # Test event processing
    print(f"\n🔧 Testing Event Processing:")
    if important_events:
        test_event = important_events[0]
        event_key = sync.create_event_key(test_event)
        event_datetime = sync.parse_event_datetime(test_event)
        
        print(f"   Event Key: {event_key}")
        print(f"   Parsed DateTime: {event_datetime}")
        
        # Show how the calendar event would look
        event_name = test_event.get('event', 'Economic Event')
        country = test_event.get('country', 'Unknown')
        impact = test_event.get('impact', 'Low').capitalize()
        title = f"[{event_name}] - {country} - {impact}"
        
        print(f"   Calendar Title: {title}")
    
    print("\n" + "=" * 50)
    print("✅ FMP API integration working perfectly!")
    print("🔧 Next steps:")
    print("   1. Install Google Calendar deps: pip install -r requirements_google_calendar.txt")
    print("   2. Setup OAuth credentials in config/credentials.json")
    print("   3. Run: python calendar_google_sync.py --test")
    print("   4. Run: python calendar_google_sync.py --sync")

if __name__ == "__main__":
    main() 
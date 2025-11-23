from pocketflow import Flow
from nodes import CreateCalendarEventNode, ListCalendarEventsNode, ListCalendarsNode
from datetime import datetime, timedelta

def create_calendar_flow():
    """Creates a flow to manage calendar events."""
    # Create nodes
    create_event_node = CreateCalendarEventNode()
    list_events_node = ListCalendarEventsNode()
    
    # Connect nodes
    create_event_node - "success" >> list_events_node
    create_event_node - "error" >> None
    
    # Create flow
    return Flow(start=create_event_node)

def list_calendars_flow():
    """Creates a flow to list all user calendars."""
    list_calendars_node = ListCalendarsNode()
    return Flow(start=list_calendars_node)

def main():
    # Example: List all calendars
    print("=== Listing your calendars ===")
    flow = list_calendars_flow()
    shared = {}
    flow.run(shared)
    
    if 'available_calendars' in shared:
        for cal in shared['available_calendars']:
            print(f"- {cal.get('summary')}")

    # Example: Create a simple event
    print("\n=== Creating an example event ===")
    flow = create_calendar_flow()

    shared = {
        'event_summary': 'Example Meeting',
        'event_description': 'An example meeting created by PocketFlow',
        'event_start_time': datetime.now() + timedelta(days=1),
        'event_end_time': datetime.now() + timedelta(days=1, hours=1),
        'days_to_list': 7
    }

    flow.run(shared)
    
    if 'last_created_event' in shared:
        print("Event created successfully!")
        print(f"Event ID: {shared['last_created_event']['id']}")

if __name__ == "__main__":
    main()
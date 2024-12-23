import EventPage from './EventPage';
import { getAllEvents } from '@/services/events';


export async function generateStaticParams() {
  try {
    const events = await getAllEvents();
    const eventsIds = events.map((event) => ({ id: event.id }))
    console.log("Events IDs:", eventsIds);
    return eventsIds
  } catch (error) {
    console.error("Error fetching events:", error);
    return [];
  }
}

export  default async function Page({ params }) {
  const { id } = await params;

  return (
    <div>
    
      {/* Pass dynamic ID to the client component */}
      <EventPage id={id} />
    </div>
  );
}
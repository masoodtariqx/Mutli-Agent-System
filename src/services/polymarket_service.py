import requests
from typing import Optional, List
from src.models import EventMetadata

class PolymarketService:
    BASE_URL = "https://gamma-api.polymarket.com"

    @classmethod
    def get_event_details(cls, input_identifier: str) -> Optional[EventMetadata]:
        """
        Fetches event details. Input can be a numeric ID, a slug, or a full URL.
        """
        # 1. Extract slug if full URL is provided
        if "polymarket.com/event/" in input_identifier:
            input_identifier = input_identifier.split("polymarket.com/event/")[1].split("?")[0].strip("/")
        
        # 2. Determine if it's an ID or a Slug
        is_id = input_identifier.isdigit()
        
        try:
            if is_id:
                url = f"{cls.BASE_URL}/events/{input_identifier}"
            else:
                # If it's a slug, we need to query the events list by slug
                url = f"{cls.BASE_URL}/events?slug={input_identifier}"
            
            response = requests.get(url)
            if response.status_code != 200:
                print(f"Error fetching event: {response.status_code}")
                return None
            
            data = response.json()
            
            # If fetched by slug, it returns a list
            if not is_id:
                if isinstance(data, list) and len(data) > 0:
                    data = data[0]
                else:
                    print(f"No event found for slug: {input_identifier}")
                    return None
            
            return EventMetadata(
                event_id=str(data.get("id")),
                title=data.get("title", ""),
                description=data.get("description", ""),
                resolution_rules=data.get("rules", ""),
                market_probability=data.get("market_probability"),
                liquidity=data.get("liquidity"),
                resolution_date=data.get("ends_at", "")
            )
        except Exception as e:
            print(f"Exception fetching event: {e}")
            return None

    @classmethod
    def search_tech_events(cls, limit: int = 10) -> List[EventMetadata]:
        """
        Automated discovery of tech events using keywords.
        """
        tech_keywords = ["AI", "OpenAI", "GPT", "Tesla", "SpaceX", "Apple", "Nvidia", "Google", "Microsoft", "Meta"]
        query = " ".join(tech_keywords)
        
        try:
            # Polymarket Gamma events endpoint with sorting for "trending" (liquidity)
            params = {
                "active": "true",
                "closed": "false",
                "limit": limit,
                "search": "AI",
                "order": "liquidity",
                "ascending": "false"
            }
            response = requests.get(cls.BASE_URL + "/events", params=params)
            if response.status_code != 200:
                return []
            
            events_data = response.json()
            discovered = []
            
            for data in events_data:
                # Basic filtering for tech relevance if needed
                discovered.append(EventMetadata(
                    event_id=str(data.get("id")),
                    title=data.get("title", ""),
                    description=data.get("description", ""),
                    resolution_rules=data.get("rules", ""),
                    market_probability=data.get("market_probability"),
                    liquidity=data.get("liquidity"),
                    resolution_date=data.get("ends_at", "")
                ))
            return discovered
        except Exception as e:
            print(f"Exception during discovery: {e}")
            return []

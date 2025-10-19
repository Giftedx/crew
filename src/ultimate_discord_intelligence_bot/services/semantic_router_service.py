
import os

from semantic_router import Route
from semantic_router.encoders import OpenAIEncoder
from semantic_router.layer import RouteLayer

from core.settings import get_settings


class SemanticRouterService:
    def __init__(self, routes: list[Route] | None = None):
        self.settings = get_settings()
        self.encoder = self._get_encoder()
        if routes:
            self.rl = RouteLayer(encoder=self.encoder, routes=routes)
        else:
            self.rl = None

    def _get_encoder(self):
        if self.settings.OPENROUTER_API_KEY:
            return OpenAIEncoder(
                openai_api_key=self.settings.OPENROUTER_API_KEY,
                openai_api_base=self.settings.OPENROUTER_API_BASE,
            )
        # Fallback or default encoder if no OpenRouter key
        return OpenAIEncoder(openai_api_key=os.getenv("OPENAI_API_KEY"))

    def add_routes(self, routes: list[Route]):
        self.rl = RouteLayer(encoder=self.encoder, routes=routes)

    def route(self, query: str) -> str | None:
        if not self.rl:
            return None

        if self.settings.ENABLE_SEMANTIC_ROUTER:
            try:
                response = self.rl(query)
                return response.name
            except Exception as e:
                # Log the error appropriately
                print(f"Semantic router failed: {e}")
                return None
        return None

# Example usage (can be removed or adapted)
if __name__ == "__main__":
    # Define some example routes
    search_route = Route(
        name="search",
        utterances=[
            "search for information about",
            "find me details on",
            "what is the capital of France?",
        ],
    )

    transcribe_route = Route(
        name="transcribe_audio",
        utterances=[
            "transcribe this audio file",
            "what is being said in this audio?",
            "convert this speech to text",
        ],
    )

    routes = [search_route, transcribe_route]

    # Initialize the service
    router_service = SemanticRouterService(routes=routes)

    # Test the router
    query = "can you find me details on the latest AI advancements?"
    route_name = router_service.route(query)
    print(f"Query: '{query}' -> Route: '{route_name}'")

    query_2 = "please transcribe this lecture recording"
    route_name_2 = router_service.route(query_2)
    print(f"Query: '{query_2}' -> Route: '{route_name_2}'")

    query_3 = "tell me a joke"
    route_name_3 = router_service.route(query_3)
    print(f"Query: '{query_3}' -> Route: '{route_name_3}'")

from fastapi import APIRouter

from app.api.v1.endpoints import admin, analytics, artifacts, auth, capabilities, domain_packs, events, knowledge, org, planning, promotions, queue_routing, requests, reviews, runtime, runs, templates


api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(requests.router, prefix="/requests", tags=["requests"])
api_router.include_router(templates.router, prefix="/templates", tags=["templates"])
api_router.include_router(runs.router, prefix="/runs", tags=["runs"])
api_router.include_router(artifacts.router, prefix="/artifacts", tags=["artifacts"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["knowledge"])
api_router.include_router(planning.router, prefix="/planning", tags=["planning"])
api_router.include_router(domain_packs.router, prefix="/domain-packs", tags=["domain-packs"])
api_router.include_router(queue_routing.router, prefix="/queue-routing", tags=["queue-routing"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
api_router.include_router(promotions.router, prefix="/promotions", tags=["promotions"])
api_router.include_router(capabilities.router, prefix="/capabilities", tags=["capabilities"])
api_router.include_router(org.router, prefix="/org", tags=["org"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(events.router, prefix="/events", tags=["events"])
api_router.include_router(runtime.router, prefix="/runtime", tags=["runtime"])

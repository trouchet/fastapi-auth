from fastapi import Request, FastAPI
from fastapi.routing import APIRoute

def get_token(request: Request) -> str:
    return request.headers.get('Authorization', '').replace('Bearer ', '')

def get_route_and_token(request: Request):
    route = request.scope['path']
    token = request.headers.get('Authorization', '').replace('Bearer ', '')

    return route, token

# List all routes
def list_routes(app: FastAPI):
    route_info = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            route_info.append({
                "path": route.path,
                "name": route.name,
                "methods": route.methods,
            })
    return route_info

def get_route(request: Request) -> str:
    return request.scope['path']

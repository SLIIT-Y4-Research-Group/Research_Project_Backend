from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import mood_routes, auth_routes, parent_management_routes, child_routes, trusted_routes

app = FastAPI(title="Children Mental Health API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],         
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(mood_routes.router)
app.include_router(auth_routes.router)
app.include_router(parent_management_routes.router)
app.include_router(child_routes.router)
app.include_router(trusted_routes.router)

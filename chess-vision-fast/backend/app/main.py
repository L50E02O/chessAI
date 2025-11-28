from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import routes
from .utils import get_settings

settings = get_settings()

app = FastAPI(title='Chess Vision Fast', version='0.1.0')

# CORS debe ir primero y permitir todo en desarrollo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router)


@app.get('/health')
def health() -> dict:
    return {'status': 'ok'}

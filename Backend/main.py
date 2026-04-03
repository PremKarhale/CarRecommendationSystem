from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from Routes import recommend

app = FastAPI(title="Car Recommendation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(recommend.router, prefix="/api/cars")

@app.get("/")
def root():
    return {
        "message":"Welcome to Car Recommendation System API "
    }

@app.get("/health")
def health():
    return {
        "status":"ok"
    }

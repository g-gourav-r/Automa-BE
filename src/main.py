from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api import api_router

app = FastAPI(title="Automa API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Automa API!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi import FastAPI
from app.routes import upload, chat, retrieve

app = FastAPI()

# Include routers
app.include_router(upload.router, prefix="/upload", tags=["upload"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(retrieve.router, prefix="/retrieve", tags=["retrieve"])

@app.get("/")
def root():
    return {"message": "Welcome to the PDF Chat Application"}

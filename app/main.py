import io
from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

    
from .utils.helpers import decode_base64_to_image, serialize_context
from .services.pdf_processor import PDFProcessor
from .services.chat_service import ChatService
from .models.schemas import ChatRequest, ChatResponse, DocumentSummary
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
import tempfile
import shutil
# Initialize PDF processor
from .services.pdf_processor import PDFProcessor

# Load environment variables
load_dotenv()

app = FastAPI(title="PDF Chat API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize templates
templates = Jinja2Templates(directory="templates")

# Store PDF processors for each session
pdf_sessions = {}

@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")

        # Create temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = os.path.join(temp_dir, file.filename)
            
            # Save uploaded file
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            
            processor = PDFProcessor()
            
            # Process the PDF
            await processor.process_pdf(temp_file_path)
            
            # Generate session ID and store processor
            session_id = PDFProcessor.generate_session_id()
            pdf_sessions[session_id] = processor
            
            return JSONResponse({
                "session_id": session_id,
                "message": "PDF processed successfully",
                "summary": {
                    "text_summaries": processor.text_summaries if hasattr(processor, 'text_summaries') else [],
                    "table_summaries": processor.table_summaries if hasattr(processor, 'table_summaries') else [],
                    "image_summaries": processor.image_summaries if hasattr(processor, 'image_summaries') else []
                }
            })
            
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")  # Add logging
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")


@app.post("/chat/{session_id}", response_model=ChatResponse)
async def chat_with_pdf(session_id: str, request: ChatRequest):
    if session_id not in pdf_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        processor = pdf_sessions[session_id]
        chat_service = ChatService(processor)
        
        response = await chat_service.get_response(request.question)
        
        serialized_context = serialize_context(response['context'])
        
        return ChatResponse(
            answer=response['response'],
            context=serialized_context
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/image/{session_id}/{image_index}")
async def get_image(session_id: str, image_index: int):
    if session_id not in pdf_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    processor = pdf_sessions[session_id]
    
    if image_index >= len(processor.images):
        raise HTTPException(status_code=404, detail="Image not found")
    
    try:
        image_bytes = decode_base64_to_image(processor.images[image_index])
        return StreamingResponse(io.BytesIO(image_bytes), media_type="image/jpeg")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/session/{session_id}")
async def end_session(session_id: str):
    if session_id in pdf_sessions:
        del pdf_sessions[session_id]
        return {"message": "Session ended successfully"}
    raise HTTPException(status_code=404, detail="Session not found")
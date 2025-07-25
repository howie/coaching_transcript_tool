import io
import logging
from typing import Optional

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import StreamingResponse

from coaching_assistant.core import format_transcript

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Coaching Transcript Tool API",
    description="An API to format coaching transcript files (VTT) into Markdown or Excel.",
    version="1.0.0",
)

@app.get("/")
def read_root():
    """Root endpoint providing a welcome message."""
    return {"message": "Welcome to the Coaching Transcript Tool API!"}

@app.post("/format")
async def format_transcript_endpoint(
    file: UploadFile = File(..., description="The VTT transcript file to process."),
    output_format: str = Form("markdown", description="The desired output format ('markdown' or 'excel')."),
    coach_name: Optional[str] = Form(None, description="Name of the coach to be replaced with 'Coach'."),
    client_name: Optional[str] = Form(None, description="Name of the client to be replaced with 'Client'."),
    convert_to_traditional_chinese: bool = Form(False, description="Convert Simplified Chinese to Traditional Chinese."),
):
    """
    Receives a VTT file, processes it, and returns the formatted version.
    """
    logger.info(
        f"Received request to format '{file.filename}' to '{output_format}'."
    )
    try:
        file_content = await file.read()

        try:
            content_str = file_content.decode('utf-8')
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="File is not valid UTF-8.")

        result = format_transcript(
            file_content=content_str,
            output_format=output_format,
            coach_name=coach_name,
            client_name=client_name,
            convert_to_traditional_chinese=convert_to_traditional_chinese,
        )

        filename = file.filename or "output"
        
        if output_format.lower() == 'excel':
            output_filename = f"{filename.rsplit('.', 1)[0]}.xlsx"
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            content_stream = result
        elif output_format.lower() == 'markdown':
            output_filename = f"{filename.rsplit('.', 1)[0]}.md"
            media_type = "text/markdown; charset=utf-8"
            content_stream = io.BytesIO(result.encode('utf-8'))
        else:
            raise HTTPException(status_code=400, detail="Invalid output format specified.")

        logger.info(f"Successfully formatted file. Preparing response as {output_filename}.")

        return StreamingResponse(
            content_stream,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={output_filename}"}
        )

    except Exception as e:
        logger.exception(f"Error processing file {file.filename}:")
        raise HTTPException(status_code=500, detail=str(e))

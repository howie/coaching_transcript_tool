"""
Format transcript routes for the Coaching Transcript Tool Backend API.

重構後的檔案處理 API，改進了錯誤處理和日誌記錄。
"""

import io
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, StreamingResponse

from ..core.processor import format_transcript
from ..parser import UnrecognizedFormatError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def format_root():
    """格式化 API 根端點"""
    return {"message": "Coaching Transcript Tool Format API v2.0"}


@router.get("/openai.json")
async def get_openai_schema():
    """
    提供 OpenAI plugin schema 檔案供 Custom GPT 使用。
    """
    file_path = Path(__file__).parent.parent / "static" / "openai.json"
    if not file_path.exists():
        logger.error(f"OpenAI schema file not found at {file_path}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="OpenAI schema file not found",
        )
    return FileResponse(file_path, media_type="application/json")


@router.post("/format")
async def format_transcript_endpoint(
    file: UploadFile = File(..., description="The VTT transcript file to process."),
    output_format: str = Form(
        "markdown",
        description="The desired output format ('markdown' or 'excel').",
    ),
    coach_name: Optional[str] = Form(
        None, description="Name of the coach to be replaced with 'Coach'."
    ),
    client_name: Optional[str] = Form(
        None, description="Name of the client to be replaced with 'Client'."
    ),
    convert_to_traditional_chinese: bool = Form(
        False, description="Convert Simplified Chinese to Traditional Chinese."
    ),
):
    """
    接收 VTT 檔案，處理並回傳格式化的版本。

    重構後改進：
    - 更好的錯誤處理和日誌記錄
    - 統一的回應格式
    - 增強的檔案驗證
    """
    logger.info(
        f"Received format request - file: '{file.filename}', "
        f"format: '{output_format}', coach: '{coach_name}', "
        f"client: '{client_name}', "
        f"traditional: {convert_to_traditional_chinese}"
    )

    try:
        # 檔案大小檢查
        if file.size and file.size > 50 * 1024 * 1024:  # 50MB limit
            raise HTTPException(
                status_code=413, detail="File too large. Maximum size is 50MB."
            )

        # 檔案類型檢查
        if file.content_type and not file.content_type.startswith("text/"):
            logger.warning(f"Potentially unsupported content type: {file.content_type}")

        file_content = await file.read()

        if not file_content:
            raise HTTPException(status_code=400, detail="Empty file uploaded")

        result = format_transcript(
            file_content=file_content,
            original_filename=file.filename,
            output_format=output_format,
            coach_name=coach_name,
            client_name=client_name,
            convert_to_traditional_chinese=convert_to_traditional_chinese,
        )

        filename = file.filename or "transcript"
        base_filename = filename.rsplit(".", 1)[0] if "." in filename else filename

        # 清理檔案名稱，移除可能導致問題的字符
        import re

        safe_filename = re.sub(r"[^\w\-_]", "_", base_filename)

        if output_format.lower() == "excel":
            output_filename = f"{safe_filename}.xlsx"
            media_type = (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            content_stream = io.BytesIO(result)
        elif output_format.lower() == "markdown":
            output_filename = f"{safe_filename}.md"
            media_type = "text/markdown; charset=utf-8"
            content_stream = io.BytesIO(result.encode("utf-8"))
        else:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid output format '{output_format}'. "
                    "Supported formats: 'markdown', 'excel'"
                ),
            )

        logger.info(
            f"Successfully processed file '{file.filename}' -> '{output_filename}'"
        )

        return StreamingResponse(
            content_stream,
            media_type=media_type,
            headers={
                "Content-Disposition": (f"attachment; filename={output_filename}")
            },
        )

    except UnrecognizedFormatError as e:
        logger.warning(f"Unrecognized format error for file '{file.filename}': {e}")
        raise HTTPException(status_code=400, detail=f"Unrecognized file format: {e}")
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.exception(f"Unexpected error processing file '{file.filename}':")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while processing file: {str(e)}",
        )

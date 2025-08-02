from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from ..models.message import ChatMessage
from ..services.langchain_service import chain_with_history
from ..services.auth_service import get_current_user
from ..services.firebase_service import db
import json
import logging
import traceback

router = APIRouter()

async def stream_generator(response_stream):
    """
    Standard stream generator.
    """
    try:
        async for chunk in response_stream:
            content = chunk.content
            if content:
                yield f"data: {json.dumps({'content': content})}\n\n"
    except Exception:
        tb_str = traceback.format_exc()
        logging.error(f"BACKEND: An exception occurred during stream generation:\n{tb_str}")

@router.post("/message")
async def stream_chat_message(
    chat_message: ChatMessage,
    current_user: dict = Depends(get_current_user)
):
    conversation_id = chat_message.conversation_id
    user_id = current_user.get('uid')
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Could not identify user from token.")

    conv_ref = db.collection("conversations").document(conversation_id)
    conv_doc = conv_ref.get()

    if not conv_doc.exists or conv_doc.to_dict().get("user_id") != user_id:
        raise HTTPException(status_code=404, detail="Conversation not found or access denied")

    # The config now requires both 'session_id' and 'user_id'
    config = {
        "configurable": {
            "session_id": conversation_id,
            "user_id": user_id
        }
    }
    
    try:
        response_stream = chain_with_history.astream(
            {"question": chat_message.message},
            config=config,
        )
        return StreamingResponse(stream_generator(response_stream), media_type="text/event-stream")
    except Exception as e:
        logging.error(f"BACKEND: Error calling chain_with_history.astream: {e}")
        raise HTTPException(status_code=500, detail=f"Error initiating chat stream: {e}")

from fastapi import APIRouter, WebSocket, Request, Response, Depends
from app.services.orchestrator import StreamOrchestrator
from app.services.config_service import ConfigService

router = APIRouter()
config_service = ConfigService()

@router.post("/incoming")
async def incoming_call_webhook(request: Request):
    form_data = await request.form()
    
    # Check if this is an Outbound call response
    # When we dial out, we passed params in the URL. Twilio preserves these.
    # However, for the initial TwiML request, we might need to parse query params if Twilio passes them back, 
    # OR we just inspect the 'Direction' param form Twilio.
    
    # Twilio sends Query Params to the webhook if they were in the URL
    query_params = request.query_params
    
    direction = query_params.get("direction", "inbound")
    campaign_id = query_params.get("campaign_id")
    customer_name = query_params.get("customer_name")
    
    # Detection results
    answered_by = form_data.get("AnsweredBy") # human, machine_start, etc.
    
    host = request.headers.get("host")
    
    # Pass metadata to WebSocket via URL params
    stream_url = (
        f"wss://{host}/api/v1/voice/stream"
        f"?direction={direction}"
        f"&answered_by={answered_by}"
        f"&customer_name={customer_name}"
    )
    
    # TwiML
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Connect>
            <Stream url="{stream_url}" />
        </Connect>
    </Response>
    """
    return Response(content=twiml, media_type="application/xml")

@router.websocket("/stream")
async def websocket_stream(websocket: WebSocket, direction: str = "inbound", answered_by: str = None, customer_name: str = None, phone_number: str = None):
    """
    1. Accept WS.
    2. Fetch Config for 'phone_number'.
    3. Start Orchestrator.
    """
    await websocket.accept()
    
    # 1. Fetch Config
    agent_config = await config_service.get_agent_config(phone_number)
    
    if not agent_config:
        # Graceful failure: Speak error and close
        # Note: In raw WS, we can't easily speak without the orchestrator, 
        # so we just close with a log in this phase.
        await websocket.close(code=4000, reason="Agent not configured")
        return
    agent_config['call_context'] = {
        "direction": direction,
        "answered_by": answered_by,
        "customer_name": customer_name
    }

    # 2. Initialize Orchestrator with Config
    orchestrator = StreamOrchestrator(websocket, agent_config)
    await orchestrator.handle_stream()
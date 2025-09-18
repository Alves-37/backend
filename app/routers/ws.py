from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.realtime import manager

router = APIRouter(prefix="/ws", tags=["ws"])

@router.websocket("")
async def websocket_endpoint(websocket: WebSocket):
    # Futuro: validar token via query params: token = websocket.query_params.get("token")
    await manager.connect(websocket)
    try:
        while True:
            # Mantém a conexão viva; receber mensagens do cliente (pings) se houver
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception:
        await manager.disconnect(websocket)

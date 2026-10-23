@app.get("/")
async def root():
    return {"status": "success", "message": "KoolBot Backend is Running Smoothly!"}
@app.get("/")
async def root():
    return {"status": "success", "message": "KoolBot Backend is Running Smoothly!"}
import asyncio
import base64
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from playwright.async_api import async_playwright

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions = {}

async def capture_screenshot(page):
    screenshot_bytes = await page.screenshot(type="jpeg", quality=60)
    return base64.b64encode(screenshot_bytes).decode("utf-8")

@app.websocket("/ws/property-listing/{session_id}")
async def property_listing_ws(websocket: WebSocket, session_id: str):
    await websocket.accept()
    sessions[session_id] = {"status": "running", "paused": False, "user_input": None}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 720})
        page = await context.new_page()

        try:
            await websocket.send_json({"type": "log", "message": "Opening Property Portal..."})
            await page.goto("https://www.olx.in/post", wait_until="domcontentloaded")
            
            img_data = await capture_screenshot(page)
            await websocket.send_json({"type": "screenshot", "image": img_data})

            await websocket.send_json({
                "type": "human_input_required",
                "message": "Enter your Phone Number to continue login:"
            })

            while sessions[session_id]["user_input"] is None:
                if sessions[session_id]["status"] == "stopped":
                    await websocket.send_json({"type": "log", "message": "Stopped by user."})
                    await browser.close()
                    return
                await asyncio.sleep(0.5)

            phone = sessions[session_id]["user_input"]
            sessions[session_id]["user_input"] = None

            await page.fill('input[type="tel"]', phone)
            await asyncio.sleep(1)
            
            img_data = await capture_screenshot(page)
            await websocket.send_json({"type": "screenshot", "image": img_data})

        except Exception as e:
            await websocket.send_json({"type": "error", "message": str(e)})
        finally:
            await browser.close()

@app.post("/api/stop/{session_id}")
async def stop_session(session_id: str):
    if session_id in sessions:
        sessions[session_id]["status"] = "stopped"
        return {"status": "success", "message": "Session stopped"}
    return {"status": "error", "message": "Session not found"}

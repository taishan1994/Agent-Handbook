import asyncio
import json
import uuid
from fastapi import FastAPI, BackgroundTasks, Form
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from flow import create_article_flow

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Store active jobs and their SSE queues
active_jobs = {}

def run_article_workflow(job_id: str, topic: str):
    """Run the article workflow in background"""
    try:
        # Get the pre-created queue from active_jobs
        sse_queue = active_jobs[job_id]
        shared = {
            "topic": topic,
            "sse_queue": sse_queue,
            "sections": [],
            "draft": "",
            "final_article": ""
        }
        
        # Run the workflow
        flow = create_article_flow()
        flow.run(shared)
        
    except Exception as e:
        # Send error message
        error_msg = {"step": "error", "progress": 0, "data": {"error": str(e)}}
        if job_id in active_jobs:
            active_jobs[job_id].put_nowait(error_msg)

@app.post("/start-job")
async def start_job(background_tasks: BackgroundTasks, topic: str = Form(...)):
    """Start a new article generation job"""
    job_id = str(uuid.uuid4())
    
    # Create SSE queue and register job immediately
    sse_queue = asyncio.Queue()
    active_jobs[job_id] = sse_queue
    
    # Start background task
    background_tasks.add_task(run_article_workflow, job_id, topic)
    
    return {"job_id": job_id, "topic": topic, "status": "started"}

@app.get("/progress/{job_id}")
async def get_progress(job_id: str):
    """Stream progress updates via SSE"""
    
    async def event_stream():
        if job_id not in active_jobs:
            yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
            return
            
        sse_queue = active_jobs[job_id]
        
        # Send initial connection confirmation
        yield f"data: {json.dumps({'step': 'connected', 'progress': 0, 'data': {'message': 'Connected to job progress'}})}\n\n"
        
        try:
            while True:
                # Wait for next progress update
                try:
                    # Use asyncio.wait_for to avoid blocking forever
                    progress_msg = await asyncio.wait_for(sse_queue.get(), timeout=1.0)
                    yield f"data: {json.dumps(progress_msg)}\n\n"
                    
                    # If job is complete, clean up and exit
                    if progress_msg.get("step") == "complete":
                        del active_jobs[job_id]
                        break
                        
                except asyncio.TimeoutError:
                    # Send heartbeat to keep connection alive
                    yield f"data: {json.dumps({'heartbeat': True})}\n\n"
                    
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )

@app.get("/")
async def get_index():
    """Serve the main page"""
    return FileResponse("static/index.html")

@app.get("/progress.html")
async def get_progress_page():
    """Serve the progress page"""
    return FileResponse("static/progress.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import cv2
import numpy as np
from PIL import Image
import io
import base64
import time
from pathlib import Path

from models.yolo_loader import YOLOModel
from services.graph_builder import GraphBuilder
from services.stride_analyzer import StrideAnalyzer
from schemas.api_models import InferenceResponse, Metadata

# Initialize FastAPI app
app = FastAPI(
    title="AutoStride API",
    description="API for architectural diagram analysis with YOLO and STRIDE threat modeling",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
graph_builder = GraphBuilder()
stride_analyzer = StrideAnalyzer()

# Initialize YOLO model manager on startup
YOLOModel.initialize()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "AutoStride API", "version": "1.0.0"}


@app.get("/api/v1/models")
async def list_models():
    """List available YOLO models."""
    return {
        "available_models": YOLOModel.get_available_models(),
        "default_model": YOLOModel.get_default_model(),
    }


@app.post("/api/v1/inference", response_model=InferenceResponse)
async def inference(
    file: UploadFile = File(..., description="Architecture diagram image"),
    conf_threshold: float = Query(
        0.5, ge=0.1, le=1.0, description="Confidence threshold for detections"
    ),
    include_visualization: bool = Query(
        False, description="Include visualization image in response"
    ),
    model_name: Optional[str] = Query(
        None,
        description="YOLO model to use (e.g., 'yolo11m-pose_manual_v3_v1'). If not specified, uses default model.",
    ),
):
    """
    Process an architecture diagram and return graph + STRIDE analysis.

    Args:
        file: Uploaded image file (PNG, JPG, JPEG)
        conf_threshold: Detection confidence threshold (0.1 to 1.0)
        include_visualization: Whether to include visualization with detections
        model_name: Name of YOLO model to use. If None, uses default model.

    Returns:
        InferenceResponse with graph, STRIDE analysis, and metadata
    """
    start_time = time.time()

    # Validate file type
    if not file.content_type in ["image/png", "image/jpeg", "image/jpg"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}. Only PNG, JPG, and JPEG are supported.",
        )

    # Validate file size (10 MB limit)
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 10 MB limit")

    try:
        # Convert uploaded file to image
        image = Image.open(io.BytesIO(contents))

        # Convert RGBA to RGB if necessary
        if image.mode == "RGBA":
            # Create a white background
            background = Image.new("RGB", image.size, (255, 255, 255))
            # Paste the image on the background using alpha channel as mask
            background.paste(image, mask=image.split()[3])  # 3 is the alpha channel
            image = background
        elif image.mode != "RGB":
            # Convert any other mode to RGB
            image = image.convert("RGB")

        image_np = np.array(image)

        # Convert RGB to BGR for OpenCV compatibility (YOLO expects BGR)
        if len(image_np.shape) == 3 and image_np.shape[2] == 3:
            image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

        print(
            f"DEBUG: Image shape after conversion: {image_np.shape}, dtype: {image_np.dtype}"
        )

        # Run YOLO inference with selected model
        yolo_results = YOLOModel.predict(
            image_np, conf_threshold=conf_threshold, model_name=model_name
        )

        # Build graph from detections
        graph = graph_builder.build_graph(yolo_results)

        # Perform STRIDE analysis
        stride_analysis = stride_analyzer.analyze(graph)

        # Generate visualization if requested
        visualization = None
        if include_visualization:
            # Plot YOLO results
            im_array = yolo_results.plot()
            # Convert BGR to RGB
            im_array = cv2.cvtColor(im_array, cv2.COLOR_BGR2RGB)
            # Convert to PIL Image
            pil_img = Image.fromarray(im_array)
            # Encode to base64
            buffered = io.BytesIO()
            pil_img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            visualization = f"data:image/png;base64,{img_str}"

        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000  # in milliseconds

        # Count total detections
        total_detections = len(graph.nodes) + len(graph.edges)

        # Create metadata
        used_model = model_name if model_name else YOLOModel.get_default_model()
        metadata = Metadata(
            processing_time_ms=round(processing_time, 2),
            model_version=used_model,
            total_detections=total_detections,
            confidence_threshold=conf_threshold,
        )

        # Create response
        response = InferenceResponse(
            graph=graph,
            stride_analysis=stride_analysis,
            metadata=metadata,
            visualization=visualization,
        )

        return response

    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"Model file not found: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "AutoStride API - Architectural Threat Modeling",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "models": "/api/v1/models",
            "inference": "/api/v1/inference",
            "docs": "/docs",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

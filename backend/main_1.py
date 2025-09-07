from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import numpy as np
from dotenv import load_dotenv
from qdrant_client import QdrantClient
import tempfile
import librosa
from PIL import Image
import torch
import torch.nn as nn
from torchvision import models, transforms
from openai import OpenAI
import pickle
from transformers import Wav2Vec2Processor, Wav2Vec2Model

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Multi-Modal Bird Search API",
    description="Search for birds using audio, images, or text descriptions",
    version="1.0.0"
)

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize clients
qdrant_client = QdrantClient(
    url=os.getenv('QDRANT_ENDPOINT'),
    api_key=os.getenv('QDRANT_API_KEY'),
)

openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Initialize image model (ResNet50)
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
image_model = models.resnet50(pretrained=True)
image_model = nn.Sequential(*list(image_model.children())[:-1])
image_model.eval()
image_model.to(device)

# Image preprocessing
image_transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

processor = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base")
model = Wav2Vec2Model.from_pretrained("facebook/wav2vec2-base")

# Audio feature extraction
def extract_audio_features(audio_path: str) -> np.ndarray:
    # Load audio at 16kHz (Wav2Vec2 requirement)
    audio, sr = librosa.load(audio_path, sr=16000)
    
    # Get wav2vec features
    inputs = processor(audio, sampling_rate=16000, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**inputs)
        features = torch.mean(outputs.last_hidden_state, dim=1).squeeze().numpy()
    
    return features

# Pydantic models
class SearchRequest(BaseModel):
    query: str
    limit: int = 10

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    total_found: int
    search_type: str

class BirdInfo(BaseModel):
    bird_id: int
    species_name: str
    scientific_name: Optional[str]
    family: Optional[str]
    confidence_score: float

# API Endpoints

@app.get("/")
async def root():
    """API health check"""
    return {"message": "Multi-Modal Bird Search API", "status": "active"}

@app.get("/collections/status")
async def get_collections_status():
    """Get status of all Qdrant collections"""
    try:
        collections = ["bird_audio_search", "bird_image_search", "bird_text_search"]
        status = {}
        
        for collection_name in collections:
            try:
                info = qdrant_client.get_collection(collection_name)
                status[collection_name] = {
                    "status": "active",
                    "points_count": info.points_count,
                    "vector_size": info.config.params.vectors.size
                }
            except Exception as e:
                status[collection_name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking collections: {str(e)}")

@app.post("/search/text")
async def search_by_text(request: SearchRequest):
    """Search birds by text description"""
    try:
        # Generate embedding for the text query
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=request.query
        )
        query_vector = response.data[0].embedding
        
        # Search in Qdrant
        results = qdrant_client.search(
            collection_name="bird_text_search",
            query_vector=query_vector,
            limit=request.limit
        )
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                "bird_id": result.payload.get("bird_id"),
                "species_name": result.payload.get("species_name"),
                "scientific_name": result.payload.get("scientific_name"),
                "family": result.payload.get("family"),
                "confidence_score": float(result.score),
                "data_completeness": result.payload.get("data_completeness"),
                "searchable_text": result.payload.get("searchable_text", "")[:200] + "..."
            })
        
        return SearchResponse(
            results=formatted_results,
            total_found=len(results),
            search_type="text"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text search error: {str(e)}")

@app.post("/search/image")
async def search_by_image(file: UploadFile = File(...), limit: int = Query(10)):
    """Search birds by uploaded image"""
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Load and preprocess image
            image = Image.open(tmp_file_path).convert('RGB')
            image_tensor = image_transform(image).unsqueeze(0).to(device)
            
            # Extract features
            with torch.no_grad():
                features = image_model(image_tensor)
                features = features.view(features.size(0), -1).squeeze().cpu().numpy()
            
            # Search in Qdrant
            results = qdrant_client.search(
                collection_name="bird_image_search",
                query_vector=features.tolist(),
                limit=limit
            )
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "bird_id": result.payload.get("bird_id"),
                    "species_name": result.payload.get("species_name"),
                    "image_path": result.payload.get("image_path"),
                    "source_url": result.payload.get("source_url"),
                    "quality_score": result.payload.get("quality_score"),
                    "confidence_score": float(result.score),
                    "width": result.payload.get("width"),
                    "height": result.payload.get("height")
                })
            
            return SearchResponse(
                results=formatted_results,
                total_found=len(results),
                search_type="image"
            )
            
        finally:
            # Clean up temporary file
            os.unlink(tmp_file_path)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image search error: {str(e)}")

@app.post("/search/audio")
async def search_by_audio(file: UploadFile = File(...), limit: int = Query(10)):
    """Search birds by uploaded audio file"""
    try:
        # Validate file type
        if not file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="File must be an audio file")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Extract audio features
            features = extract_audio_features(tmp_file_path)
            
            # Search in Qdrant
            results = qdrant_client.search(
                collection_name="bird_audio_search",
                query_vector=features.tolist(),
                limit=limit
            )
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "bird_id": result.payload.get("bird_id"),
                    "species_name": result.payload.get("species_name"),
                    "clip_path": result.payload.get("clip_path"),
                    "clip_duration": result.payload.get("clip_duration"),
                    "confidence_score": float(result.score),
                    "feature_type": result.payload.get("feature_type"),
                    "audio_quality": result.payload.get("audio_quality")
                })
            
            return SearchResponse(
                results=formatted_results,
                total_found=len(results),
                search_type="audio"
            )
            
        finally:
            # Clean up temporary file
            os.unlink(tmp_file_path)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio search error: {str(e)}")

@app.get("/search/cross-modal/{bird_id}")
async def cross_modal_search(bird_id: int, limit: int = Query(5)):
    """Find similar birds across all modalities for a given bird_id"""
    try:
        results = {}
        
        # Search in each collection by bird_id
        collections = ["bird_audio_search", "bird_image_search", "bird_text_search"]
        
        for collection_name in collections:
            try:
                # Find the bird in this collection
                bird_results = qdrant_client.scroll(
                    collection_name=collection_name,
                    scroll_filter={
                        "must": [
                            {
                                "key": "bird_id",
                                "match": {"value": bird_id}
                            }
                        ]
                    },
                    limit=1
                )
                
                if bird_results[0]:  # If bird found
                    target_vector = bird_results[0][0].vector
                    
                    # Search for similar birds
                    similar_results = qdrant_client.search(
                        collection_name=collection_name,
                        query_vector=target_vector,
                        limit=limit
                    )
                    
                    # Format results
                    modality = collection_name.replace("bird_", "").replace("_search", "")
                    results[modality] = []
                    
                    for result in similar_results:
                        results[modality].append({
                            "bird_id": result.payload.get("bird_id"),
                            "species_name": result.payload.get("species_name"),
                            "confidence_score": float(result.score),
                            **result.payload  # Include all metadata
                        })
                        
            except Exception as e:
                results[collection_name] = {"error": str(e)}
        
        return {
            "target_bird_id": bird_id,
            "cross_modal_results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cross-modal search error: {str(e)}")

@app.get("/bird/{bird_id}")
async def get_bird_info(bird_id: int):
    """Get comprehensive information about a specific bird"""
    try:
        bird_info = {}
        
        collections = ["bird_audio_search", "bird_image_search", "bird_text_search"]
        
        for collection_name in collections:
            try:
                results = qdrant_client.scroll(
                    collection_name=collection_name,
                    scroll_filter={
                        "must": [
                            {
                                "key": "bird_id", 
                                "match": {"value": bird_id}
                            }
                        ]
                    },
                    limit=10  # Get all instances of this bird
                )
                
                modality = collection_name.replace("bird_", "").replace("_search", "")
                bird_info[modality] = []
                
                for point in results[0]:
                    bird_info[modality].append(point.payload)
                    
            except Exception as e:
                bird_info[collection_name] = {"error": str(e)}
        
        if not any(bird_info.values()):
            raise HTTPException(status_code=404, detail=f"Bird with ID {bird_id} not found")
        
        return {
            "bird_id": bird_id,
            "modalities": bird_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving bird info: {str(e)}")

@app.get("/stats")
async def get_database_stats():
    """Get statistics about the bird database"""
    try:
        stats = {}
        collections = ["bird_audio_search", "bird_image_search", "bird_text_search"]
        
        for collection_name in collections:
            try:
                info = qdrant_client.get_collection(collection_name)
                modality = collection_name.replace("bird_", "").replace("_search", "")
                stats[modality] = {
                    "total_points": info.points_count,
                    "vector_dimensions": info.config.params.vectors.size,
                    "status": info.status
                }
            except Exception as e:
                stats[collection_name] = {"error": str(e)}
        
        return {
            "database_stats": stats,
            "total_collections": len([s for s in stats.values() if "error" not in s])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
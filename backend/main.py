from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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
    description="Search for birds using audio, images, or text descriptions with comprehensive results",
    version="1.0.0"
)

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for audio only (images use Wikimedia URLs)
app.mount("/audio", StaticFiles(directory="../clips_10sec"), name="audio")

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
    audio, sr = librosa.load(audio_path, sr=16000)
    inputs = processor(audio, sampling_rate=16000, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**inputs)
        features = torch.mean(outputs.last_hidden_state, dim=1).squeeze().numpy()
    return features

def get_all_text_data():
    """Get all text data from collection"""
    try:
        results = qdrant_client.scroll(
            collection_name="bird_text_search",
            limit=100,
            with_payload=True,
            with_vectors=False
        )
        return {point.payload.get("bird_id"): point.payload for point in results[0]}
    except Exception as e:
        print(f"Error getting all text data: {e}")
        return {}

def get_all_image_data():
    """Get all image data from collection"""
    try:
        results = qdrant_client.scroll(
            collection_name="bird_image_search",
            limit=1000,
            with_payload=True,
            with_vectors=False
        )
        image_data = {}
        for point in results[0]:
            bird_id = point.payload.get("bird_id")
            if bird_id not in image_data:
                image_data[bird_id] = []
            image_data[bird_id].append(point.payload)
        return image_data
    except Exception as e:
        print(f"Error getting all image data: {e}")
        return {}

def get_all_audio_data():
    """Get all audio data from collection"""
    try:
        results = qdrant_client.scroll(
            collection_name="bird_audio_search",
            limit=1000,
            with_payload=True,
            with_vectors=False
        )
        audio_data = {}
        for point in results[0]:
            bird_id = point.payload.get("bird_id")
            if bird_id not in audio_data:
                audio_data[bird_id] = []
            # Add audio URL
            payload = point.payload.copy()
            if payload.get("clip_path"):
                filename = payload["clip_path"].split("\\")[-1].split("/")[-1]
                payload["audio_url"] = f"http://localhost:8000/audio/{filename}"
            audio_data[bird_id].append(payload)
        return audio_data
    except Exception as e:
        print(f"Error getting all audio data: {e}")
        return {}

# Cache data on startup
print("Loading all data into memory...")
ALL_TEXT_DATA = get_all_text_data()
ALL_IMAGE_DATA = get_all_image_data()
ALL_AUDIO_DATA = get_all_audio_data()
print(f"Loaded {len(ALL_TEXT_DATA)} text records, {len(ALL_IMAGE_DATA)} image groups, {len(ALL_AUDIO_DATA)} audio groups")

def create_comprehensive_result(search_result, search_type: str) -> Dict[str, Any]:
    """Create comprehensive result using cached data"""
    bird_id = search_result.payload.get("bird_id")
    if bird_id is None:
        return None
    
    # Get data from cache
    text_info = ALL_TEXT_DATA.get(bird_id, {})
    images = ALL_IMAGE_DATA.get(bird_id, [])
    audio_clips = ALL_AUDIO_DATA.get(bird_id, [])
    
    return {
        "bird_id": bird_id,
        "species_name": search_result.payload.get("species_name") or text_info.get("species_name", "Unknown"),
        "scientific_name": text_info.get("scientific_name", ""),
        "family": text_info.get("family", ""),
        "confidence_score": float(search_result.score),
        "search_match_type": search_type,
        
        # Raw text information for LLM processing
        "text_description": text_info.get("searchable_text", ""),
        "raw_text_data": text_info,  # Complete raw text data
        
        # Basic extracted fields (you can enhance with LLM later)
        "habitats": "",
        "geographic_regions": "",
        "size": text_info.get("size", ""),
        "ecology": "",
        "group_dynamics": "",
        "extract": "",
        "url": f"https://en.wikipedia.org/wiki/{text_info.get('species_name', '').replace(' ', '_')}" if text_info.get("species_name") else "",
        
        # Media data
        "images": images,
        "primary_image": images[0] if images else None,
        "audio_clips": audio_clips,
        "primary_audio": audio_clips[0] if audio_clips else None
    }

# Pydantic models
class SearchRequest(BaseModel):
    query: str
    limit: int = 12

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    total_found: int
    search_type: str

# API Endpoints
@app.get("/")
async def root():
    return {"message": "Multi-Modal Bird Search API", "status": "active"}

@app.get("/collections/status")
async def get_collections_status():
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
                status[collection_name] = {"status": "error", "error": str(e)}
        
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking collections: {str(e)}")

@app.get("/refresh-cache")
async def refresh_cache():
    """Refresh cached data"""
    global ALL_TEXT_DATA, ALL_IMAGE_DATA, ALL_AUDIO_DATA
    ALL_TEXT_DATA = get_all_text_data()
    ALL_IMAGE_DATA = get_all_image_data()
    ALL_AUDIO_DATA = get_all_audio_data()
    return {
        "message": "Cache refreshed",
        "counts": {
            "text": len(ALL_TEXT_DATA),
            "images": len(ALL_IMAGE_DATA),
            "audio": len(ALL_AUDIO_DATA)
        }
    }

@app.post("/search/text")
async def search_by_text(request: SearchRequest):
    """Search birds by text description"""
    try:
        # Generate embedding
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=request.query
        )
        query_vector = response.data[0].embedding
        
        # Search in text collection
        results = qdrant_client.search(
            collection_name="bird_text_search",
            query_vector=query_vector,
            limit=request.limit
        )
        
        # Create comprehensive results
        comprehensive_results = []
        for result in results:
            comprehensive_result = create_comprehensive_result(result, "text")
            if comprehensive_result:
                comprehensive_results.append(comprehensive_result)
        
        return SearchResponse(
            results=comprehensive_results,
            total_found=len(comprehensive_results),
            search_type="text"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text search error: {str(e)}")

@app.post("/search/audio")
async def search_by_audio(file: UploadFile = File(...), limit: int = Query(12)):
    """Search birds by uploaded audio file"""
    try:
        if not file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="File must be an audio file")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Extract audio features
            features = extract_audio_features(tmp_file_path)
            
            # Search in audio collection
            results = qdrant_client.search(
                collection_name="bird_audio_search",
                query_vector=features.tolist(),
                limit=limit
            )
            
            # Create comprehensive results
            comprehensive_results = []
            for result in results:
                comprehensive_result = create_comprehensive_result(result, "audio")
                if comprehensive_result:
                    comprehensive_results.append(comprehensive_result)
            
            return SearchResponse(
                results=comprehensive_results,
                total_found=len(comprehensive_results),
                search_type="audio"
            )
            
        finally:
            os.unlink(tmp_file_path)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio search error: {str(e)}")

@app.get("/bird/{bird_id}")
async def get_bird_info(bird_id: int):
    """Get comprehensive information about a specific bird"""
    try:
        text_info = ALL_TEXT_DATA.get(bird_id, {})
        images = ALL_IMAGE_DATA.get(bird_id, [])
        audio_clips = ALL_AUDIO_DATA.get(bird_id, [])
        
        if not any([text_info, images, audio_clips]):
            raise HTTPException(status_code=404, detail=f"Bird with ID {bird_id} not found")
        
        return {
            "bird_id": bird_id,
            "species_name": text_info.get("species_name", "Unknown"),
            "scientific_name": text_info.get("scientific_name", ""),
            "family": text_info.get("family", ""),
            "text_information": text_info,
            "raw_text_data": text_info,
            "images": images,
            "audio_clips": audio_clips,
            "counts": {
                "images": len(images),
                "audio_clips": len(audio_clips)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving bird info: {str(e)}")

@app.post("/enhance-description")
async def enhance_description(request: dict):
    """Use LLM to enhance bird description"""
    try:
        raw_text = request.get("raw_text_data", {})
        searchable_text = raw_text.get("searchable_text", "")
        
        if not searchable_text:
            return {"enhanced_description": "No text data available for enhancement"}
        
        # Use OpenAI to create a structured summary
        prompt = f"""
        Extract and format the following bird information from this raw data:
        
        Raw data: {searchable_text}
        
        provide a summary of the data in 100 words. Don't add unnecessary information other than bird's details.
        
        Format as a readable paragraph for each section.
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000
        )
        
        return {"enhanced_description": response.choices[0].message.content}
        
    except Exception as e:
        return {"enhanced_description": f"Error enhancing description: {str(e)}"}

@app.get("/stats")
async def get_database_stats():
    """Get database statistics"""
    try:
        return {
            "database_stats": {
                "text": {"total_points": len(ALL_TEXT_DATA), "status": "loaded"},
                "image": {"total_points": len(ALL_IMAGE_DATA), "status": "loaded"},
                "audio": {"total_points": len(ALL_AUDIO_DATA), "status": "loaded"}
            },
            "total_collections": 3
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")

def get_unique_birds_from_results(results, search_type: str) -> List[Dict[str, Any]]:
    """Get unique birds from search results, avoiding duplicates"""
    seen_bird_ids = set()
    unique_results = []
    
    for result in results:
        bird_id = result.payload.get("bird_id")
        if bird_id is not None and bird_id not in seen_bird_ids:
            seen_bird_ids.add(bird_id)
            comprehensive_result = create_comprehensive_result(result, search_type)
            if comprehensive_result:
                unique_results.append(comprehensive_result)
    
    return unique_results

@app.post("/search/image")
async def search_by_image(file: UploadFile = File(...), limit: int = Query(12)):
    """Search birds by uploaded image"""
    try:
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Process image
            image = Image.open(tmp_file_path).convert('RGB')
            image_tensor = image_transform(image).unsqueeze(0).to(device)
            
            with torch.no_grad():
                features = image_model(image_tensor)
                features = features.view(features.size(0), -1).squeeze().cpu().numpy()
            
            # Search in image collection - get more results to account for duplicates
            results = qdrant_client.search(
                collection_name="bird_image_search",
                query_vector=features.tolist(),
                limit=limit * 5  # Get more since we'll deduplicate
            )
            
            # Get unique birds only
            comprehensive_results = get_unique_birds_from_results(results, "image")
            
            # Limit to requested amount
            comprehensive_results = comprehensive_results[:limit]
            
            return SearchResponse(
                results=comprehensive_results,
                total_found=len(comprehensive_results),
                search_type="image"
            )
            
        finally:
            os.unlink(tmp_file_path)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image search error: {str(e)}")
    
@app.get("/birds/all")
async def get_all_birds():
    """Get all 88 bird records with comprehensive information"""
    try:
        all_birds = []
        
        # Iterate through all cached text data (which contains all 88 birds)
        for bird_id, text_info in ALL_TEXT_DATA.items():
            # Get associated media data
            images = ALL_IMAGE_DATA.get(bird_id, [])
            audio_clips = ALL_AUDIO_DATA.get(bird_id, [])
            
            # Create comprehensive result (same structure as search results)
            bird_record = {
                "bird_id": bird_id,
                "species_name": text_info.get("species_name", "Unknown"),
                "scientific_name": text_info.get("scientific_name", ""),
                "family": text_info.get("family", ""),
                
                # Raw text information
                "text_description": text_info.get("searchable_text", ""),
                "raw_text_data": text_info,
                
                # Basic fields
                "size": text_info.get("size", ""),
                "url": f"https://en.wikipedia.org/wiki/{text_info.get('species_name', '').replace(' ', '_')}" if text_info.get("species_name") else "",
                
                # Media data
                "images": images,
                "primary_image": images[0] if images else None,
                "audio_clips": audio_clips,
                "primary_audio": audio_clips[0] if audio_clips else None
            }
            
            all_birds.append(bird_record)
        
        return {
            "results": all_birds,
            "total_found": len(all_birds),
            "search_type": "all_records"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching all birds: {str(e)}")
        
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
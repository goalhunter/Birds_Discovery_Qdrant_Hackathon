"""
CrewAI Wikimedia Commons Bird Image Collector
Smart multi-agent system to find and download bird images from Wikimedia Commons
"""

import requests
import json
import pickle
import pandas as pd
from pathlib import Path
import time
from PIL import Image
import io
from urllib.parse import unquote
from crewai import Agent, Task, Crew

class WikimediaBirdImageCollector:
    """Intelligent bird image collection from Wikimedia Commons"""
    
    def __init__(self):
        self.base_url = "https://commons.wikimedia.org/w/api.php"
        self.output_dir = Path("bird_images_wikimedia")
        self.output_dir.mkdir(exist_ok=True)
        
        # Create CrewAI agents
        self.agents = self._create_agents()
    
    def _create_agents(self):
        """Create specialized agents for image collection"""
        
        # Image Search Agent
        search_agent = Agent(
            role='Wikimedia Bird Image Search Specialist',
            goal='Find the best bird images on Wikimedia Commons using optimal search strategies',
            backstory="""You are an expert at searching Wikimedia Commons for high-quality bird images.
            You know the best search terms, categories, and techniques to find clear, well-documented
            bird photographs. You understand scientific naming and common naming conventions.""",
            verbose=True,
            allow_delegation=False
        )
        
        # Quality Assessment Agent
        quality_agent = Agent(
            role='Bird Image Quality Evaluator',
            goal='Evaluate and rank bird images based on clarity, composition, and scientific value',
            backstory="""You are a professional bird photographer and ornithologist who can quickly
            assess image quality. You know what makes a good reference photo: proper lighting,
            clear bird features, minimal distractions, and good composition.""",
            verbose=True,
            allow_delegation=False
        )
        
        # Organization Agent
        org_agent = Agent(
            role='Digital Asset Organizer',
            goal='Systematically organize and catalog downloaded bird images',
            backstory="""You are a meticulous digital librarian who ensures perfect organization
            of image collections. You create consistent naming schemes, maintain metadata,
            and ensure easy retrieval of images.""",
            verbose=True,
            allow_delegation=False
        )
        
        return {
            'searcher': search_agent,
            'evaluator': quality_agent,
            'organizer': org_agent
        }
    
    def search_wikimedia_images(self, species_name, limit=10):
        """Search Wikimedia Commons for bird species images"""
        
        search_terms = [
            f"{species_name}",
            f"{species_name} bird",
            f"{species_name} male",
            f"{species_name} female"
        ]
        
        all_results = []
        
        for term in search_terms:
            # Search for files
            params = {
                'action': 'query',
                'format': 'json',
                'list': 'search',
                'srsearch': term,
                'srnamespace': 6,  # File namespace
                'srlimit': limit,
                'srinfo': 'totalhits|suggestion'
            }
            
            try:
                response = requests.get(self.base_url, params=params, timeout=10)
                data = response.json()
                
                if 'query' in data and 'search' in data['query']:
                    for item in data['query']['search']:
                        title = item['title']
                        
                        # Filter for likely bird images
                        title_lower = title.lower()
                        if any(ext in title_lower for ext in ['.jpg', '.jpeg', '.png']):
                            if 'bird' in title_lower or species_name.lower() in title_lower:
                                all_results.append({
                                    'title': title,
                                    'search_term': term,
                                    'snippet': item.get('snippet', ''),
                                    'timestamp': item.get('timestamp', '')
                                })
                
                time.sleep(0.5)  # Be respectful
                
            except Exception as e:
                print(f"❌ Search failed for '{term}': {e}")
        
        # Remove duplicates
        unique_results = []
        seen_titles = set()
        for result in all_results:
            if result['title'] not in seen_titles:
                unique_results.append(result)
                seen_titles.add(result['title'])
        
        return unique_results[:limit]
    
    def get_image_info(self, file_title):
        """Get detailed information about an image"""
        
        params = {
            'action': 'query',
            'format': 'json',
            'titles': file_title,
            'prop': 'imageinfo',
            'iiprop': 'url|size|metadata|extmetadata'
        }

        for attempt in range(3):
            try:
                print(f"📋 Getting info for: {file_title}")
                delay = 2 ** (attempt + 1)
                time.sleep(delay)

                response = requests.get(self.base_url, params=params, timeout=10)
                data = response.json()
                
                pages = data.get('query', {}).get('pages', {})
                for page_id, page_data in pages.items():
                    if 'imageinfo' in page_data:
                        image_info = page_data['imageinfo'][0]
                        return {
                            'url': image_info.get('url'),
                            'width': image_info.get('width'),
                            'height': image_info.get('height'),
                            'size': image_info.get('size'),
                            'title': file_title,
                            'description': page_data.get('extract', ''),
                            'metadata': image_info.get('extmetadata', {})
                        }
            
            except Exception as e:
                print(f"❌ Failed to get info for {file_title}: {e}")
            
            return None
    
    def evaluate_image_quality(self, image_info):
        """Evaluate image quality using basic metrics"""
        
        if not image_info:
            return 0
        
        score = 0
        width = image_info.get('width', 0)
        height = image_info.get('height', 0)
        
        # Size scoring (prefer larger images)
        if width >= 800 and height >= 600:
            score += 3
        elif width >= 500 and height >= 400:
            score += 2
        elif width >= 300 and height >= 200:
            score += 1
        
        # Aspect ratio (prefer reasonable bird photo ratios)
        if width > 0 and height > 0:
            ratio = width / height
            if 0.8 <= ratio <= 2.0:  # Reasonable ratios for bird photos
                score += 2
        
        # File size (prefer not too small, not too huge)
        size = image_info.get('size', 0)
        if 50000 <= size <= 5000000:  # 50KB to 5MB
            score += 1
        
        return score
    
    def download_image(self, image_info, species_name, bird_id, image_number):
        """Download and save an image with proper headers"""
        
        if not image_info or not image_info.get('url'):
            return None
        
        try:
            # Add proper headers (IMPORTANT!)
            headers = {
                'User-Agent': 'BirdSearchBot/1.0 (https://github.com/your-username/bird-search; your-email@example.com) Python/3.8',
                'Accept': 'image/*',
                'Accept-Language': 'en-US,en;q=0.9'
            }
            
            # Download image with headers
            response = requests.get(image_info['url'], headers=headers, timeout=15)
            response.raise_for_status()
            
            # Rest of the function remains the same...
            img = Image.open(io.BytesIO(response.content))
            
            # Create filename
            safe_species = species_name.replace(' ', '_').replace('/', '_')
            filename = f"bird_{bird_id:02d}_{image_number}_{safe_species}.jpg"
            filepath = self.output_dir / filename
            
            # Save image
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            print(f"      ✅ Saved: {filename}")
            
            return {
                'bird_id': bird_id,
                'species_name': species_name,
                'image_path': str(filepath),
                'source_url': image_info['url'],
                'source_title': image_info.get('title', ''),
                'width': image_info.get('width'),
                'height': image_info.get('height'),
                'file_size_mb': len(response.content) / (1024*1024),
                'source': 'Wikimedia Commons',
                'license': 'Free Use (Wikimedia Commons)',
                'image_number': image_number
            }
            
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return None
        
    def collect_species_images(self, species_name, bird_id, max_images=3):
        """Use CrewAI agents to collect images for a species"""
        
        print(f"\n🔍 Collecting images for: {species_name} (ID: {bird_id})")
        
        # Create tasks for agents
        search_task = Task(
            description=f"""
            Search Wikimedia Commons for high-quality images of {species_name}.
            
            Search Strategy:
            1. Try different search terms: "{species_name}", "{species_name} bird"
            2. Look for clear, well-lit photographs
            3. Avoid illustrations, drawings, or low-quality images
            4. Prioritize images that clearly show the bird
            
            Find at least {max_images * 2} candidate images to evaluate.
            """,
            agent=self.agents['searcher'],
            expected_output=f"List of candidate Wikimedia image files for {species_name}"
        )
        
        quality_task = Task(
            description=f"""
            Evaluate the candidate images found for {species_name} and select the best ones.
            
            Quality Criteria:
            1. Image resolution (prefer 800x600 or larger)
            2. Clear view of the bird (not distant or blurry)  
            3. Good lighting and contrast
            4. Minimal background distractions
            5. Bird occupies significant portion of frame
            
            Rank all candidates and select the top {max_images} images.
            """,
            agent=self.agents['evaluator'],
            expected_output=f"Ranked list of top {max_images} images with quality scores"
        )
        
        # Execute search manually (CrewAI agents provide intelligence)
        print(f"🤖 Agent: Searching Wikimedia Commons...")
        search_results = self.search_wikimedia_images(species_name, limit=15)
        
        if not search_results:
            print(f"   ❌ No images found for {species_name}")
            return []
        
        print(f"   ✅ Found {len(search_results)} candidate images")
        
        # Get detailed info and evaluate quality
        print(f"🤖 Agent: Evaluating image quality...")
        image_candidates = []
        
        for result in search_results[:10]:  # Limit API calls
            info = self.get_image_info(result['title'])
            if info:
                quality_score = self.evaluate_image_quality(info)
                if quality_score > 2:  # Minimum quality threshold
                    image_candidates.append((info, quality_score))
        
        # Sort by quality score
        image_candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Download best images
        print(f"🤖 Agent: Organizing and downloading best {max_images} images...")
        downloaded = []
        
        for i, (image_info, score) in enumerate(image_candidates[:max_images]):
            print(f"   📥 Downloading image {i+1}/{max_images} (score: {score})")
            
            result = self.download_image(image_info, species_name, bird_id, i+1)
            if result:
                result['quality_score'] = score
                downloaded.append(result)
                print(f"      ✅ Saved: {Path(result['image_path']).name}")
            
            time.sleep(1)  # Be respectful
        
        print(f"   🎉 Successfully downloaded {len(downloaded)} images for {species_name}")
        return downloaded

def collect_all_bird_images(features_file="bird_features.pkl", images_per_bird=2):
    """Main function to collect images for all bird species"""
    
    print("🤖 Starting CrewAI Wikimedia Bird Image Collection")
    print("="*60)
    
    # Load bird species
    with open(features_file, 'rb') as f:
        features_list = pickle.load(f)
    
    print(f"📋 Processing {len(features_list)} bird species")
    print(f"🎯 Target: {images_per_bird} images per species")
    
    # Initialize collector
    collector = WikimediaBirdImageCollector()
    
    # Process each species
    all_downloaded = []
    successful_species = 0
    
    for i, bird_data in enumerate(features_list):
        species_name = bird_data['species_name']
        bird_id = bird_data['bird_id']
        
        print(f"\n📸 Processing {i+1}/{len(features_list)}: {species_name}")
        
        # Collect images for this species
        downloaded = collector.collect_species_images(species_name, bird_id, images_per_bird)
        
        if downloaded:
            all_downloaded.extend(downloaded)
            successful_species += 1
        
        # Progress update
        if (i + 1) % 10 == 0:
            print(f"\n📊 Progress: {i+1}/{len(features_list)} species processed")
            print(f"   ✅ Successful: {successful_species}")
            print(f"   📸 Images downloaded: {len(all_downloaded)}")
    
    # Save results
    print(f"\n💾 Saving results...")
    
    # Create summary DataFrame
    results_df = pd.DataFrame(all_downloaded)
    results_df.to_csv('wikimedia_bird_images.csv', index=False)
    
    # Create species summary
    species_summary = results_df.groupby(['bird_id', 'species_name']).agg({
        'image_path': 'count',
        'quality_score': 'mean',
        'file_size_mb': 'mean'
    }).rename(columns={'image_path': 'image_count'}).reset_index()
    
    species_summary.to_csv('bird_images_summary.csv', index=False)
    
    print(f"\n🎉 Collection Complete!")
    print(f"   📊 Total images: {len(all_downloaded)}")
    print(f"   🐦 Successful species: {successful_species}/{len(features_list)}")
    print(f"   📁 Images saved to: {collector.output_dir}")
    print(f"   📄 Log saved to: wikimedia_bird_images.csv")
    print(f"   📈 Summary saved to: bird_images_summary.csv")
    
    return all_downloaded

def quick_test_collection(species_name="Common Redpoll"):
    """Test the collection system on a single species"""
    
    print(f"🧪 Testing image collection for: {species_name}")
    
    collector = WikimediaBirdImageCollector()
    results = collector.collect_species_images(species_name, 0, max_images=2)
    
    if results:
        print(f"✅ Test successful! Downloaded {len(results)} images")
        for result in results:
            print(f"   📸 {Path(result['image_path']).name} ({result['width']}x{result['height']})")
    else:
        print(f"❌ Test failed - no images downloaded")
    
    return results

if __name__ == "__main__":
    
    print("🚀 Wikimedia Commons Bird Image Collector")
    print("\nChoose an option:")
    print("1. Quick test (single species)")
    print("2. Collect images for all species")
    
    choice = input("\nEnter choice (1 or 2): ")
    
    if choice == "1":
        quick_test_collection()
        
    elif choice == "2":
        collect_all_bird_images(images_per_bird=5)
        
    else:
        print("Invalid choice!")
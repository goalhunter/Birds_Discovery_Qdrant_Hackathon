import os
import pandas as pd
import requests
import json
import re
import time
from typing import Dict, List
from crewai import Agent, Task, Crew
from crewai.tools import tool

# Set up API keys (add your actual keys)
# os.environ["OPENAI_API_KEY"] = "your-openai-api-key"  # Uncomment and add your key

# Custom Tools using CrewAI's proper decorator
@tool
def fetch_wikipedia_data(species_name: str) -> str:
    """Fetch comprehensive bird data from Wikipedia API for a given species name.
    Returns JSON string with extract, URL, and thumbnail information."""
    try:
        clean_name = species_name.replace(' ', '_')
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{clean_name}"
        
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            result = {
                'species_name': species_name,
                'extract': data.get('extract', ''),
                'url': data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                'thumbnail': data.get('thumbnail', {}).get('source', '') if data.get('thumbnail') else '',
                'success': True
            }
            return json.dumps(result, indent=2)
    except Exception as e:
        error_result = {
            'species_name': species_name,
            'error': f"Error fetching {species_name}: {str(e)}",
            'success': False
        }
        return json.dumps(error_result, indent=2)
    
    return json.dumps({'species_name': species_name, 'error': 'No data found', 'success': False})

@tool
def extract_taxonomy_info(wikipedia_text: str) -> str:
    """Extract scientific name and family classification from Wikipedia text.
    Returns JSON with scientific_name and family fields."""
    
    # Scientific name extraction patterns
    scientific_patterns = [
        r'\(([A-Z][a-z]+ [a-z]+)\)',  # (Genus species)
        r'^([A-Z][a-z]+ [a-z]+)',    # Genus species at start
        r'scientific name[:\s]+([A-Z][a-z]+ [a-z]+)',
        r'binomial name[:\s]+([A-Z][a-z]+ [a-z]+)'
    ]
    
    scientific_name = 'Unknown'
    for pattern in scientific_patterns:
        match = re.search(pattern, wikipedia_text, re.IGNORECASE)
        if match:
            scientific_name = match.group(1)
            break
    
    # Family extraction patterns
    family_patterns = [
        r'family ([A-Z][a-z]+idae)',
        r'([A-Z][a-z]+idae) family',
        r'belongs to the family ([A-Z][a-z]+idae)',
        r'member of the ([A-Z][a-z]+idae)',
        r'of the ([A-Z][a-z]+idae) family'
    ]
    
    family = 'Unknown'
    for pattern in family_patterns:
        match = re.search(pattern, wikipedia_text, re.IGNORECASE)
        if match:
            family = match.group(1)
            break
    
    result = {
        'scientific_name': scientific_name,
        'family': family,
        'extraction_success': scientific_name != 'Unknown' or family != 'Unknown'
    }
    
    return json.dumps(result, indent=2)

@tool
def analyze_habitat_geography(wikipedia_text: str) -> str:
    """Analyze habitat preferences and geographic distribution from Wikipedia text.
    Returns JSON with habitats and geographic_regions arrays."""
    
    text_lower = wikipedia_text.lower()
    
    # Comprehensive habitat mapping
    habitats = []
    habitat_keywords = {
        'forest': ['forest', 'woodland', 'trees', 'canopy', 'rainforest', 'coniferous', 'deciduous', 'tropical forest'],
        'wetland': ['wetland', 'marsh', 'swamp', 'water', 'pond', 'lake', 'river', 'streams', 'bog', 'fen'],
        'grassland': ['grassland', 'prairie', 'field', 'meadow', 'savanna', 'steppe', 'pasture', 'rangeland'],
        'urban': ['urban', 'city', 'suburban', 'parks', 'gardens', 'buildings', 'developed areas', 'human settlements'],
        'coastal': ['coastal', 'shore', 'beach', 'ocean', 'sea', 'marine', 'seashore', 'tidal', 'estuarine'],
        'mountain': ['mountain', 'alpine', 'highland', 'cliff', 'rocky', 'peaks', 'montane', 'subalpine'],
        'desert': ['desert', 'arid', 'dry', 'scrubland', 'semi-arid', 'xeric'],
        'agricultural': ['farm', 'agricultural', 'crop', 'cultivated', 'orchard', 'plantation']
    }
    
    for habitat, keywords in habitat_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            habitats.append(habitat)
    
    # Geographic regions analysis
    regions = []
    region_keywords = {
        'africa': ['africa', 'african', 'sahara', 'congo', 'ethiopia', 'kenya', 'tanzania'],
        'europe': ['europe', 'european', 'scandinavia', 'mediterranean', 'britain', 'ireland'],
        'asia': ['asia', 'asian', 'siberia', 'china', 'india', 'japan', 'southeast asia'],
        'north_america': ['north america', 'canada', 'united states', 'alaska', 'mexico', 'greenland'],
        'south_america': ['south america', 'brazil', 'argentina', 'colombia', 'peru', 'amazon', 'andes'],
        'australia': ['australia', 'australian', 'new zealand', 'tasmania', 'oceania'],
        'arctic': ['arctic', 'polar', 'tundra', 'subarctic', 'boreal']
    }
    
    for region, keywords in region_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            regions.append(region)
    
    result = {
        'habitats': habitats or ['unknown'],
        'geographic_regions': regions,
        'habitat_diversity': len(habitats),
        'geographic_spread': len(regions)
    }
    
    return json.dumps(result, indent=2)

@tool
def analyze_bird_behavior(wikipedia_text: str) -> str:
    """Comprehensive analysis of bird behavioral patterns, physical traits, and ecological roles.
    Returns detailed JSON with size, behaviors, feeding, social structure, migration, colors, and vocalizations."""
    
    text_lower = wikipedia_text.lower()
    
    # Size classification with more specific patterns
    size_category = 'medium'
    if any(phrase in text_lower for phrase in ['tiny', 'very small', 'smallest', 'miniature', 'diminutive']):
        size_category = 'tiny'
    elif any(phrase in text_lower for phrase in ['small', 'little', 'petite', 'compact']):
        size_category = 'small'  
    elif any(phrase in text_lower for phrase in ['large', 'big', 'sizeable', 'robust']):
        size_category = 'large'
    elif any(phrase in text_lower for phrase in ['very large', 'huge', 'massive', 'giant', 'enormous']):
        size_category = 'very_large'
    
    # Behavioral patterns
    behaviors = []
    behavior_keywords = {
        'migratory': ['migrate', 'migration', 'migratory', 'seasonal movement'],
        'resident': ['resident', 'non-migratory', 'year-round', 'permanent resident'],
        'nocturnal': ['nocturnal', 'night', 'nighttime', 'active at night'],
        'diurnal': ['diurnal', 'day', 'daytime', 'active during day'],
        'territorial': ['territorial', 'defend territory', 'aggressive', 'territorial behavior'],
        'colonial': ['colonial', 'colony', 'communal', 'group nesting']
    }
    
    for behavior, keywords in behavior_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            behaviors.append(behavior)
    
    # Feeding behavior analysis
    feeding_type = 'omnivore'
    feeding_keywords = {
        'insectivore': ['insect', 'insects', 'bug', 'larvae', 'arthropod', 'invertebrate'],
        'granivore': ['seed', 'seeds', 'grain', 'nuts', 'berries'],
        'piscivore': ['fish', 'fishing', 'aquatic prey', 'piscivorous'],
        'nectivore': ['nectar', 'flower', 'pollen', 'pollinator'],
        'frugivore': ['fruit', 'berry', 'berries', 'frugivorous'],
        'carnivore': ['predator', 'prey', 'hunt', 'carnivorous', 'meat', 'rodent'],
        'scavenger': ['carrion', 'scaveng', 'dead', 'carcass']
    }
    
    for feeding, keywords in feeding_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            feeding_type = feeding
            break
    
    # Social structure
    social_structure = 'pairs'
    if any(phrase in text_lower for phrase in ['flock', 'group', 'social', 'communal', 'gregarious']):
        social_structure = 'social'
    elif any(phrase in text_lower for phrase in ['solitary', 'alone', 'isolated', 'individual']):
        social_structure = 'solitary'
    
    # Migration patterns
    migration_type = 'unknown'
    if any(phrase in text_lower for phrase in ['long-distance', 'long distance', 'transoceanic', 'intercontinental']):
        migration_type = 'long_distance'
    elif any(phrase in text_lower for phrase in ['short-distance', 'short distance', 'partial', 'altitudinal']):
        migration_type = 'short_distance'
    elif any(phrase in text_lower for phrase in ['resident', 'non-migratory', 'year-round']):
        migration_type = 'resident'
    
    # Color extraction
    colors = []
    color_words = ['black', 'white', 'brown', 'gray', 'grey', 'red', 'blue', 'green', 'yellow', 
                   'orange', 'purple', 'pink', 'golden', 'silver', 'chestnut', 'rufous']
    
    for color in color_words:
        if color in text_lower:
            colors.append(color)
    
    # Vocalization analysis
    vocalization = 'unknown'
    if any(phrase in text_lower for phrase in ['song', 'melodic', 'musical', 'singing', 'melodious']):
        vocalization = 'melodic'
    elif any(phrase in text_lower for phrase in ['call', 'harsh', 'loud', 'screech', 'cry']):
        vocalization = 'harsh'
    elif any(phrase in text_lower for phrase in ['quiet', 'soft', 'whisper', 'subtle']):
        vocalization = 'soft'
    
    result = {
        'size_category': size_category,
        'behaviors': behaviors,
        'feeding_type': feeding_type,
        'social_structure': social_structure,
        'migration_type': migration_type,
        'primary_colors': colors,
        'vocalization': vocalization,
        'behavior_complexity': len(behaviors),
        'color_diversity': len(colors)
    }
    
    return json.dumps(result, indent=2)

# Define specialized agents
wikipedia_researcher = Agent(
    role='Wikipedia Data Researcher',
    goal='Efficiently fetch comprehensive Wikipedia data for bird species',
    backstory="""You are an expert ornithological data collector with deep knowledge of Wikipedia's API structure. 
    Your specialty is gathering reliable, comprehensive information about bird species from Wikipedia's vast database. 
    You understand the nuances of scientific nomenclature and can navigate Wikipedia's data structure expertly.""",
    tools=[fetch_wikipedia_data],
    verbose=True,
    max_iter=2
)

taxonomy_specialist = Agent(
    role='Avian Taxonomy Expert',
    goal='Extract accurate taxonomic classifications and scientific nomenclature',
    backstory="""You are a world-renowned ornithological taxonomist with expertise in bird classification systems. 
    You have spent decades studying phylogenetic relationships and can identify scientific names, family classifications, 
    and taxonomic hierarchies with exceptional accuracy. Your knowledge spans both modern and historical nomenclature.""",
    tools=[extract_taxonomy_info],
    verbose=True,
    max_iter=2
)

habitat_ecologist = Agent(
    role='Habitat and Biogeography Specialist',
    goal='Analyze habitat preferences and geographic distribution patterns',
    backstory="""You are an ecological specialist focusing on avian biogeography and habitat analysis. 
    Your expertise covers global ecosystems, migration corridors, and species distribution patterns. 
    You excel at identifying environmental requirements and geographic ranges from descriptive texts.""",
    tools=[analyze_habitat_geography],
    verbose=True,
    max_iter=2
)

behavioral_biologist = Agent(
    role='Avian Behavioral Ecologist',
    goal='Analyze comprehensive behavioral patterns and ecological roles',
    backstory="""You are a leading behavioral ecologist specializing in avian behavior, feeding ecology, 
    and social structures. Your research covers migration patterns, breeding behaviors, foraging strategies, 
    and interspecies interactions. You can extract complex behavioral insights from observational data.""",
    tools=[analyze_bird_behavior],
    verbose=True,
    max_iter=2
)

data_synthesizer = Agent(
    role='Ornithological Data Integration Specialist',
    goal='Synthesize multi-source data into comprehensive, structured bird profiles',
    backstory="""You are a data scientist specializing in biological database integration with a focus on ornithology. 
    Your expertise lies in combining diverse data sources into coherent, structured formats suitable for 
    graph databases and relationship mapping. You understand Neo4j structures and scientific data standards.""",
    verbose=True,
    max_iter=1
)

def create_bird_analysis_crew(species_name: str, csv_metadata: dict) -> Crew:
    """Create a specialized crew to analyze a single bird species"""
    
    # Task 1: Data Collection
    wikipedia_task = Task(
        description=f"""Fetch comprehensive Wikipedia data for the bird species '{species_name}'.
        
        Your objectives:
        1. Use the fetch_wikipedia_data tool to get Wikipedia summary information
        2. Ensure you retrieve the full extract text, URL, and thumbnail if available
        3. Verify the data quality and completeness
        4. Return detailed information that will be used by other specialists
        
        Species to research: {species_name}""",
        expected_output="Complete JSON data containing Wikipedia extract, URL, thumbnail, and success status",
        agent=wikipedia_researcher,
        tools=[fetch_wikipedia_data]
    )
    
    # Task 2: Taxonomic Analysis
    taxonomy_task = Task(
        description=f"""Extract taxonomic information for '{species_name}' from the Wikipedia data obtained by the researcher.
        
        Your objectives:
        1. Analyze the Wikipedia text to find scientific nomenclature
        2. Identify the family classification (especially -idae endings)
        3. Look for binomial names in parentheses or mentioned explicitly
        4. Provide confidence assessment of your extractions
        
        Focus on accuracy and use multiple pattern matching approaches.""",
        expected_output="JSON containing scientific_name, family, and extraction success indicators",
        agent=taxonomy_specialist,
        context=[wikipedia_task],
        tools=[extract_taxonomy_info]
    )
    
    # Task 3: Habitat Analysis
    habitat_task = Task(
        description=f"""Analyze habitat preferences and geographic distribution for '{species_name}' using the Wikipedia data.
        
        Your objectives:
        1. Identify all mentioned habitat types (forest, wetland, grassland, etc.)
        2. Extract geographic regions and distribution patterns
        3. Assess habitat diversity and geographic spread
        4. Consider seasonal variations if mentioned
        
        Be thorough in identifying both primary and secondary habitats.""",
        expected_output="JSON with comprehensive habitat arrays, geographic regions, and diversity metrics",
        agent=habitat_ecologist,
        context=[wikipedia_task],
        tools=[analyze_habitat_geography]
    )
    
    # Task 4: Behavioral Analysis
    behavior_task = Task(
        description=f"""Conduct comprehensive behavioral analysis for '{species_name}' from the Wikipedia data.
        
        Your objectives:
        1. Classify size category based on descriptive terms
        2. Extract behavioral patterns (migration, activity periods, territorial behavior)
        3. Analyze feeding ecology and dietary preferences
        4. Determine social structure and group dynamics
        5. Identify color patterns and vocalization characteristics
        6. Assess migration patterns if applicable
        
        Provide detailed behavioral insights that will support ecological relationship mapping.""",
        expected_output="Comprehensive JSON with size, behaviors, feeding, social structure, migration, colors, and vocalizations",
        agent=behavioral_biologist,
        context=[wikipedia_task],
        tools=[analyze_bird_behavior]
    )
    
    # Task 5: Data Synthesis
    synthesis_task = Task(
        description=f"""Synthesize all collected data for '{species_name}' into a comprehensive, structured bird profile ready for Neo4j integration.
        
        Your objectives:
        1. Combine Wikipedia data, taxonomic info, habitat analysis, and behavioral data
        2. Integrate the CSV metadata: {csv_metadata}
        3. Create a complete JSON structure with all relevant fields
        4. Ensure data consistency and resolve any conflicts
        5. Format for optimal Neo4j relationship mapping
        6. Add data quality indicators and processing metadata
        
        Create a final profile that captures the complete ecological and biological picture of this species.""",
        expected_output="Complete, structured JSON bird profile ready for database integration and relationship mapping",
        agent=data_synthesizer,
        context=[wikipedia_task, taxonomy_task, habitat_task, behavior_task]
    )
    
    # Assemble the crew
    crew = Crew(
        agents=[wikipedia_researcher, taxonomy_specialist, habitat_ecologist, behavioral_biologist, data_synthesizer],
        tasks=[wikipedia_task, taxonomy_task, habitat_task, behavior_task, synthesis_task],
        verbose=True,
        planning=False  # Disable planning to avoid extra complexity
    )
    
    return crew

def process_birds_with_crewai(csv_file: str = 'bird_images_summary.csv') -> Dict:
    """Main function to process bird species using CrewAI"""
    
    # Read CSV file
    df = pd.read_csv(csv_file)
    
    print(f"🐦 Starting CrewAI Bird Analysis Pipeline")
    print(f"📊 Processing {len(df)} bird species")
    print("="*70)
    
    bird_database = {}
    successful_processing = 0
    
    for idx, row in df.iterrows():
        species_name = row['species_name']
        csv_metadata = {
            'bird_id': row['bird_id'],
            'image_count': row['image_count'],
            'quality_score': row['quality_score'],
            'file_size_mb': row['file_size_mb']
        }
        
        print(f"\n🔄 PROCESSING ({idx+1}/{len(df)}): {species_name}")
        print("="*70)
        
        try:
            # Create specialized crew for this species
            crew = create_bird_analysis_crew(species_name, csv_metadata)
            
            # Execute the crew workflow
            start_time = time.time()
            result = crew.kickoff()
            processing_time = time.time() - start_time
            
            # Parse and store the result
            # Parse and store the result
            try:
                # Extract the actual content from CrewOutput
                if hasattr(result, 'raw'):
                    result_text = result.raw
                else:
                    result_text = str(result)
                
                # Clean up markdown formatting if present
                if result_text.startswith('```json'):
                    result_text = result_text[7:-3].strip()
                elif result_text.startswith('```'):
                    result_text = result_text[3:-3].strip()
                
                bird_profile = json.loads(result_text)
                
                # Add processing metadata
                bird_profile['processing_metadata'] = {
                    'processing_time_seconds': round(processing_time, 2),
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'crew_agents': 5,
                    'processing_success': True
                }
                
                bird_database[species_name] = bird_profile
                successful_processing += 1
                
                print(f"✅ SUCCESS: {species_name} processed in {processing_time:.2f}s")
                
            except (json.JSONDecodeError, AttributeError) as e:
                print(f"⚠️  Parsing error for {species_name}: {e}")
                bird_database[species_name] = {
                    'species_name': species_name,
                    'csv_metadata': csv_metadata,
                    'error': f'Parsing failed: {str(e)}',
                    'processing_success': False
                }
            
        except Exception as e:
            print(f"❌ ERROR processing {species_name}: {str(e)}")
            bird_database[species_name] = {
                'species_name': species_name,
                'csv_metadata': csv_metadata,
                'error': str(e),
                'processing_success': False
            }
        
        # Rate limiting and progress
        time.sleep(1)  # Respectful rate limiting
        print(f"📈 Progress: {idx+1}/{len(df)} species processed")
    
    # Save comprehensive results
    output_file = 'crewai_comprehensive_bird_database.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(bird_database, f, indent=2, ensure_ascii=False)
    
    # Generate final report
    generate_final_report(bird_database, output_file, successful_processing, len(df))
    
    return bird_database

def generate_final_report(bird_database: Dict, output_file: str, successful: int, total: int):
    """Generate comprehensive processing report"""
    print("\n" + "="*70)
    print("🎉 CREWAI BIRD ANALYSIS PIPELINE COMPLETED")
    print("="*70)
    
    print(f"📁 Database saved to: {output_file}")
    print(f"📊 Total species processed: {total}")
    print(f"✅ Successful extractions: {successful}")
    print(f"❌ Failed extractions: {total - successful}")
    print(f"📈 Success rate: {(successful/total)*100:.1f}%")
    
    # Quality metrics
    scientific_names_found = sum(1 for data in bird_database.values() 
                               if data.get('scientific_name') and data.get('scientific_name') != 'Unknown')
    families_identified = sum(1 for data in bird_database.values() 
                            if data.get('family') and data.get('family') != 'Unknown')
    habitat_data_extracted = sum(1 for data in bird_database.values() 
                               if data.get('habitats') and data.get('habitats') != ['unknown'])
    
    print(f"\n🔬 Data Quality Metrics:")
    print(f"   Scientific names extracted: {scientific_names_found}/{total} ({(scientific_names_found/total)*100:.1f}%)")
    print(f"   Family classifications: {families_identified}/{total} ({(families_identified/total)*100:.1f}%)")
    print(f"   Habitat data extracted: {habitat_data_extracted}/{total} ({(habitat_data_extracted/total)*100:.1f}%)")
    
    print(f"\n🚀 Ready for Neo4j graph database integration!")
    print(f"🔗 The data structure supports rich relationship mapping between:")
    print("   • Species ↔ Families ↔ Taxonomic hierarchies")
    print("   • Species ↔ Habitats ↔ Geographic regions")
    print("   • Species ↔ Behaviors ↔ Ecological roles")
    print("   • Species ↔ Feeding types ↔ Food webs")

if __name__ == "__main__":
    print("🚀 Initializing CrewAI Bird Analysis System...")
    
    # Process birds (start small for testing)
    bird_database = process_birds_with_crewai('bird_images_summary.csv')
    
    print(f"\n🎯 Analysis complete! Check 'crewai_comprehensive_bird_database.json' for results.")
    print("📋 Ready to proceed with Neo4j integration or further analysis.")
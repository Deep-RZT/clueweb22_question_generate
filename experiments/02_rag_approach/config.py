# Energy Literature Crawler Configuration

# Energy domain keywords for paper collection
ENERGY_KEYWORDS = [
    # General / Overarching
    "energy", "energy system", "energy infrastructure", "energy transition", 
    "energy security", "energy planning", "energy economics", "energy consumption", 
    "energy demand", "energy policy", "sustainable energy", "carbon neutrality",
    
    # Power Systems & Electricity
    "power system", "electricity generation", "electric grid", "smart grid", 
    "load forecasting", "transmission network", "grid integration", 
    "distributed energy resources", "energy storage", "pumped hydro storage", 
    "battery storage",
    
    # Fossil Energy
    "fossil fuel", "natural gas", "gas pipeline", "LNG", "coal power", 
    "oil and gas", "shale gas", "petroleum refining", 
    "carbon capture and storage", "CCS",
    
    # Renewable Energy
    "renewable energy", "solar energy", "photovoltaic", "wind energy", 
    "onshore wind", "offshore wind", "geothermal energy", "hydropower", 
    "hydroelectric", "bioenergy", "biomass", "biogas", "tidal energy", 
    "wave energy",
    
    # Emerging Energy & Hydrogen
    "hydrogen energy", "green hydrogen", "blue hydrogen", "fuel cell", 
    "ammonia fuel", "synthetic fuels", "power-to-gas", "energy carriers",
    
    # End-use & Efficiency
    "building energy efficiency", "industrial energy use", "electric vehicles", 
    "energy-saving technologies", "smart home energy", "demand-side management",
    
    # Emissions & Environmental Impact
    "carbon emissions", "greenhouse gases", "life cycle assessment", 
    "emission intensity", "climate policy", "carbon footprint",
    
    # Markets & Policy
    "energy market", "energy pricing", "emission trading scheme", 
    "carbon tax", "renewable energy incentives", "decarbonization policy"
]

# Flatten all keywords into a single list
ALL_KEYWORDS = ENERGY_KEYWORDS

# Crawler settings
CRAWLER_CONFIG = {
    "max_papers_per_source": 300,  # Maximum papers to collect from each source
    "total_target": 1000,  # Total target number of papers
    "delay_between_requests": 1,  # Seconds to wait between requests
    "max_retries": 3,
    "timeout": 30,
    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Output directories
OUTPUT_DIRS = {
    "raw_papers": "data/raw_papers",
    "processed_text": "data/processed_text", 
    "metadata": "data/metadata",
    "logs": "logs"
}

# arXiv categories related to energy
ARXIV_CATEGORIES = [
    "physics.soc-ph",  # Physics and Society
    "eess.SY",         # Systems and Control
    "cs.SY",           # Systems and Control
    "physics.app-ph",  # Applied Physics
    "cond-mat.mtrl-sci", # Materials Science
    "physics.chem-ph", # Chemical Physics
]

# OpenAlex concepts related to energy
OPENALEX_CONCEPTS = [
    "C159985019",  # Energy
    "C127313418",  # Renewable energy
    "C159750122",  # Solar energy
    "C2777964",    # Wind power
    "C2776044",    # Nuclear power
    "C2777649",    # Fossil fuel
] 
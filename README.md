# World Model: LLM-Driven Dynamic World Simulation

A sophisticated world modeling system that simulates complex global interactions through hierarchical agents and dynamic parameter systems, inspired by World3 model principles and neuroscience-based approaches.

## 🌍 Overview

This project implements a comprehensive world modeling system that uses Large Language Models (LLMs) to simulate and predict global dynamics across multiple scales of influence - from individual actors to entire nations. The system creates interconnected webs of influence that can model complex feedback loops, emergent behaviors, and cascading effects across different levels of society.

## 🔬 Approach to World Modeling

### Core Philosophy
Our approach is **akin to the World3 model and neuroscience**, where:
- **Parameters** are organized as hierarchical trees containing smaller, reasoned components
- **Actors** represent entities at different scales of influence
- **LLMs** automatically generate and reason about these components
- **Feedback loops** emerge naturally from parameter interactions
- **Influence scores** determine relative impact across different scales

### Key Concepts

**Hierarchical Influence Structure:**
```
Level 1: World           (Global systems, climate, economics)
Level 2: Countries       (Nations, regions, blocs)
Level 3: Companies       (Corporations, industries, markets)
Level 4: Individuals     (Leaders, celebrities, activists)
```

**Influence Scaling Example:**
- Elon Musk (Individual) might have equivalent influence to Buddhism (Cultural Movement of 500M people)
- Both impact: World future, country policies, technological development

## 🎭 Actor System

### Actor Categories
- **Countries**: Nations, regions, political blocs
- **Companies**: Corporations, industries, startups
- **Societies**: Cultural movements, religions, ideologies
- **Subsocieties**: Communities, ethnic groups, demographics
- **Celebrities**: Public figures, influencers, thought leaders
- **Industries**: Sectors, markets, economic domains
- **Activists**: NGOs, advocacy groups, movements
- **Science**: Research institutions, academic fields
- **Politicians**: Governments, parties, political figures

### Actor Parameters
Each actor maintains dynamic parameters including:
- **Economic**: GDP, ARR, spending, savings, investments
- **Safety**: Security levels, projected safety, stability
- **Well-being**: Quality of life, happiness indices, health metrics
- **Influence**: Reach, impact potential, network effects
- **Resources**: Access to materials, energy, human capital
- **Innovation**: R&D capacity, technological advancement, patents

### Actions Framework
Each parameter supports three primary actions:
- **Decrease**: Reduce parameter value with reasoned function
- **Increase**: Enhance parameter value with calculated impact
- **Hold**: Maintain current state with stability reasoning

## 🔧 System Architecture

### 1. Initialization Phase

**Step 1: Define Actor Categories**
- Generate hierarchical tree structure based on user-defined depth (1-4 levels)
- Create system prompts for each tree level
- Establish influence relationships between levels

**Step 2: Parameter Definition**
- Populate actor tree with comprehensive parameter sets
- Define constituent components for each actor level
- Assess influences of external conditions (wars, policies, resources)
- Capture current world state at simulation start date
- Export structured data to CSV/JSON format

**Step 3: Action System Extension**
- Map possible actions for each parameter at every depth level
- Create cross-level influence connections
- Establish feedback loops between related parameters

### 2. Training Phase

**Real-World Data Integration:**
- Gather historical data for every possible metric
- Download and format data into structured CSV files
- Implement AI-powered internet search for missing data points
- Create temporal datasets (monthly, weekly, yearly based on resolution)

**Connection Creation:**
- Initialize linking factors and functions between parameters
- Build lookup tables through internet research
- Create Partial Differential Equations (PDEs) for each relationship

**Orchestration Training:**
- LLM calls for each actor and sub-actor parameter
- Hierarchical reasoning across thousands of equations
- Parallel processing with centralized logging database
- Backpropagation analysis for parameter optimization
- Deviation measurement against real-world data

### 3. Inference Phase (Future Prediction)

**External Parameter Definition:**
- Policies, wars, natural disasters
- Resource availability, scientific breakthroughs
- Social media trends, scandals, election results
- Temporal resolution settings

**Dynamic Extension:**
- Scan all parameters and actors for needed extensions
- Create new lookup tables and linking factors
- Establish metric relationships for emerging connections

**Simulation Execution:**
- Orchestration agent manages hierarchical LLM calls
- Parameter updates through PDE reasoning
- Centralized state management and logging
- Iterative progression through temporal steps

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Node.js 16+
- OpenAI or Anthropic API key
- Modern web browser

### Installation

1. **Clone and navigate to project:**
   ```bash
   git clone <repository-url>
   cd 58_Worldmodel/worldmodel
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Node.js dependencies:**
   ```bash
   npm install
   ```

4. **Set up environment variables:**
   ```bash
   cp env.example .env
   # Edit .env with your API keys
   ```

### Running the System

**Start the backend:**
```bash
python backend/main.py
```

**Start the frontend:**
```bash
npm start
```

**Initialize actors:**
```bash
python backend/routes/initialization_route/actors_init.py
```

## 📊 Features

### Current Implementation
- ✅ **Hierarchical Actor Generation**: Multi-level actor creation with influence scoring
- ✅ **LLM Integration**: OpenAI and Anthropic API support with fallback logic
- ✅ **Cost Tracking**: Real-time API usage monitoring and cost analysis
- ✅ **JSON Persistence**: Automatic data saving with metadata and versioning
- ✅ **Web Interface**: Modern React frontend with responsive design
- ✅ **Error Handling**: Comprehensive error management and retry logic

### Roadmap
- 🔄 **Training System**: Real-world data integration and PDE generation
- 🔄 **Inference Engine**: Dynamic parameter updates and prediction system
- 🔄 **Visualization**: Interactive network graphs and influence mapping
- 🔄 **Scenario Planning**: What-if analysis and alternative future modeling
- 🔄 **Performance Optimization**: Parallel processing and caching systems

## 🔬 Technical Details

### Data Structure
```json
{
  "actor": {
    "name": "United States",
    "level": 2,
    "influence_score": 0.85,
    "parameters": {
      "gdp": 23.32,
      "military_spending": 0.732,
      "innovation_index": 0.89
    },
    "actions": {
      "gdp": ["increase", "decrease", "hold"],
      "connections": ["China.trade", "EU.policies"]
    }
  }
}
```

### Scaling Considerations
- **Horizontal Scaling**: Distributed LLM calls across multiple instances
- **Vertical Scaling**: Optimized parameter calculations and caching
- **Data Management**: Efficient storage and retrieval of historical simulations
- **Real-time Processing**: Stream processing for live parameter updates

## 📈 Cost Analysis

The system includes comprehensive cost tracking for:
- API calls per simulation run
- Token usage across different models
- Cost per parameter calculation
- Session-wide expense monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests and documentation
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🎯 Vision

This world model aims to become the most sophisticated simulation platform for understanding global dynamics, enabling researchers, policymakers, and organizations to:
- **Predict** complex global interactions
- **Understand** cascade effects across different scales
- **Plan** for alternative futures and scenarios
- **Optimize** decision-making with comprehensive impact analysis

---

*"The future is not predetermined, but understanding the complex webs of influence that shape our world can help us navigate toward better outcomes."*

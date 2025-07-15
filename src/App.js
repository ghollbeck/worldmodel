import React, { useState } from 'react';
import './App.css';

function App() {
  const [parameters, setParameters] = useState({
    population: 7800000000,
    economy: 75,
    environment: 60,
    technology: 80,
    health: 70,
    education: 65,
    governance: 55
  });

  // New state for mode selection
  const [inputMode, setInputMode] = useState('dropdown'); // 'dropdown' or 'freetext'
  const [freeTextInput, setFreeTextInput] = useState('');

  // State for parameter cards
  const [parameterCards, setParameterCards] = useState([]);
  const [nextCardId, setNextCardId] = useState(1);

  const [depthLevel, setDepthLevel] = useState(3);

  // New state for active phase
  const [activePhase, setActivePhase] = useState('initialization');

  // New state for logs
  const [logs, setLogs] = useState([
    { id: 1, timestamp: new Date().toISOString(), message: 'System initialized', type: 'info' },
    { id: 2, timestamp: new Date().toISOString(), message: 'Ready for initialization phase', type: 'info' }
  ]);

  // Extended list of world model parameters
  const worldModelParameters = [
    { id: 'population', label: 'Population', min: 0, max: 15000000000, step: 1000000, unit: 'people' },
    { id: 'economy', label: 'Economic Growth', min: 0, max: 100, step: 1, unit: '%' },
    { id: 'environment', label: 'Environmental Quality', min: 0, max: 100, step: 1, unit: '%' },
    { id: 'technology', label: 'Technology Level', min: 0, max: 100, step: 1, unit: '%' },
    { id: 'health', label: 'Health Index', min: 0, max: 100, step: 1, unit: '%' },
    { id: 'education', label: 'Education Level', min: 0, max: 100, step: 1, unit: '%' },
    { id: 'governance', label: 'Governance Quality', min: 0, max: 100, step: 1, unit: '%' },
    { id: 'climate_stability', label: 'Climate Stability', min: 0, max: 100, step: 1, unit: '%' },
    { id: 'resource_scarcity', label: 'Resource Scarcity', min: 0, max: 100, step: 1, unit: '%' },
    { id: 'social_cohesion', label: 'Social Cohesion', min: 0, max: 100, step: 1, unit: '%' },
    { id: 'political_stability', label: 'Political Stability', min: 0, max: 100, step: 1, unit: '%' },
    { id: 'innovation_rate', label: 'Innovation Rate', min: 0, max: 100, step: 1, unit: '%' },
    { id: 'energy_efficiency', label: 'Energy Efficiency', min: 0, max: 100, step: 1, unit: '%' },
    { id: 'biodiversity', label: 'Biodiversity Index', min: 0, max: 100, step: 1, unit: '%' },
    { id: 'urbanization', label: 'Urbanization Level', min: 0, max: 100, step: 1, unit: '%' },
    { id: 'inequality', label: 'Income Inequality', min: 0, max: 100, step: 1, unit: '%' },
    { id: 'trade_openness', label: 'Trade Openness', min: 0, max: 100, step: 1, unit: '%' },
    { id: 'corruption_level', label: 'Corruption Level', min: 0, max: 100, step: 1, unit: '%' },
    { id: 'military_spending', label: 'Military Spending', min: 0, max: 100, step: 1, unit: '% of GDP' },
    { id: 'renewable_energy', label: 'Renewable Energy', min: 0, max: 100, step: 1, unit: '%' },
    { id: 'water_security', label: 'Water Security', min: 0, max: 100, step: 1, unit: '%' },
    { id: 'food_security', label: 'Food Security', min: 0, max: 100, step: 1, unit: '%' },
    { id: 'cyber_security', label: 'Cyber Security', min: 0, max: 100, step: 1, unit: '%' },
    { id: 'demographic_dividend', label: 'Demographic Dividend', min: 0, max: 100, step: 1, unit: '%' },
    { id: 'global_connectivity', label: 'Global Connectivity', min: 0, max: 100, step: 1, unit: '%' }
  ];

  const handleSliderChange = (param, value) => {
    setParameters(prev => ({
      ...prev,
      [param]: value
    }));
  };

  const handleCardSliderChange = (cardId, value) => {
    setParameterCards(prev => 
      prev.map(card => 
        card.id === cardId 
          ? { ...card, value: value }
          : card
      )
    );
  };

  const handleAddParameterCard = () => {
    const newCard = {
      id: nextCardId,
      parameterId: 'population',
      value: 50,
      order: parameterCards.length
    };
    setParameterCards(prev => [...prev, newCard]);
    setNextCardId(prev => prev + 1);
  };

  const handleRemoveParameterCard = (cardId) => {
    setParameterCards(prev => prev.filter(card => card.id !== cardId));
  };

  const handleParameterCardChange = (cardId, parameterId) => {
    setParameterCards(prev => 
      prev.map(card => 
        card.id === cardId 
          ? { ...card, parameterId, value: 50 }
          : card
      )
    );
  };

  const getParameterInfo = (parameterId) => {
    return worldModelParameters.find(p => p.id === parameterId) || worldModelParameters[0];
  };

  const formatParameterValue = (value, parameterId) => {
    const param = getParameterInfo(parameterId);
    if (parameterId === 'population') {
      return `${(value / 1000000000).toFixed(1)}B`;
    }
    return `${value}${param.unit}`;
  };

  const handleRunSimulation = () => {
    console.log('Running simulation with parameters:', parameters);
    console.log('Parameter cards:', parameterCards);
    console.log('Input mode:', inputMode);
    console.log('Free text input:', freeTextInput);
    console.log('Depth level:', depthLevel);
    
    // Add log entry
    const newLog = {
      id: logs.length + 1,
      timestamp: new Date().toISOString(),
      message: `Running simulation with ${parameterCards.length} parameters`,
      type: 'info'
    };
    setLogs(prev => [...prev, newLog]);
    
    // Here you would trigger the actual simulation
  };

  const handlePhaseChange = (phase) => {
    setActivePhase(phase);
    
    // Add log entry
    const newLog = {
      id: logs.length + 1,
      timestamp: new Date().toISOString(),
      message: `Switched to ${phase} phase`,
      type: 'info'
    };
    setLogs(prev => [...prev, newLog]);
  };

  const formatLogTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  return (
    <div className="App">
      {/* Main Header */}
      <div className="main-header">
        <h1 className="main-title">World model</h1>
        <p className="main-subtitle">LLM driven dynamic world model</p>
      </div>

      <div className="simulation-container">
        {/* Left Panel - Controls */}
        <div className="controls-panel">
          
          {/* Phase Title and Buttons */}
          <div className="phase-section">
            <h2 className="phase-title">Initialization, training, inference</h2>
            <div className="phase-buttons">
              <button 
                className={`phase-btn ${activePhase === 'initialization' ? 'active' : ''}`}
                onClick={() => handlePhaseChange('initialization')}
              >
                Initialization
              </button>
              <button 
                className={`phase-btn ${activePhase === 'training' ? 'active' : ''}`}
                onClick={() => handlePhaseChange('training')}
              >
                Training
              </button>
            </div>
          </div>

          {/* Mode Selection and Depth Level */}
          <div className="top-controls">
            <div className="mode-selection">
              <h3>Input Mode</h3>
              <div className="mode-buttons">
                <button 
                  className={`mode-btn ${inputMode === 'dropdown' ? 'active' : ''}`}
                  onClick={() => setInputMode('dropdown')}
                >
                  Drop-down
                </button>
                <button 
                  className={`mode-btn ${inputMode === 'freetext' ? 'active' : ''}`}
                  onClick={() => setInputMode('freetext')}
                >
                  Free Text
                </button>
              </div>
            </div>

            <div className="depth-control">
              <label>Depth Level</label>
              <select
                value={depthLevel}
                onChange={(e) => setDepthLevel(parseInt(e.target.value))}
                className="depth-dropdown"
              >
                <option value={1}>Level 1</option>
                <option value={2}>Level 2</option>
                <option value={3}>Level 3</option>
                <option value={4}>Level 4</option>
                <option value={5}>Level 5</option>
              </select>
            </div>
          </div>

          {/* Conditional Content Based on Mode */}
          {inputMode === 'freetext' ? (
            <div className="freetext-section">
              <h2>AI Parameter Analysis</h2>
              <div className="freetext-input-container">
                <textarea
                  value={freeTextInput}
                  onChange={(e) => setFreeTextInput(e.target.value)}
                  placeholder="Describe the scenario you want to analyze. For example: 'A world where climate change accelerates, leading to mass migration and resource conflicts..'"
                  className="freetext-input"
                  rows="8"
                />
              </div>
            </div>
          ) : (
            <div className="dropdown-section">
              <div className="parameters-header">
                <h2>External Factors</h2>
                <button onClick={handleAddParameterCard} className="add-parameter-btn">
                  + Add Parameter
                </button>
              </div>

              <div className="parameter-cards">
                {parameterCards.map((card) => {
                  const paramInfo = getParameterInfo(card.parameterId);
                  return (
                    <div key={card.id} className="parameter-card">
                      <div className="card-header">
                        <select
                          value={card.parameterId}
                          onChange={(e) => handleParameterCardChange(card.id, e.target.value)}
                          className="parameter-select"
                        >
                          {worldModelParameters.map(param => (
                            <option key={param.id} value={param.id}>
                              {param.label}
                            </option>
                          ))}
                        </select>
                        <div className="card-controls">
                          <button 
                            onClick={() => handleRemoveParameterCard(card.id)}
                            className="remove-card-btn"
                          >
                            ×
                          </button>
                        </div>
                      </div>
                      <div className="card-slider">
                        <input
                          type="range"
                          min={paramInfo.min}
                          max={paramInfo.max}
                          step={paramInfo.step}
                          value={card.value}
                          onChange={(e) => handleCardSliderChange(card.id, parseInt(e.target.value))}
                          className="slider"
                        />
                        <span className="parameter-value">
                          {formatParameterValue(card.value, card.parameterId)}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Run Button */}
          <button onClick={handleRunSimulation} className="run-button">
            🚀 Run Simulation
          </button>
        </div>

        {/* Right Panel - Results */}
        <div className="results-panel">
          <h2>Simulation Results</h2>
          <div className="results-content">
            <div className="simple-placeholder">
              <p>Mock results will be shown here soon.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Logs Container */}
      <div className="logs-container">
        <div className="logs-header">
          <h3>System Logs</h3>
          <button 
            onClick={() => setLogs([])}
            className="clear-logs-btn"
          >
            Clear Logs
          </button>
        </div>
        <div className="logs-content">
          {logs.map(log => (
            <div key={log.id} className={`log-entry ${log.type}`}>
              <span className="log-timestamp">{formatLogTimestamp(log.timestamp)}</span>
              <span className="log-message">{log.message}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default App; 
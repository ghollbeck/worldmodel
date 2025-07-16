import React, { useState, ChangeEvent } from 'react';
import './App.css';

type InputMode = 'dropdown' | 'freetext';
type Phase = 'initialization' | 'training';

type ParameterId =
  | 'population'
  | 'economy'
  | 'environment'
  | 'technology'
  | 'health'
  | 'education'
  | 'governance'
  | 'climate_stability'
  | 'resource_scarcity'
  | 'social_cohesion'
  | 'political_stability'
  | 'innovation_rate'
  | 'energy_efficiency'
  | 'biodiversity'
  | 'urbanization'
  | 'inequality'
  | 'trade_openness'
  | 'corruption_level'
  | 'military_spending'
  | 'renewable_energy'
  | 'water_security'
  | 'food_security'
  | 'cyber_security'
  | 'demographic_dividend'
  | 'global_connectivity';

interface ParameterCard {
  id: number;
  parameterId: ParameterId;
  value: number;
  order: number;
}

interface WorldModelParameter {
  id: ParameterId;
  label: string;
  min: number;
  max: number;
  step: number;
  unit: string;
}

interface LogEntry {
  id: number;
  timestamp: string;
  message: string;
  type: 'info' | 'error' | 'warning';
}

// Fix: Use an index signature compatible with JS/TS transpilation
type Parameters = Partial<Record<ParameterId, number>>;

const worldModelParameters: WorldModelParameter[] = [
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

const initialParameters: Parameters = {
  population: 7800000000,
  economy: 75,
  environment: 60,
  technology: 80,
  health: 70,
  education: 65,
  governance: 55
};

const App: React.FC = () => {
  const [parameters, setParameters] = useState<Parameters>(initialParameters);

  const [inputMode, setInputMode] = useState<InputMode>('dropdown');
  const [freeTextInput, setFreeTextInput] = useState<string>('');

  const [parameterCards, setParameterCards] = useState<ParameterCard[]>([]);
  const [nextCardId, setNextCardId] = useState<number>(1);

  const [depthLevel, setDepthLevel] = useState<number>(3);

  const [activePhase, setActivePhase] = useState<Phase>('initialization');

  const [logs, setLogs] = useState<LogEntry[]>([
    { id: 1, timestamp: new Date().toISOString(), message: 'System initialized', type: 'info' },
    { id: 2, timestamp: new Date().toISOString(), message: 'Ready for initialization phase', type: 'info' }
  ]);

  const handleSliderChange = (param: ParameterId, value: number) => {
    setParameters(prev => ({
      ...prev,
      [param]: value
    }));
  };

  const handleCardSliderChange = (cardId: number, value: number) => {
    setParameterCards(prev =>
      prev.map(card =>
        card.id === cardId
          ? { ...card, value }
          : card
      )
    );
  };

  const handleAddParameterCard = () => {
    const newCard: ParameterCard = {
      id: nextCardId,
      parameterId: 'population',
      value: 50,
      order: parameterCards.length
    };
    setParameterCards(prev => [...prev, newCard]);
    setNextCardId(prev => prev + 1);
  };

  const handleRemoveParameterCard = (cardId: number) => {
    setParameterCards(prev => prev.filter(card => card.id !== cardId));
  };

  const handleParameterCardChange = (cardId: number, parameterId: string) => {
    setParameterCards(prev =>
      prev.map(card =>
        card.id === cardId
          ? { ...card, parameterId: parameterId as ParameterId, value: 50 }
          : card
      )
    );
  };

  const getParameterInfo = (parameterId: string): WorldModelParameter => {
    return worldModelParameters.find(p => p.id === parameterId) || worldModelParameters[0];
  };

  const formatParameterValue = (value: number, parameterId: string): string => {
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

    const newLog: LogEntry = {
      id: logs.length + 1,
      timestamp: new Date().toISOString(),
      message: `Running simulation with ${parameterCards.length} parameters`,
      type: 'info'
    };
    setLogs(prev => [...prev, newLog]);
    // Here you would trigger the actual simulation
  };

  const handlePhaseChange = (phase: Phase) => {
    setActivePhase(phase);

    const newLog: LogEntry = {
      id: logs.length + 1,
      timestamp: new Date().toISOString(),
      message: `Switched to ${phase} phase`,
      type: 'info'
    };
    setLogs(prev => [...prev, newLog]);
  };

  const formatLogTimestamp = (timestamp: string): string => {
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
                Run Initialization
              </button>
              <button
                className={`phase-btn ${activePhase === 'training' ? 'active' : ''}`}
                onClick={() => handlePhaseChange('training')}
              >
                Run Training
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
                onChange={(e: ChangeEvent<HTMLSelectElement>) => setDepthLevel(parseInt(e.target.value))}
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
                  onChange={(e: ChangeEvent<HTMLTextAreaElement>) => setFreeTextInput(e.target.value)}
                  placeholder="Describe the scenario you want to analyze. For example: 'A world where climate change accelerates, leading to mass migration and resource conflicts..'"
                  className="freetext-input"
                  rows={8}
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
                          onChange={(e: ChangeEvent<HTMLSelectElement>) => handleParameterCardChange(card.id, e.target.value)}
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
                          onChange={(e: ChangeEvent<HTMLInputElement>) => handleCardSliderChange(card.id, parseInt(e.target.value))}
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
};

export default App;
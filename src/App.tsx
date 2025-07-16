import React, { useState, useEffect, ChangeEvent } from 'react';
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

interface GenerationConfig {
  provider: string;
  model: string;
  num_actors: number;
  num_subactors: number;
  target_depth: number;
  skip_on_error: boolean;
  num_params: number;
}

interface GenerationStatus {
  status: 'idle' | 'running' | 'completed' | 'failed';
  message: string;
  progress?: number;
  details?: any;
}

interface RunInfo {
  status: string;
  run_folder?: string;
  level_files?: Array<{
    level: number;
    file: string;
    size: number;
    modified: number;
  }>;
  total_levels?: number;
}

type Parameters = {
  [key in ParameterId]?: number;
};

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

const providerOptions = [
  { value: 'anthropic', label: 'Anthropic' },
  { value: 'openai', label: 'OpenAI' }
];

const modelOptions = {
  anthropic: [
    { value: 'claude-3-5-sonnet-latest', label: 'Claude 3.5 Sonnet (Latest)' },
    { value: 'claude-3-5-sonnet-20241022', label: 'Claude 3.5 Sonnet (Oct 2024)' },
    { value: 'claude-3-5-haiku-20241022', label: 'Claude 3.5 Haiku (Oct 2024)' },
    { value: 'claude-3-sonnet-20240229', label: 'Claude 3 Sonnet' },
    { value: 'claude-3-haiku-20240307', label: 'Claude 3 Haiku' },
    { value: 'claude-3-opus-20240229', label: 'Claude 3 Opus' }
  ],
  openai: [
    { value: 'gpt-4o', label: 'GPT-4o' },
    { value: 'gpt-4o-mini', label: 'GPT-4o Mini' },
    { value: 'gpt-4', label: 'GPT-4' },
    { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
    { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' }
  ]
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
  const [nextLogId, setNextLogId] = useState<number>(3);

  // New state for generation controls
  const [generationConfig, setGenerationConfig] = useState<GenerationConfig>({
    provider: 'anthropic',
    model: 'claude-3-5-sonnet-latest',
    num_actors: 4, // changed from 10 to 4
    num_subactors: 4, // changed from 8 to 4
    target_depth: 3, // changed from 2 to 3
    skip_on_error: true, // unchanged
    num_params: 20
  });

  const [generationStatus, setGenerationStatus] = useState<{
    actors: GenerationStatus;
    parameters: GenerationStatus;
  }>({
    actors: { status: 'idle', message: 'Ready to generate actors' },
    parameters: { status: 'idle', message: 'Ready to generate parameters' }
  });

  const [runInfo, setRunInfo] = useState<RunInfo>({ status: 'no_runs' });
  const [actorData, setActorData] = useState<any>(null);

  // Poll for status updates
  // useEffect(() => {
  //   const pollStatus = async () => {
  //     try {
  //       const response = await fetch('http://localhost:8000/api/status');
  //       const status = await response.json();
  //       setGenerationStatus(status);
        
  //       // Update logs with status changes
  //       if (status.actors.status === 'completed' && generationStatus.actors.status === 'running') {
  //         addLog('Actor generation completed successfully', 'info');
  //         fetchRunInfo();
  //       } else if (status.actors.status === 'failed' && generationStatus.actors.status === 'running') {
  //         addLog('Actor generation failed', 'error');
  //       }
        
  //       if (status.parameters.status === 'completed' && generationStatus.parameters.status === 'running') {
  //         addLog('Parameter generation completed successfully', 'info');
  //         fetchRunInfo();
  //       } else if (status.parameters.status === 'failed' && generationStatus.parameters.status === 'running') {
  //         addLog('Parameter generation failed', 'error');
  //       }
  //     } catch (error) {
  //       console.error('Failed to fetch status:', error);
  //     }
  //   };

  //   const interval = setInterval(pollStatus, 2000);
  //   return () => clearInterval(interval);
  // }, [generationStatus.actors.status, generationStatus.parameters.status]);

  // Fetch run info on component mount
  useEffect(() => {
    fetchRunInfo();
  }, []);

  const fetchRunInfo = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/runs/latest');
      const info = await response.json();
      setRunInfo(info);
      
      // Fetch actor data if available
      if (info.status === 'found' && info.total_levels > 0) {
        const dataResponse = await fetch('http://localhost:8000/api/runs/data/0');
        const data = await dataResponse.json();
        setActorData(data);
      }
    } catch (error) {
      console.error('Failed to fetch run info:', error);
    }
  };

  const addLog = (message: string, type: 'info' | 'error' | 'warning') => {
    const newLog: LogEntry = {
      id: nextLogId,
      timestamp: new Date().toISOString(),
      message,
      type
    };
    setLogs(prev => [...prev, newLog]);
    setNextLogId(prev => prev + 1);
  };

  const handleGenerationConfigChange = (key: keyof GenerationConfig, value: any) => {
    setGenerationConfig(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleGenerateActors = async () => {
    if (generationStatus.actors.status === 'running') {
      addLog('Actor generation is already running', 'warning');
      return;
    }

    try {
      addLog(`Starting actor generation with ${generationConfig.num_actors} actors`, 'info');
      
      const response = await fetch('http://localhost:8000/api/generate/actors', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          provider: generationConfig.provider,
          model: generationConfig.model,
          num_actors: generationConfig.num_actors,
          num_subactors: generationConfig.num_subactors,
          target_depth: generationConfig.target_depth,
          skip_on_error: generationConfig.skip_on_error
        })
      });

      if (response.ok) {
        addLog('Actor generation started successfully', 'info');
      } else {
        const error = await response.json();
        addLog(`Failed to start actor generation: ${error.detail}`, 'error');
      }
    } catch (error) {
      addLog(`Error starting actor generation: ${error}`, 'error');
    }
  };

  const handleGenerateParameters = async () => {
    if (generationStatus.parameters.status === 'running') {
      addLog('Parameter generation is already running', 'warning');
      return;
    }

    if (runInfo.status === 'no_runs') {
      addLog('No actor data found. Please generate actors first.', 'warning');
      return;
    }

    try {
      addLog(`Starting parameter generation with ${generationConfig.num_params} parameters per actor`, 'info');
      
      const response = await fetch('http://localhost:8000/api/generate/parameters', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          provider: generationConfig.provider,
          model: generationConfig.model,
          num_params: generationConfig.num_params
        })
      });

      if (response.ok) {
        addLog('Parameter generation started successfully', 'info');
      } else {
        const error = await response.json();
        addLog(`Failed to start parameter generation: ${error.detail}`, 'error');
      }
    } catch (error) {
      addLog(`Error starting parameter generation: ${error}`, 'error');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return '#ffa500';
      case 'completed': return '#4caf50';
      case 'failed': return '#f44336';
      default: return '#2196f3';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running': return '🔄';
      case 'completed': return '✅';
      case 'failed': return '❌';
      default: return '⚪';
    }
  };

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

    addLog(`Running simulation with ${parameterCards.length} parameters`, 'info');
    // Here you would trigger the actual simulation
  };

  const handlePhaseChange = (phase: Phase) => {
    setActivePhase(phase);
    addLog(`Switched to ${phase} phase`, 'info');
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

          {/* Generation Controls Section */}
          <div className="generation-section">
            <h2 className="section-title">🤖 LLM Generation Controls</h2>
            
            {/* Provider & Model Selection */}
            <div className="generation-config">
              <div className="config-row">
                <div className="config-item">
                  <label>Provider</label>
                  <select
                    value={generationConfig.provider}
                    onChange={(e) => handleGenerationConfigChange('provider', e.target.value)}
                    className="config-select"
                  >
                    {providerOptions.map(option => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="config-item">
                  <label>Model</label>
                  <select
                    value={generationConfig.model}
                    onChange={(e) => handleGenerationConfigChange('model', e.target.value)}
                    className="config-select"
                  >
                    {modelOptions[generationConfig.provider as keyof typeof modelOptions].map(option => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Actor Generation Controls */}
              <div className="config-group">
                <h3>🎭 Actor Generation</h3>
                <div className="config-row">
                  <div className="config-item">
                    <label>Number of Actors (1-200)</label>
                    <input
                      type="range"
                      min="1"
                      max="200"
                      value={generationConfig.num_actors}
                      onChange={(e) => handleGenerationConfigChange('num_actors', parseInt(e.target.value))}
                      className="slider"
                    />
                    <span className="slider-value">{generationConfig.num_actors}</span>
                  </div>
                  <div className="config-item">
                    <label>Sub-actors per Actor (1-20)</label>
                    <input
                      type="range"
                      min="1"
                      max="20"
                      value={generationConfig.num_subactors}
                      onChange={(e) => handleGenerationConfigChange('num_subactors', parseInt(e.target.value))}
                      className="slider"
                    />
                    <span className="slider-value">{generationConfig.num_subactors}</span>
                  </div>
                </div>
                <div className="config-row">
                  <div className="config-item">
                    <label>Target Depth (0-10)</label>
                    <input
                      type="range"
                      min="0"
                      max="10"
                      value={generationConfig.target_depth}
                      onChange={(e) => handleGenerationConfigChange('target_depth', parseInt(e.target.value))}
                      className="slider"
                    />
                    <span className="slider-value">{generationConfig.target_depth}</span>
                  </div>
                  <div className="config-item">
                    <label>Skip on Error</label>
                    <input
                      type="checkbox"
                      checked={generationConfig.skip_on_error}
                      onChange={(e) => handleGenerationConfigChange('skip_on_error', e.target.checked)}
                      className="checkbox"
                    />
                  </div>
                </div>
                
                <div className="generation-button-row">
                  <button
                    onClick={handleGenerateActors}
                    disabled={generationStatus.actors.status === 'running'}
                    className={`generation-btn ${generationStatus.actors.status === 'running' ? 'running' : ''}`}
                  >
                    {getStatusIcon(generationStatus.actors.status)} Generate Actors
                  </button>
                  <div className="status-info">
                    <span style={{ color: getStatusColor(generationStatus.actors.status) }}>
                      {generationStatus.actors.message}
                    </span>
                    {generationStatus.actors.progress !== null && (
                      <div className="progress-bar">
                        <div 
                          className="progress-fill" 
                          style={{ width: `${generationStatus.actors.progress}%` }}
                        />
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Parameter Generation Controls */}
              <div className="config-group">
                <h3>📊 Parameter Generation</h3>
                <div className="config-row">
                  <div className="config-item">
                    <label>Parameters per Actor (10-100)</label>
                    <input
                      type="range"
                      min="10"
                      max="100"
                      value={generationConfig.num_params}
                      onChange={(e) => handleGenerationConfigChange('num_params', parseInt(e.target.value))}
                      className="slider"
                    />
                    <span className="slider-value">{generationConfig.num_params}</span>
                  </div>
                </div>
                
                <div className="generation-button-row">
                  <button
                    onClick={handleGenerateParameters}
                    disabled={generationStatus.parameters.status === 'running' || runInfo.status === 'no_runs'}
                    className={`generation-btn ${generationStatus.parameters.status === 'running' ? 'running' : ''}`}
                  >
                    {getStatusIcon(generationStatus.parameters.status)} Generate Parameters
                  </button>
                  <div className="status-info">
                    <span style={{ color: getStatusColor(generationStatus.parameters.status) }}>
                      {generationStatus.parameters.message}
                    </span>
                    {generationStatus.parameters.progress !== null && (
                      <div className="progress-bar">
                        <div 
                          className="progress-fill" 
                          style={{ width: `${generationStatus.parameters.progress}%` }}
                        />
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>

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
          <h2>Generation Results</h2>
          <div className="results-content">
            {runInfo.status === 'found' ? (
              <div className="results-data">
                <div className="run-info">
                  <h3>📁 Latest Run: {runInfo.run_folder}</h3>
                  <p>Total Levels: {runInfo.total_levels}</p>
                  {runInfo.level_files && runInfo.level_files.map(file => (
                    <div key={file.level} className="level-info">
                      <strong>Level {file.level}:</strong> {file.file} ({(file.size / 1024).toFixed(1)} KB)
                    </div>
                  ))}
                </div>
                
                {actorData && actorData.actors && (
                  <div className="actor-preview">
                    <h3>🎭 Generated Actors ({actorData.actors.length})</h3>
                    <div className="actor-list">
                      {actorData.actors.slice(0, 5).map((actor: any, index: number) => (
                        <div key={index} className="actor-item">
                          <strong>{actor.name}</strong> ({actor.type})
                          <p className="actor-description">{actor.description}</p>
                          {actor.sub_actors && actor.sub_actors.length > 0 && (
                            <p className="sub-actors-count">
                              Sub-actors: {actor.sub_actors.length}
                            </p>
                          )}
                        </div>
                      ))}
                      {actorData.actors.length > 5 && (
                        <div className="actor-item">
                          <strong>... and {actorData.actors.length - 5} more actors</strong>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="no-results">
                <p>No generation results yet. Use the controls above to generate actors and parameters.</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Logs Container */}
      <div className="logs-container">
        <div className="logs-header">
          <h3>System Logs</h3>
          <button
            onClick={() => {
              setLogs([]);
              setNextLogId(1);
            }}
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
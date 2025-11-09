import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { AlertTriangle, RefreshCw, Activity, Database } from 'lucide-react';

const TMobileCHIDashboard = () => {
  const [selectedRegion, setSelectedRegion] = useState('Dallas');
  const [chiData, setCHIData] = useState({});
  const [historicalData, setHistoricalData] = useState({});
  const [alerts, setAlerts] = useState([]);
  const [kudos, setKudos] = useState([]);
  const [outageParams, setOutageParams] = useState({ impact: 50, duration: 30 });
  const [question, setQuestion] = useState('');
  const [chatResponse, setChatResponse] = useState('');
  const [autoRefresh, setAutoRefresh] = useState(true);

  const regions = [
    { name: 'Dallas', lat: 32.7767, lng: -96.7970 },
    { name: 'Seattle', lat: 47.6062, lng: -122.3321 },
    { name: 'New York', lat: 40.7128, lng: -74.0060 },
    { name: 'Los Angeles', lat: 34.0522, lng: -118.2437 },
    { name: 'Chicago', lat: 41.8781, lng: -87.6298 },
    { name: 'Miami', lat: 25.7617, lng: -80.1918 }
  ];

  const calculateCHI = (sentiment, nps_health, volume_delta) => {
    return (sentiment * 0.4 + nps_health * 0.4 + (1 + volume_delta) * 0.2) * 100;
  };

  const generateBaselineData = (region) => {
    const sentiment = 0.6 + Math.random() * 0.3;
    const nps_health = 0.7 + Math.random() * 0.25;
    const volume_delta = -0.2 + Math.random() * 0.3;
    
    const chi = calculateCHI(sentiment, nps_health, volume_delta);
    
    const keywords = ['5G speed', 'customer service', 'coverage', 'plans', 'network quality']
      .sort(() => Math.random() - 0.5)
      .slice(0, 3);
    
    return {
      region,
      chi,
      sentiment,
      nps_health,
      volume_delta,
      keywords,
      timestamp: new Date().toISOString()
    };
  };

  const initializeData = () => {
    const newCHIData = {};
    const newHistoricalData = {};
    
    regions.forEach(region => {
      const data = generateBaselineData(region.name);
      newCHIData[region.name] = data;

      const history = [];
      const baseTime = new Date().getTime() - 3600000; 
      for (let i = 0; i < 12; i++) {
        const timestamp = new Date(baseTime + i * 300000); 
        const chi = data.chi + (Math.random() - 0.5) * 10;
        history.push({
          timestamp: timestamp.toISOString(),
          chi: Math.max(0, Math.min(100, chi))
        });
      }
      newHistoricalData[region.name] = history;
    });
    
    setCHIData(newCHIData);
    setHistoricalData(newHistoricalData);

    setKudos([
      {
        id: 1,
        timestamp: new Date().toISOString(),
        region: 'Seattle',
        feedback: 'Amazing 5G speeds! Best network I\'ve ever used.'
      }
    ]);
  };

  const simulateOutage = () => {
    const current = chiData[selectedRegion];
    if (!current) return;
    
    const chi_before = current.chi;
    const impact_factor = outageParams.impact / 100;
    
    const sentiment_drop = impact_factor * (0.3 + Math.random() * 0.3);
    const nps_drop = impact_factor * (0.2 + Math.random() * 0.2);
    const volume_spike = impact_factor * (0.5 + Math.random() * 1.0);
    
    const new_sentiment = Math.max(0, current.sentiment - sentiment_drop);
    const new_nps = Math.max(0, current.nps_health - nps_drop);
    const new_volume = current.volume_delta + volume_spike;
    
    const new_chi = calculateCHI(new_sentiment, new_nps, new_volume);

    setCHIData(prev => ({
      ...prev,
      [selectedRegion]: {
        ...prev[selectedRegion],
        chi: new_chi,
        sentiment: new_sentiment,
        nps_health: new_nps,
        volume_delta: new_volume,
        keywords: ['outage', 'down', 'slow', 'network issue', 'service problem'],
        timestamp: new Date().toISOString()
      }
    }));

    setHistoricalData(prev => ({
      ...prev,
      [selectedRegion]: [
        ...prev[selectedRegion],
        {
          timestamp: new Date().toISOString(),
          chi: new_chi
        }
      ].slice(-20)
    }));

    if (chi_before - new_chi >= 10) {
      const newAlert = {
        id: alerts.length + 1,
        timestamp: new Date().toISOString(),
        region: selectedRegion,
        chi_before: chi_before,
        chi_after: new_chi,
        reason: `CHI drop ≥10 and <60 | topics: outage, down, slow`,
        recommendation: 'Investigate local towers    Notify customers via SMS    Escalate to NOC if persists'
      };
      setAlerts(prev => [...prev, newAlert]);
    }
  };

  const answerQuestion = (q) => {
    const question = q.toLowerCase();
    
    if (question.includes('drop') || question.includes('decrease')) {
      const region = question.includes('dallas') ? 'Dallas' : selectedRegion;
      return `The CHI drop in ${region} was likely caused by a network outage or service degradation. This typically affects customer sentiment and increases support volume. Recommended actions: investigate tower status, notify affected customers, and escalate to NOC.`;
    }
    
    if (question.includes('improve') || question.includes('increase')) {
      return 'To improve CHI scores, focus on: 1) Reducing network outages and improving coverage, 2) Enhancing customer service response times, 3) Proactive communication during issues, 4) Addressing billing concerns quickly.';
    }
    
    if (question.includes('alert')) {
      return `Currently tracking ${alerts.length} alerts. Alerts are triggered when CHI drops ≥10 points or falls below 60. Each alert includes recommendations for remediation.`;
    }
    
    return 'I can help you understand CHI data, explain drops or improvements, and provide recommendations for enhancing customer happiness. What would you like to know?';
  };

  useEffect(() => {
    initializeData();
  }, []);

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => {
        setCHIData(prev => {
          const updated = { ...prev };
          Object.keys(updated).forEach(region => {
            const current = updated[region];
            const fluctuation = (Math.random() - 0.5) * 0.05;
            updated[region] = {
              ...current,
              chi: Math.max(0, Math.min(100, current.chi + fluctuation * 10))
            };
          });
          return updated;
        });
      }, 5000);
      
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const getMapPosition = (lat, lng) => {
    const x = ((lng + 180) / 360) * 100;
    const latRad = (lat * Math.PI) / 180;
    const mercN = Math.log(Math.tan(Math.PI / 4 + latRad / 2));
    const y = 50 - (50 * mercN) / (2 * Math.PI);
    return { x, y };
  };

  const currentCHI = chiData[selectedRegion] || {};
  const currentHistory = historicalData[selectedRegion] || [];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900">
            T-Mobile Customer Happiness Index (CHI) — MVP
          </h1>
          <div className="flex items-center gap-2">
            <Activity className={`w-4 h-4 ${autoRefresh ? 'text-green-600 animate-pulse' : 'text-gray-400'}`} />
            <span className="text-sm text-gray-600">Live</span>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <aside className="w-64 bg-white border-r border-gray-200 p-6 space-y-6">
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-2">API</h3>
            <div className="text-xs text-gray-600">
              <div className="font-medium mb-1">FastAPI base URL</div>
              <div className="bg-gray-100 p-2 rounded font-mono text-xs break-all">
                http://127.0.0.1:8000
              </div>
            </div>
          </div>

          <button 
            onClick={initializeData}
            className="w-full px-4 py-2 text-sm font-medium text-white bg-pink-600 rounded hover:bg-pink-700 flex items-center justify-center gap-2"
          >
            <Database className="w-4 h-4" />
            Load Seed Data
          </button>

          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Outage Simulator</h3>
            <div className="space-y-3">
              <div>
                <label className="text-xs text-gray-600">Region</label>
                <select 
                  value={selectedRegion}
                  onChange={(e) => setSelectedRegion(e.target.value)}
                  className="w-full mt-1 px-3 py-2 border border-gray-300 rounded text-sm"
                >
                  {regions.map(r => <option key={r.name}>{r.name}</option>)}
                </select>
              </div>
              
              <div>
                <label className="text-xs text-gray-600">Impact %</label>
                <div className="flex items-center gap-2 mt-1">
                  <button 
                    onClick={() => setOutageParams(p => ({...p, impact: Math.max(0, p.impact - 10)}))} 
                    className="px-2 py-1 border rounded hover:bg-gray-50"
                  >
                    −
                  </button>
                  <input 
                    type="number" 
                    value={outageParams.impact}
                    onChange={(e) => setOutageParams(p => ({...p, impact: parseInt(e.target.value) || 0}))}
                    className="w-full px-3 py-1 border rounded text-sm text-center"
                  />
                  <button 
                    onClick={() => setOutageParams(p => ({...p, impact: Math.min(100, p.impact + 10)}))} 
                    className="px-2 py-1 border rounded hover:bg-gray-50"
                  >
                    +
                  </button>
                </div>
              </div>

              <div>
                <label className="text-xs text-gray-600">Duration (min)</label>
                <div className="flex items-center gap-2 mt-1">
                  <button 
                    onClick={() => setOutageParams(p => ({...p, duration: Math.max(5, p.duration - 5)}))} 
                    className="px-2 py-1 border rounded hover:bg-gray-50"
                  >
                    −
                  </button>
                  <input 
                    type="number" 
                    value={outageParams.duration}
                    onChange={(e) => setOutageParams(p => ({...p, duration: parseInt(e.target.value) || 5}))}
                    className="w-full px-3 py-1 border rounded text-sm text-center"
                  />
                  <button 
                    onClick={() => setOutageParams(p => ({...p, duration: p.duration + 5}))} 
                    className="px-2 py-1 border rounded hover:bg-gray-50"
                  >
                    +
                  </button>
                </div>
              </div>

              <button 
                onClick={simulateOutage}
                className="w-full px-4 py-2 text-sm font-medium text-white bg-pink-600 rounded hover:bg-pink-700"
              >
                Run Simulation
              </button>
            </div>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Engineer Chatbot</h3>
            <div className="space-y-2">
              <div className="text-xs text-gray-600 mb-1">Ask a question</div>
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Why did CHI drop in Dallas?"
                className="w-full px-3 py-2 border border-gray-300 rounded text-sm resize-none"
                rows="3"
              />
              <button 
                onClick={() => setChatResponse(answerQuestion(question))}
                className="w-full px-4 py-2 text-sm font-medium text-white bg-pink-600 rounded hover:bg-pink-700"
              >
                Ask
              </button>
              {chatResponse && (
                <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded text-xs">
                  {chatResponse}
                </div>
              )}
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-6">
          <button 
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`mb-4 px-4 py-2 text-sm font-medium rounded flex items-center gap-2 ${
              autoRefresh ? 'bg-green-600 text-white hover:bg-green-700' : 'bg-gray-300 text-gray-700 hover:bg-gray-400'
            }`}
          >
            <RefreshCw className={`w-4 h-4 ${autoRefresh ? 'animate-spin' : ''}`} />
            {autoRefresh ? 'Auto-Refresh ON' : 'Auto-Refresh OFF'}
          </button>

          <div className="grid grid-cols-3 gap-6 mb-6">
            {/* Map Section */}
            <div className="col-span-2 bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-bold mb-4">Regional Mood Map</h2>
              <div className="h-96 rounded relative overflow-hidden bg-white">
                <img 
                  src="https://eoimages.gsfc.nasa.gov/images/imagerecords/73000/73909/world.topo.bathy.200412.3x5400x2700.jpg"
                  alt="World Map"
                  className="w-full h-full object-cover opacity-90"
                  onError={(e) => {
                    e.target.onerror = null;
                    e.target.src = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Equirectangular_projection_SW.jpg/1280px-Equirectangular_projection_SW.jpg";
                  }}
                />
                {/* Region markers overlay */}
                <div className="absolute inset-0">
                  {regions.map(region => {
                    const positions = {
                      'Seattle': { left: '16%', top: '32%' },
                      'Los Angeles': { left: '14%', top: '48%' },
                      'Dallas': { left: '21%', top: '50%' },
                      'Chicago': { left: '23%', top: '42%' },
                      'New York': { left: '27%', top: '40%' },
                      'Miami': { left: '26%', top: '56%' }
                    };
                    
                    const pos = positions[region.name];
                    const regionCHI = chiData[region.name]?.chi || 70;
                    const color = regionCHI > 70 ? '#10b981' : regionCHI > 50 ? '#f59e0b' : '#ef4444';
                    
                    return (
                      <div
                        key={region.name}
                        className="absolute cursor-pointer transition-all hover:scale-110"
                        style={{
                          left: pos.left,
                          top: pos.top,
                          transform: 'translate(-50%, -50%)'
                        }}
                        onClick={() => setSelectedRegion(region.name)}
                      >
                        <div
                          className="w-4 h-4 rounded-full border-2 border-white shadow-lg"
                          style={{ backgroundColor: color }}
                        />
                        {selectedRegion === region.name && (
                          <>
                            <div
                              className="absolute inset-0 w-7 h-7 rounded-full border-2 animate-pulse"
                              style={{ 
                                borderColor: color,
                                left: '50%',
                                top: '50%',
                                transform: 'translate(-50%, -50%)'
                              }}
                            />
                            <div className="absolute left-1/2 -top-8 transform -translate-x-1/2 bg-gray-900 text-white px-3 py-1 rounded text-xs font-bold whitespace-nowrap shadow-xl z-10">
                              {region.name}
                            </div>
                          </>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* CHI Metrics */}
            <div className="bg-white rounded-lg shadow p-6">
              <div className="mb-4">
                <label className="text-sm text-gray-600">Select region</label>
                <select 
                  value={selectedRegion}
                  onChange={(e) => setSelectedRegion(e.target.value)}
                  className="w-full mt-1 px-3 py-2 border border-gray-300 rounded"
                >
                  {regions.map(r => <option key={r.name}>{r.name}</option>)}
                </select>
              </div>

              <div className="space-y-4">
                <div>
                  <div className="text-sm text-gray-600">CHI</div>
                  <div className={`text-4xl font-bold ${
                    currentCHI.chi > 70 ? 'text-green-600' : 
                    currentCHI.chi > 50 ? 'text-yellow-600' : 'text-red-600'
                  }`}>
                    {currentCHI.chi?.toFixed(1) || '0.0'}
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <div className="text-xs text-gray-600">Sentiment</div>
                    <div className="text-lg font-semibold">{currentCHI.sentiment?.toFixed(2) || '0.00'}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-600">NPS health</div>
                    <div className="text-lg font-semibold">{currentCHI.nps_health?.toFixed(2) || '0.00'}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-600">Vol Δ</div>
                    <div className="text-lg font-semibold">{currentCHI.volume_delta?.toFixed(2) || '0.00'}</div>
                  </div>
                </div>

                <div>
                  <div className="text-sm text-gray-600 mb-2">Top keywords:</div>
                  <div className="flex flex-wrap gap-2">
                    {currentCHI.keywords?.map((kw, i) => (
                      <span key={i} className="px-2 py-1 bg-gray-100 text-xs rounded">{kw}</span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Historical Chart */}
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h3 className="text-lg font-semibold mb-3">CHI Trend - {selectedRegion}</h3>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={currentHistory}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis 
                  dataKey="timestamp" 
                  tick={{ fontSize: 11 }}
                  tickFormatter={(value) => new Date(value).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
                />
                <YAxis tick={{ fontSize: 11 }} domain={[0, 100]} />
                <Tooltip 
                  labelFormatter={(value) => new Date(value).toLocaleString()}
                  formatter={(value) => [value.toFixed(1), 'CHI']}
                />
                <Line type="monotone" dataKey="chi" stroke="#ec4899" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Alerts */}
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-red-600" />
              Alerts (recent)
            </h2>
            {alerts.length === 0 ? (
              <div className="text-gray-500 text-sm bg-gray-50 p-4 rounded">No alerts yet.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left">ID</th>
                      <th className="px-4 py-2 text-left">Timestamp</th>
                      <th className="px-4 py-2 text-left">Region</th>
                      <th className="px-4 py-2 text-left">CHI Before</th>
                      <th className="px-4 py-2 text-left">CHI After</th>
                      <th className="px-4 py-2 text-left">Reason</th>
                      <th className="px-4 py-2 text-left">Recommendation</th>
                    </tr>
                  </thead>
                  <tbody>
                    {alerts.map((alert, i) => (
                      <tr key={i} className="border-t hover:bg-gray-50">
                        <td className="px-4 py-2">{alert.id}</td>
                        <td className="px-4 py-2">{new Date(alert.timestamp).toLocaleTimeString()}</td>
                        <td className="px-4 py-2 font-medium">{alert.region}</td>
                        <td className="px-4 py-2">{alert.chi_before?.toFixed(1)}</td>
                        <td className="px-4 py-2 text-red-600 font-semibold">{alert.chi_after?.toFixed(1)}</td>
                        <td className="px-4 py-2 text-xs">{alert.reason}</td>
                        <td className="px-4 py-2 text-xs text-blue-600">{alert.recommendation}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Kudos */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-4">Kudos (positive feedback)</h2>
            {kudos.length === 0 ? (
              <div className="text-blue-600 bg-blue-50 p-4 rounded">No kudos yet.</div>
            ) : (
              <div className="space-y-3">
                {kudos.map((kudo, i) => (
                  <div key={i} className="p-4 bg-green-50 border border-green-200 rounded hover:shadow-md transition-shadow">
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="font-semibold text-green-800">{kudo.region}</div>
                        <div className="text-sm text-gray-700 mt-1">{kudo.feedback}</div>
                      </div>
                      <div className="text-xs text-gray-500">{new Date(kudo.timestamp).toLocaleTimeString()}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
};

export default TMobileCHIDashboard;

import React from 'react';
import { toast } from 'sonner';
import axios from 'axios';
import { API_BASE } from '../../lib/api.js';

const API = API_BASE;

export const SystemModesSection = ({ systemModes, setSystemModes, token, onEmergencyStop }) => {
  const axiosConfig = { headers: { Authorization: `Bearer ${token}` } };

  const toggleSystemMode = async (mode) => {
    const newValue = !systemModes[mode];
    
    if (mode === 'paperTrading' && newValue) {
      setSystemModes(prev => ({ ...prev, paperTrading: true, liveTrading: false }));
      toast.success('Paper Trading activated. Live Trading disabled.');
    } else if (mode === 'liveTrading' && newValue) {
      if (!window.confirm('⚠️ WARNING: This will enable REAL trading with REAL money. Are you sure?')) {
        return;
      }
      setSystemModes(prev => ({ ...prev, liveTrading: true, paperTrading: false }));
      toast.success('Live Trading activated. Paper Trading disabled.');
    } else {
      setSystemModes(prev => ({ ...prev, [mode]: newValue }));
      toast.success(`${mode} ${newValue ? 'activated' : 'deactivated'}`);
    }
    
    try {
      await axios.put(`${API}/system/mode`, { mode, enabled: newValue }, axiosConfig);
    } catch (err) {
      console.error('Mode toggle error:', err);
      toast.error('Failed to update mode');
    }
  };

  return (
    <div className="dash-section">
      <h2 className="section-title">🔧 System Mode</h2>
      
      <div className="system-modes">
        <div className="mode-item">
          <label className="mode-label">
            <input
              type="checkbox"
              checked={systemModes.paperTrading}
              onChange={() => toggleSystemMode('paperTrading')}
            />
            <span className="mode-text">
              📦 Paper Trading Mode
              <small>Test strategies without real money</small>
            </span>
          </label>
        </div>

        <div className="mode-item">
          <label className="mode-label">
            <input
              type="checkbox"
              checked={systemModes.liveTrading}
              onChange={() => toggleSystemMode('liveTrading')}
            />
            <span className="mode-text live-mode">
              💰 Live Trading Mode
              <small>Trade with real money</small>
            </span>
          </label>
        </div>

        <div className="mode-item">
          <label className="mode-label">
            <input
              type="checkbox"
              checked={systemModes.autopilot}
              onChange={() => toggleSystemMode('autopilot')}
            />
            <span className="mode-text">
              🤖 Autopilot Mode
              <small>AI manages trading automatically</small>
            </span>
          </label>
        </div>
      </div>

      <div className="emergency-controls">
        <button 
          className="emergency-stop-btn" 
          onClick={onEmergencyStop}
        >
          🚨 EMERGENCY STOP
        </button>
        <small>Immediately stops ALL bots and trading</small>
      </div>
    </div>
  );
};

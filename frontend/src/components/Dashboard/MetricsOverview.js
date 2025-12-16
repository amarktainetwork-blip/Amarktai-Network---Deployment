import React from 'react';

export const MetricsOverview = ({ metrics }) => {
  return (
    <div className="metrics-grid">
      <div className="metric-card">
        <div className="metric-icon">💰</div>
        <div className="metric-content">
          <div className="metric-label">Total Profit</div>
          <div className="metric-value">{metrics.totalProfit}</div>
        </div>
      </div>

      <div className="metric-card">
        <div className="metric-icon">🤖</div>
        <div className="metric-content">
          <div className="metric-label">Active Bots</div>
          <div className="metric-value">{metrics.activeBots}</div>
        </div>
      </div>

      <div className="metric-card">
        <div className="metric-icon">📊</div>
        <div className="metric-content">
          <div className="metric-label">Exposure</div>
          <div className="metric-value">{metrics.exposure}</div>
        </div>
      </div>

      <div className="metric-card">
        <div className="metric-icon">⚠️</div>
        <div className="metric-content">
          <div className="metric-label">Risk Level</div>
          <div className="metric-value">{metrics.riskLevel}</div>
        </div>
      </div>

      <div className="metric-card">
        <div className="metric-icon">🧠</div>
        <div className="metric-content">
          <div className="metric-label">AI Sentiment</div>
          <div className="metric-value">{metrics.aiSentiment}</div>
        </div>
      </div>

      <div className="metric-card">
        <div className="metric-icon">🕒</div>
        <div className="metric-content">
          <div className="metric-label">Last Update</div>
          <div className="metric-value">{metrics.lastUpdate}</div>
        </div>
      </div>
    </div>
  );
};

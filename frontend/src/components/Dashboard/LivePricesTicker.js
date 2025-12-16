import React from 'react';

export const LivePricesTicker = ({ livePrices }) => {
  return (
    <div className="live-prices-ticker">
      {Object.entries(livePrices).map(([pair, data]) => {
        const changeClass = data.change >= 0 ? 'positive' : 'negative';
        const changeSymbol = data.change >= 0 ? '+' : '';
        
        return (
          <div key={pair} className="price-item">
            <span className="pair-name">{pair}</span>
            <span className="price-value">R{data.price.toLocaleString()}</span>
            <span className={`price-change ${changeClass}`}>
              {changeSymbol}{data.change.toFixed(2)}%
            </span>
          </div>
        );
      })}
    </div>
  );
};

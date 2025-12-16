import { useEffect, useRef, useState } from 'react';
import { toast } from 'sonner';

/**
 * Custom hook for WebSocket connection management
 * Handles connection, reconnection, and message processing
 */
export const useWebSocket = (token, WS_URL, onMessage) => {
  const wsRef = useRef(null);
  const [connectionStatus, setConnectionStatus] = useState({
    ws: 'Disconnected',
    sse: 'Disconnected'
  });
  const [wsRtt, setWsRtt] = useState('—');

  useEffect(() => {
    if (!token) return;

    let reconnectAttempts = 0;
    const MAX_RECONNECT_ATTEMPTS = 5;

    const connectWebSocket = () => {
      try {
        const wsUrl = `${WS_URL}/api/ws?token=${token}`;
        wsRef.current = new WebSocket(wsUrl);

        wsRef.current.onopen = () => {
          reconnectAttempts = 0;
          setConnectionStatus({ ws: 'Connected', sse: 'Connected' });
          console.log('✅ WebSocket connected');

          const pingInterval = setInterval(() => {
            if (wsRef.current?.readyState === WebSocket.OPEN) {
              const startTime = Date.now();
              wsRef.current.send(JSON.stringify({ 
                type: 'ping', 
                timestamp: startTime 
              }));
            }
          }, 5000);

          wsRef.current.pingInterval = pingInterval;
        };

        wsRef.current.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            
            if (data.type === 'pong') {
              const rtt = Date.now() - data.timestamp;
              setWsRtt(`${rtt}ms`);
            } else {
              onMessage(data);
            }
          } catch (err) {
            console.error('WebSocket message parse error:', err);
          }
        };

        wsRef.current.onclose = () => {
          setConnectionStatus({ ws: 'Disconnected', sse: 'Disconnected' });
          setWsRtt('—');
          
          if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
            reconnectAttempts++;
            setTimeout(() => {
              console.log(`Reconnecting... (${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})`);
              connectWebSocket();
            }, 5000);
          } else {
            console.log('❌ Max reconnect attempts reached');
          }
        };

        wsRef.current.onerror = (error) => {
          console.error('WebSocket error:', error);
          setConnectionStatus({ ws: 'Error', sse: 'Error' });
        };
      } catch (err) {
        console.error('WebSocket connection error:', err);
        setConnectionStatus({ ws: 'Error', sse: 'Error' });
      }
    };

    connectWebSocket();

    return () => {
      if (wsRef.current) {
        if (wsRef.current.pingInterval) {
          clearInterval(wsRef.current.pingInterval);
        }
        wsRef.current.close();
      }
    };
  }, [token, WS_URL, onMessage]);

  return { connectionStatus, wsRtt };
};

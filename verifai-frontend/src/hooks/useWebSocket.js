import { useEffect, useRef, useState } from 'react';
import { bindWebSocket, createWebSocket } from '../services/websocket';

export const useWebSocket = (path, { onOpen, onClose, onError } = {}) => {
  const socketRef = useRef(null);
  const [lastMessage, setLastMessage] = useState(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const socket = createWebSocket(path || '');
    socketRef.current = socket;

    bindWebSocket(socket, {
      onOpen: (event) => {
        setIsConnected(true);
        if (onOpen) onOpen(event);
      },
      onClose: (event) => {
        setIsConnected(false);
        if (onClose) onClose(event);
      },
      onError,
      onMessage: (event) => {
        setLastMessage(event.data);
      },
    });

    return () => {
      socket.close();
    };
  }, [path, onOpen, onClose, onError]);

  const sendMessage = (payload) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(payload);
    }
  };

  return { sendMessage, lastMessage, isConnected };
};

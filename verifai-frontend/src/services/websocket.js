const WS_BASE_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';

export const createWebSocket = (path = '') => {
  const url = `${WS_BASE_URL}${path}`;
  return new WebSocket(url);
};

export const bindWebSocket = (socket, handlers = {}) => {
  if (!socket) return null;

  const { onOpen, onClose, onMessage, onError } = handlers;

  if (onOpen) socket.addEventListener('open', onOpen);
  if (onClose) socket.addEventListener('close', onClose);
  if (onMessage) socket.addEventListener('message', onMessage);
  if (onError) socket.addEventListener('error', onError);

  return socket;
};

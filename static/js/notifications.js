// notifications.js

export function setupNotifications(onNotification) {
    if (!window.currentUsername) {
        // Not logged in, do not connect
        return;
    }
    const wsScheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const wsPath = `${wsScheme}://${window.location.host}/ws/notifications/`;
    const socket = new WebSocket(wsPath);

    socket.onopen = function() {
        console.log('WebSocket connected for notifications');
    };

    socket.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            if (data.type === 'notification' && typeof onNotification === 'function') {
                onNotification(data.notification);
            }
        } catch (e) {
            console.error('Error parsing notification message:', e);
        }
    };

    socket.onclose = function() {
        console.log('WebSocket for notifications closed');
    };

    socket.onerror = function(error) {
        console.error('WebSocket error:', error);
    };

    // Optionally return the socket for further use
    return socket;
} 
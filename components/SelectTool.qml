import QtQuick
import QtQuick.Controls

// Select tool component - handles panning and object selection
Item {
    id: tool
    
    // Properties
    property bool active: false
    
    // Internal state
    property bool isPanning: false
    property real lastX: 0
    property real lastY: 0
    
    // Sliding window smoothing (averages last N frames)
    property var deltaBufferX: []
    property var deltaBufferY: []
    property int bufferSize: 3  // Average last 3 frames for smooth motion
    
    // Signals
    signal panDelta(real dx, real dy)
    signal cursorShapeChanged(int shape)
    
    // Handle mouse press for panning (middle button only)
    function handlePress(screenX, screenY, button) {
        if (!tool.active) return false;
        
        if (button === Qt.MiddleButton) {
            isPanning = true;
            lastX = screenX;
            lastY = screenY;
            deltaBufferX = [];  // Clear buffer
            deltaBufferY = [];
            cursorShapeChanged(Qt.ClosedHandCursor);
            return true;  // Event handled
        }
        
        return false;
    }
    
    // Handle mouse release
    function handleRelease(screenX, screenY, button) {
        if (!tool.active) return false;
        
        if (isPanning) {
            isPanning = false;
            cursorShapeChanged(Qt.OpenHandCursor);
            return true;  // Event handled
        }
        
        return false;
    }
    
    // Handle mouse movement for panning
    function handleMouseMove(screenX, screenY) {
        if (!tool.active) return false;
        
        if (isPanning) {
            var dx = screenX - lastX;
            var dy = screenY - lastY;
            
            // Clamp individual deltas to prevent extreme jumps (e.g. from window focus changes)
            var maxDelta = 200;  // Maximum 200 pixels per frame
            if (Math.abs(dx) > maxDelta || Math.abs(dy) > maxDelta) {
                dx = Math.max(-maxDelta, Math.min(maxDelta, dx));
                dy = Math.max(-maxDelta, Math.min(maxDelta, dy));
            }
            
            // Add to sliding window buffer
            deltaBufferX.push(dx);
            deltaBufferY.push(dy);
            
            // Keep buffer at fixed size (remove oldest if over limit)
            if (deltaBufferX.length > bufferSize) {
                deltaBufferX.shift();
                deltaBufferY.shift();
            }
            
            // Calculate average of buffer (sliding window)
            var sumX = 0, sumY = 0;
            for (var i = 0; i < deltaBufferX.length; i++) {
                sumX += deltaBufferX[i];
                sumY += deltaBufferY[i];
            }
            var avgDx = sumX / deltaBufferX.length;
            var avgDy = sumY / deltaBufferY.length;
            
            // Emit smoothed delta (always emit, even if small)
            panDelta(avgDx, avgDy);
            
            lastX = screenX;
            lastY = screenY;
            return true;  // Event handled
        }
        
        return false;
    }
    
    // Reset tool state
    function reset() {
        isPanning = false;
    }
}


import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * Hook to detect continuous pressing/holding of an element.
 * @param {Function} onLongPress - Callback fired when duration is met
 * @param {Function} onClick - Callback fired for a normal click (duration not met)
 * @param {Object} options - { delay: number in ms, onStart: func, onCancel: func }
 */
export function useLongPress(onLongPress, onClick, { delay = 5000, onStart, onCancel } = {}) {
  const [isPressing, setIsPressing] = useState(false);
  const [timeLeft, setTimeLeft] = useState(Math.ceil(delay / 1000));
  const timerRef = useRef(null);
  const intervalRef = useRef(null);
  const isLongPressActive = useRef(false);

  // Clear timeout and interval unconditionally
  const clearIntervals = useCallback(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    if (intervalRef.current) clearInterval(intervalRef.current);
    timerRef.current = null;
    intervalRef.current = null;
  }, []);

  const startPress = useCallback((e) => {
    // Prevent default touch behavior (like selection or context menu) if possible
    if (e?.type === 'touchstart') e.preventDefault(); 
    
    clearIntervals();
    setIsPressing(true);
    isLongPressActive.current = false;
    setTimeLeft(Math.ceil(delay / 1000));
    
    if (onStart) onStart();

    // Start countdown
    intervalRef.current = setInterval(() => {
        setTimeLeft(prev => {
            if (prev <= 1) {
                clearInterval(intervalRef.current);
                return 0;
            }
            return prev - 1;
        });
    }, 1000);

    timerRef.current = setTimeout(() => {
      isLongPressActive.current = true;
      setIsPressing(false);
      onLongPress(e);
    }, delay);
  }, [onLongPress, delay, onStart, clearIntervals]);

  const cancelPress = useCallback((e) => {
    clearIntervals();
    setIsPressing(false);
    setTimeLeft(Math.ceil(delay / 1000)); // Reset
    
    if (!isLongPressActive.current) {
      // It was a short press / normal click
      if (onClick) onClick(e);
    }
    if (onCancel) onCancel();
    isLongPressActive.current = false;
  }, [clearIntervals, onClick, onCancel, delay]);

  useEffect(() => {
    return () => clearIntervals();
  }, [clearIntervals]);

  return {
    onMouseDown: startPress,
    onMouseUp: cancelPress,
    onMouseLeave: cancelPress,
    onTouchStart: startPress,
    onTouchEnd: cancelPress,
    isPressing,
    timeLeft
  };
}

/**
 * Utilizes the browser's Web Audio API to synthesize an oscillating siren sound natively.
 * Returns a function to stop the siren.
 */
export function playSiren() {
  try {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) return () => {}; 
    
    const ctx = new AudioContext();
    const oscillator = ctx.createOscillator();
    const gainNode = ctx.createGain();

    // High pitched wailing siren characteristic
    oscillator.type = 'square';
    oscillator.connect(gainNode);
    gainNode.connect(ctx.destination);

    const now = ctx.currentTime;
    
    // Oscillation sweep from 600Hz to 1200Hz over 1 second, repeatedly
    oscillator.frequency.setValueAtTime(600, now);
    
    // Loop the modulation for 10 minutes (600 seconds)
    for (let i = 0; i < 600; i++) {
        oscillator.frequency.linearRampToValueAtTime(1200, now + (i * 1.0) + 0.5);
        oscillator.frequency.linearRampToValueAtTime(600, now + (i * 1.0) + 1.0);
    }

    // Volume envelope
    gainNode.gain.setValueAtTime(0, now);
    gainNode.gain.linearRampToValueAtTime(0.5, now + 0.1); // Fade in

    oscillator.start(now);

    return () => {
      try {
        const stopTime = ctx.currentTime;
        gainNode.gain.cancelScheduledValues(stopTime);
        gainNode.gain.setValueAtTime(gainNode.gain.value, stopTime);
        gainNode.gain.linearRampToValueAtTime(0, stopTime + 0.1); // Fade out
        setTimeout(() => oscillator.stop(), 150);
      } catch (err) {
        oscillator.stop();
      }
    };

  } catch (err) {
    console.error("Failed to play siren via Web Audio API", err);
    return () => {};
  }
}

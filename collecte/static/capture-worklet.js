// Capture PCM sans boucle de retour vers le haut-parleur.
class CapturePCM extends AudioWorkletProcessor {
  process(inputs) {
    const canal = inputs[0]?.[0];
    if (canal) this.port.postMessage(canal.slice());
    return true;
  }
}
registerProcessor('capture-pcm', CapturePCM);

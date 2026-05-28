# Unity Interview Audio Pipeline

Esta carpeta contiene una integración preparada para Unity que mejora el audio antes de enviarlo a ElevenLabs Conversational AI.

## Objetivo

Reducir ruido, eco indirecto, ventiladores, teclado y falsos positivos de voz para que ElevenLabs detecte antes que el candidato ha terminado de hablar.

## Dependencias Unity

Instala estos paquetes:

1. `NativeWebSocket`
   - Git URL habitual: `https://github.com/endel/NativeWebSocket.git#upm`
   - Se usa para conectar con la `signed_url` de ElevenLabs.

2. `Newtonsoft Json`
   - Package Manager: `com.unity.nuget.newtonsoft-json`
   - Se usa para mensajes JSON flexibles.

3. Opcional: `Unity WebRTC`
   - Package Manager: `com.unity.webrtc`
   - Solo necesario si más adelante conectas el audio a un `RTCPeerConnection`.

## Backend

El backend ya expone:

```text
POST /interview/start
POST /interview/status
POST /interview/stop
POST /interview/transcript
```

Unity llama a `/interview/start`, recibe `signed_url` y `conversation_overrides`, y se conecta a ElevenLabs por WebSocket sin exponer `ELEVENLABS_API_KEY`.

## Componentes

- `InterviewAudioConfig`: configuración de DSP/VAD.
- `ProcessedMicrophoneCapture`: captura micrófono, limpia audio y emite PCM16 base64.
- `AudioFrameProcessor`: high-pass, noise gate, AGC, VAD, hangover y reducción de transitorios.
- `ElevenLabsConversationClient`: conecta con backend y ElevenLabs.
- `PcmAudioOutput`: reproduce audio recibido desde ElevenLabs.

## Configuración recomendada para entrevista

```text
microphoneSampleRate: 48000
targetSampleRate: 16000
frameMs: 20
highPassHz: 90
silenceAttenuation: 0.08
minSpeechDb: -42
vadMarginDb: 8
speechStartMs: 120
speechEndSilenceMs: 420
hangoverMs: 260
targetSpeechDb: -18
maxGain: 3.5
reduceKeyboardClicks: true
```

Si tarda demasiado en responder:

```text
speechEndSilenceMs: 300-380
hangoverMs: 180-240
vadMarginDb: 6-7
```

Si corta al usuario antes de tiempo:

```text
speechEndSilenceMs: 500-650
hangoverMs: 300-400
```

## Cómo montarlo en Unity

1. Crea un GameObject `InterviewAudio`.
2. Añade:
   - `ProcessedMicrophoneCapture`
   - `PcmAudioOutput`
   - `ElevenLabsConversationClient`
   - `AudioSource`
3. Crea un asset:
   - `Create -> TFG -> Interview Audio Config`
4. Asigna ese asset a `ProcessedMicrophoneCapture`.
5. En `ElevenLabsConversationClient` configura:

```text
backendBaseUrl = http://localhost:8000
jobType = Ingeniería
interviewerPersonality = Amable
```

6. Llama desde un botón UI:

```csharp
public async void StartInterview()
{
    await client.StartInterview();
}

public async void StopInterview()
{
    await client.StopInterview();
}
```

## Sobre echo cancellation

La cancelación de eco real necesita una referencia del audio que está sonando por altavoces. En navegador/WebRTC suele venir integrada. En Unity puro con WebSocket no hay AEC nativo universal, por eso este pipeline reduce eco indirecto con:

- volumen de salida controlado,
- noise gate,
- VAD con margen sobre noise floor,
- recomendación de colocar micrófono lejos de altavoces.

Para una demo sin auriculares:

- baja volumen de altavoces,
- usa micrófono direccional si puedes,
- activa `Auto Gain Control`,
- mantén `silenceAttenuation` entre `0.05` y `0.12`.

## Conexión con ElevenLabs

El cliente envía:

```json
{
  "type": "conversation_initiation_client_data",
  "conversation_config_override": {
    "agent": {
      "prompt": {"prompt": "..."},
      "first_message": "...",
      "language": "es"
    }
  }
}
```

Después envía audio limpio:

```json
{
  "user_audio_chunk": "base64_pcm16_16khz"
}
```

Y reproduce los eventos de audio recibidos desde ElevenLabs.

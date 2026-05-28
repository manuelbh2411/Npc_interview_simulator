using System;
using System.Text;
using NativeWebSocket;
using Newtonsoft.Json.Linq;
using UnityEngine;
using UnityEngine.Networking;

namespace TFG.InterviewAudio
{
    public sealed class ElevenLabsConversationClient : MonoBehaviour
    {
        [Header("Backend")]
        public string backendBaseUrl = "http://localhost:8000";
        public string jobType = "Ingeniería";
        public string interviewerPersonality = "Amable";
        public string candidateName;

        [Header("Audio")]
        public ProcessedMicrophoneCapture microphoneCapture;
        public PcmAudioOutput audioOutput;

        [Header("Runtime")]
        public bool autoStart;
        public ConversationState state = ConversationState.Disconnected;

        public event Action<string> AgentMessage;
        public event Action<string> UserTranscript;
        public event Action<ConversationState> StateChanged;

        private WebSocket _webSocket;
        private string _sessionId;

        private void Awake()
        {
            if (microphoneCapture == null)
            {
                microphoneCapture = GetComponent<ProcessedMicrophoneCapture>();
            }
            if (audioOutput == null)
            {
                audioOutput = GetComponent<PcmAudioOutput>();
            }
        }

        private async void Start()
        {
            if (autoStart)
            {
                await StartInterview();
            }
        }

        private void Update()
        {
#if !UNITY_WEBGL || UNITY_EDITOR
            _webSocket?.DispatchMessageQueue();
#endif
        }

        public async System.Threading.Tasks.Task StartInterview()
        {
            if (state == ConversationState.Connected || state == ConversationState.Connecting)
            {
                return;
            }

            SetState(ConversationState.Connecting);

            JObject startData = await StartBackendInterview();
            _sessionId = startData.Value<string>("session_id");
            JObject elevenlabs = (JObject)startData["elevenlabs_session_data"];
            string signedUrl = elevenlabs.Value<string>("signed_url");
            JObject overrides = (JObject)elevenlabs["conversation_overrides"];

            await ConnectElevenLabs(signedUrl, overrides);

            microphoneCapture.Pcm16Base64FrameReady += SendAudioFrame;
            microphoneCapture.SpeechStarted += () => _ = UpdateBackendStatus("connected", "speech_started");
            microphoneCapture.SpeechEnded += () => _ = UpdateBackendStatus("connected", "speech_ended");
            microphoneCapture.StartCapture();

            SetState(ConversationState.Connected);
            await UpdateBackendStatus("connected", null);
        }

        public async System.Threading.Tasks.Task StopInterview()
        {
            if (state != ConversationState.Connected)
            {
                Debug.LogWarning($"Stop ignored because conversation is {state}");
                return;
            }

            SetState(ConversationState.Stopping);
            microphoneCapture.Pcm16Base64FrameReady -= SendAudioFrame;
            microphoneCapture.StopCapture();

            await PostJson("/interview/stop", new JObject { ["session_id"] = _sessionId });
            if (_webSocket != null)
            {
                await _webSocket.Close();
                _webSocket = null;
            }
            SetState(ConversationState.Stopped);
        }

        private async System.Threading.Tasks.Task<JObject> StartBackendInterview()
        {
            JObject payload = new JObject
            {
                ["job_type"] = jobType,
                ["interviewer_personality"] = interviewerPersonality,
            };
            if (!string.IsNullOrWhiteSpace(candidateName))
            {
                payload["candidate_name"] = candidateName;
            }

            string json = await PostJson("/interview/start", payload);
            return JObject.Parse(json);
        }

        private async System.Threading.Tasks.Task ConnectElevenLabs(string signedUrl, JObject backendOverrides)
        {
            _webSocket = new WebSocket(signedUrl);

            _webSocket.OnOpen += async () =>
            {
                Debug.Log("ElevenLabs WebSocket connected");
                await SendConversationInit(backendOverrides);
            };
            _webSocket.OnError += error =>
            {
                Debug.LogError($"ElevenLabs WebSocket error: {error}");
                SetState(ConversationState.Error);
                _ = UpdateBackendStatus("error", error);
            };
            _webSocket.OnClose += code =>
            {
                Debug.Log($"ElevenLabs WebSocket closed: {code}");
                if (state != ConversationState.Stopping && state != ConversationState.Stopped)
                {
                    SetState(ConversationState.Disconnected);
                    _ = UpdateBackendStatus("disconnected", $"websocket_closed_{code}");
                }
            };
            _webSocket.OnMessage += HandleElevenLabsMessage;

            await _webSocket.Connect();
        }

        private async System.Threading.Tasks.Task SendConversationInit(JObject backendOverrides)
        {
            JObject agent = (JObject)backendOverrides["agent"];
            JObject prompt = (JObject)agent["prompt"];

            JObject init = new JObject
            {
                ["type"] = "conversation_initiation_client_data",
                ["conversation_config_override"] = new JObject
                {
                    ["agent"] = new JObject
                    {
                        ["prompt"] = new JObject
                        {
                            ["prompt"] = prompt.Value<string>("prompt")
                        },
                        ["first_message"] = agent.Value<string>("firstMessage"),
                        ["language"] = agent.Value<string>("language") ?? "es"
                    }
                }
            };

            await _webSocket.SendText(init.ToString());
        }

        private async void SendAudioFrame(string base64Pcm16)
        {
            if (_webSocket == null || _webSocket.State != WebSocketState.Open || state != ConversationState.Connected)
            {
                return;
            }

            JObject audio = new JObject
            {
                ["user_audio_chunk"] = base64Pcm16
            };
            await _webSocket.SendText(audio.ToString());
        }

        private void HandleElevenLabsMessage(byte[] bytes)
        {
            string json = Encoding.UTF8.GetString(bytes);
            JObject message;
            try
            {
                message = JObject.Parse(json);
            }
            catch
            {
                Debug.LogWarning($"Non JSON ElevenLabs message: {json}");
                return;
            }

            string type = message.Value<string>("type");
            if (type == "audio")
            {
                string audio = message["audio_event"]?.Value<string>("audio_base_64")
                    ?? message.Value<string>("audio");
                if (!string.IsNullOrWhiteSpace(audio))
                {
                    audioOutput.EnqueuePcm16Base64(audio);
                }
            }
            else if (type == "agent_response")
            {
                string text = message["agent_response_event"]?.Value<string>("agent_response")
                    ?? message.Value<string>("agent_response");
                if (!string.IsNullOrWhiteSpace(text))
                {
                    AgentMessage?.Invoke(text);
                    _ = StoreTranscript("interviewer", text);
                }
            }
            else if (type == "user_transcript")
            {
                string text = message["user_transcription_event"]?.Value<string>("user_transcript")
                    ?? message.Value<string>("user_transcript");
                if (!string.IsNullOrWhiteSpace(text))
                {
                    UserTranscript?.Invoke(text);
                    _ = StoreTranscript("candidate", text);
                }
            }
            else if (type == "interruption")
            {
                audioOutput.Clear();
            }
            else if (type == "ping")
            {
                _ = SendPong(message);
            }
        }

        private async System.Threading.Tasks.Task SendPong(JObject ping)
        {
            JObject pong = new JObject { ["type"] = "pong" };
            JToken eventId = ping["ping_event"]?["event_id"];
            if (eventId != null)
            {
                pong["event_id"] = eventId;
            }
            await _webSocket.SendText(pong.ToString());
        }

        private async System.Threading.Tasks.Task StoreTranscript(string speaker, string text)
        {
            if (string.IsNullOrWhiteSpace(_sessionId))
            {
                return;
            }

            await PostJson("/interview/transcript", new JObject
            {
                ["session_id"] = _sessionId,
                ["speaker"] = speaker,
                ["message"] = text,
                ["timestamp"] = DateTime.UtcNow.ToString("O")
            });
        }

        private async System.Threading.Tasks.Task UpdateBackendStatus(string status, string detail)
        {
            if (string.IsNullOrWhiteSpace(_sessionId))
            {
                return;
            }

            JObject payload = new JObject
            {
                ["session_id"] = _sessionId,
                ["status"] = status
            };
            if (!string.IsNullOrWhiteSpace(detail))
            {
                payload["detail"] = detail;
            }
            await PostJson("/interview/status", payload);
        }

        private async System.Threading.Tasks.Task<string> PostJson(string path, JObject payload)
        {
            string url = $"{backendBaseUrl.TrimEnd('/')}{path}";
            using UnityWebRequest request = new UnityWebRequest(url, "POST");
            byte[] body = Encoding.UTF8.GetBytes(payload.ToString());
            request.uploadHandler = new UploadHandlerRaw(body);
            request.downloadHandler = new DownloadHandlerBuffer();
            request.SetRequestHeader("Content-Type", "application/json");
            await request.SendWebRequest();

            if (request.result != UnityWebRequest.Result.Success)
            {
                throw new InvalidOperationException($"{request.responseCode} {request.error}: {request.downloadHandler.text}");
            }
            return request.downloadHandler.text;
        }

        private void SetState(ConversationState next)
        {
            state = next;
            StateChanged?.Invoke(next);
        }

        private async void OnDestroy()
        {
            if (_webSocket != null)
            {
                await _webSocket.Close();
            }
        }
    }

    public enum ConversationState
    {
        Disconnected,
        Connecting,
        Connected,
        Stopping,
        Stopped,
        Error
    }
}

#if UNITY_WEBRTC
using Unity.WebRTC;
using UnityEngine;

namespace TFG.InterviewAudio.Optional
{
    public sealed class UnityWebRTCAudioTrackBridge : MonoBehaviour
    {
        public AudioSource processedAudioSource;
        public AudioStreamTrack Track { get; private set; }

        private void Start()
        {
            if (processedAudioSource == null)
            {
                processedAudioSource = GetComponent<AudioSource>();
            }

            Track = new AudioStreamTrack(processedAudioSource);
        }

        private void OnDestroy()
        {
            Track?.Dispose();
        }
    }
}
#endif

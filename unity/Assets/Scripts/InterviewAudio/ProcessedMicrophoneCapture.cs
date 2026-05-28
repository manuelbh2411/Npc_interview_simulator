using System;
using UnityEngine;

namespace TFG.InterviewAudio
{
    public sealed class ProcessedMicrophoneCapture : MonoBehaviour
    {
        public InterviewAudioConfig config;
        public string microphoneDevice;

        public event Action<string> Pcm16Base64FrameReady;
        public event Action SpeechStarted;
        public event Action SpeechEnded;

        public bool IsCapturing { get; private set; }
        public bool IsSpeaking => _processor?.IsSpeaking ?? false;
        public float LastInputDb => _processor?.LastRmsDb ?? -90f;
        public float NoiseFloorDb => _processor?.NoiseFloorDb ?? -90f;

        private AudioClip _microphoneClip;
        private AudioFrameProcessor _processor;
        private int _lastMicPosition;
        private int _frameSize;
        private float[] _pending;
        private int _pendingCount;

        private void Awake()
        {
            if (config == null)
            {
                config = ScriptableObject.CreateInstance<InterviewAudioConfig>();
            }
        }

        public void StartCapture()
        {
            if (IsCapturing)
            {
                return;
            }

            _frameSize = Mathf.RoundToInt(config.microphoneSampleRate * config.frameMs / 1000f);
            _pending = new float[_frameSize * 2];
            _pendingCount = 0;
            _processor = new AudioFrameProcessor(config, config.microphoneSampleRate);
            _processor.SpeechStarted += () => SpeechStarted?.Invoke();
            _processor.SpeechEnded += () => SpeechEnded?.Invoke();

            _microphoneClip = Microphone.Start(
                string.IsNullOrWhiteSpace(microphoneDevice) ? null : microphoneDevice,
                true,
                1,
                config.microphoneSampleRate
            );
            _lastMicPosition = 0;
            IsCapturing = true;
        }

        public void StopCapture()
        {
            if (!IsCapturing)
            {
                return;
            }

            Microphone.End(string.IsNullOrWhiteSpace(microphoneDevice) ? null : microphoneDevice);
            IsCapturing = false;
            _microphoneClip = null;
            _pendingCount = 0;
        }

        private void Update()
        {
            if (!IsCapturing || _microphoneClip == null)
            {
                return;
            }

            int position = Microphone.GetPosition(string.IsNullOrWhiteSpace(microphoneDevice) ? null : microphoneDevice);
            if (position < 0 || position == _lastMicPosition)
            {
                return;
            }

            int sampleCount = position > _lastMicPosition
                ? position - _lastMicPosition
                : _microphoneClip.samples - _lastMicPosition + position;

            float[] buffer = new float[sampleCount];
            if (position > _lastMicPosition)
            {
                _microphoneClip.GetData(buffer, _lastMicPosition);
            }
            else
            {
                float[] tail = new float[_microphoneClip.samples - _lastMicPosition];
                float[] head = new float[position];
                _microphoneClip.GetData(tail, _lastMicPosition);
                _microphoneClip.GetData(head, 0);
                Array.Copy(tail, 0, buffer, 0, tail.Length);
                Array.Copy(head, 0, buffer, tail.Length, head.Length);
            }

            _lastMicPosition = position;
            PushSamples(buffer);
        }

        private void PushSamples(float[] samples)
        {
            int offset = 0;
            while (offset < samples.Length)
            {
                int copy = Mathf.Min(_pending.Length - _pendingCount, samples.Length - offset);
                Array.Copy(samples, offset, _pending, _pendingCount, copy);
                _pendingCount += copy;
                offset += copy;

                while (_pendingCount >= _frameSize)
                {
                    float[] frame = new float[_frameSize];
                    Array.Copy(_pending, 0, frame, 0, _frameSize);

                    int remaining = _pendingCount - _frameSize;
                    if (remaining > 0)
                    {
                        Array.Copy(_pending, _frameSize, _pending, 0, remaining);
                    }
                    _pendingCount = remaining;

                    _processor.ProcessFrame(frame);
                    float[] resampled = Pcm16Utility.ResampleLinear(frame, config.microphoneSampleRate, config.targetSampleRate);
                    Pcm16Base64FrameReady?.Invoke(Pcm16Utility.FloatToPcm16Base64(resampled));
                }
            }
        }
    }
}

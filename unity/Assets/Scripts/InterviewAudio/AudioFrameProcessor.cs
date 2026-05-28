using System;
using UnityEngine;

namespace TFG.InterviewAudio
{
    public sealed class AudioFrameProcessor
    {
        public event Action SpeechStarted;
        public event Action SpeechEnded;

        public bool IsSpeaking { get; private set; }
        public float NoiseFloorDb => LinearToDb(_noiseFloorRms);
        public float LastRmsDb { get; private set; } = -90f;

        private readonly InterviewAudioConfig _config;
        private readonly int _sampleRate;
        private readonly int _speechStartFrames;
        private readonly int _speechEndFrames;
        private readonly int _hangoverFrames;

        private float _noiseFloorRms = 0.003f;
        private float _previousInput;
        private float _previousHighPass;
        private float _currentGain = 1f;
        private int _speechFrames;
        private int _silenceFrames;
        private int _hangoverRemaining;

        public AudioFrameProcessor(InterviewAudioConfig config, int sampleRate)
        {
            _config = config;
            _sampleRate = sampleRate;
            int frameMs = Mathf.Max(1, config.frameMs);
            _speechStartFrames = Mathf.Max(1, Mathf.CeilToInt(config.speechStartMs / (float)frameMs));
            _speechEndFrames = Mathf.Max(1, Mathf.CeilToInt(config.speechEndSilenceMs / (float)frameMs));
            _hangoverFrames = Mathf.Max(1, Mathf.CeilToInt(config.hangoverMs / (float)frameMs));
        }

        public bool ProcessFrame(float[] frame)
        {
            ApplyHighPass(frame);

            float rms = CalculateRms(frame);
            float peak = CalculatePeak(frame);
            LastRmsDb = LinearToDb(rms);

            bool transientNoise = _config.reduceKeyboardClicks && IsLikelyKeyboardTransient(rms, peak);
            bool aboveAbsoluteThreshold = LastRmsDb >= _config.minSpeechDb;
            bool aboveNoiseFloor = LastRmsDb >= NoiseFloorDb + _config.vadMarginDb;
            bool voiceNow = !transientNoise && aboveAbsoluteThreshold && aboveNoiseFloor;

            UpdateVadState(voiceNow);

            if (!voiceNow && !IsSpeaking)
            {
                TrackNoiseFloor(rms);
            }

            if (_config.autoGainControl && (voiceNow || IsSpeaking))
            {
                ApplyAgc(frame, rms);
            }

            if (transientNoise)
            {
                Multiply(frame, _config.transientAttenuation);
            }
            else if (!IsSpeaking && _hangoverRemaining <= 0)
            {
                Multiply(frame, _config.silenceAttenuation);
            }

            SoftLimit(frame);
            return IsSpeaking;
        }

        private void ApplyHighPass(float[] frame)
        {
            float rc = 1f / (2f * Mathf.PI * _config.highPassHz);
            float dt = 1f / _sampleRate;
            float alpha = rc / (rc + dt);

            for (int i = 0; i < frame.Length; i++)
            {
                float input = frame[i];
                float output = alpha * (_previousHighPass + input - _previousInput);
                _previousInput = input;
                _previousHighPass = output;
                frame[i] = output;
            }
        }

        private void UpdateVadState(bool voiceNow)
        {
            if (voiceNow)
            {
                _speechFrames++;
                _silenceFrames = 0;
                _hangoverRemaining = _hangoverFrames;
                if (!IsSpeaking && _speechFrames >= _speechStartFrames)
                {
                    IsSpeaking = true;
                    SpeechStarted?.Invoke();
                }
                return;
            }

            _speechFrames = 0;
            _silenceFrames++;
            if (_hangoverRemaining > 0)
            {
                _hangoverRemaining--;
            }

            if (IsSpeaking && _silenceFrames >= _speechEndFrames)
            {
                IsSpeaking = false;
                SpeechEnded?.Invoke();
            }
        }

        private void TrackNoiseFloor(float rms)
        {
            float clamped = Mathf.Clamp(rms, 0.0001f, 0.08f);
            _noiseFloorRms = Mathf.Lerp(clamped, _noiseFloorRms, _config.noiseFloorSmoothing);
        }

        private void ApplyAgc(float[] frame, float rms)
        {
            float target = DbToLinear(_config.targetSpeechDb);
            float desiredGain = Mathf.Clamp(target / Mathf.Max(rms, 0.0001f), 1f, _config.maxGain);
            _currentGain = Mathf.Lerp(desiredGain, _currentGain, _config.gainSmoothing);
            Multiply(frame, _currentGain);
        }

        private static bool IsLikelyKeyboardTransient(float rms, float peak)
        {
            float crest = peak / Mathf.Max(rms, 0.0001f);
            return peak > 0.28f && rms < 0.045f && crest > 10f;
        }

        private static float CalculateRms(float[] frame)
        {
            double sum = 0;
            for (int i = 0; i < frame.Length; i++)
            {
                sum += frame[i] * frame[i];
            }
            return Mathf.Sqrt((float)(sum / Math.Max(1, frame.Length)));
        }

        private static float CalculatePeak(float[] frame)
        {
            float peak = 0f;
            for (int i = 0; i < frame.Length; i++)
            {
                peak = Mathf.Max(peak, Mathf.Abs(frame[i]));
            }
            return peak;
        }

        private static void Multiply(float[] frame, float gain)
        {
            for (int i = 0; i < frame.Length; i++)
            {
                frame[i] *= gain;
            }
        }

        private static void SoftLimit(float[] frame)
        {
            for (int i = 0; i < frame.Length; i++)
            {
                frame[i] = Mathf.Tanh(frame[i] * 1.15f) / 1.15f;
            }
        }

        private static float LinearToDb(float value)
        {
            return 20f * Mathf.Log10(Mathf.Max(value, 0.000001f));
        }

        private static float DbToLinear(float db)
        {
            return Mathf.Pow(10f, db / 20f);
        }
    }
}

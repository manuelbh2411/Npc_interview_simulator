using System;
using System.Collections.Concurrent;
using UnityEngine;

namespace TFG.InterviewAudio
{
    [RequireComponent(typeof(AudioSource))]
    public sealed class PcmAudioOutput : MonoBehaviour
    {
        public int inputSampleRate = 16000;

        private readonly ConcurrentQueue<float> _queue = new ConcurrentQueue<float>();
        private int _outputSampleRate;

        private void Awake()
        {
            _outputSampleRate = AudioSettings.outputSampleRate;
            GetComponent<AudioSource>().playOnAwake = true;
            GetComponent<AudioSource>().loop = true;
            GetComponent<AudioSource>().clip = AudioClip.Create("ElevenLabsOutputSilence", _outputSampleRate, 1, _outputSampleRate, false);
            GetComponent<AudioSource>().Play();
        }

        public void EnqueuePcm16Base64(string base64Audio)
        {
            byte[] bytes = Convert.FromBase64String(base64Audio);
            float[] samples = Pcm16Utility.Pcm16ToFloat(bytes);
            float[] outputRateSamples = Pcm16Utility.ResampleLinear(samples, inputSampleRate, _outputSampleRate);
            for (int i = 0; i < outputRateSamples.Length; i++)
            {
                _queue.Enqueue(outputRateSamples[i]);
            }
        }

        public void Clear()
        {
            while (_queue.TryDequeue(out _)) { }
        }

        private void OnAudioFilterRead(float[] data, int channels)
        {
            for (int i = 0; i < data.Length; i += channels)
            {
                float sample = _queue.TryDequeue(out float value) ? value : 0f;
                for (int channel = 0; channel < channels; channel++)
                {
                    data[i + channel] = sample;
                }
            }
        }
    }
}

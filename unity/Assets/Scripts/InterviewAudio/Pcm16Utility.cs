using System;
using UnityEngine;

namespace TFG.InterviewAudio
{
    public static class Pcm16Utility
    {
        public static byte[] FloatToPcm16(float[] samples)
        {
            byte[] bytes = new byte[samples.Length * 2];
            for (int i = 0; i < samples.Length; i++)
            {
                short value = (short)Mathf.Clamp(Mathf.RoundToInt(samples[i] * short.MaxValue), short.MinValue, short.MaxValue);
                bytes[i * 2] = (byte)(value & 0xff);
                bytes[i * 2 + 1] = (byte)((value >> 8) & 0xff);
            }
            return bytes;
        }

        public static float[] Pcm16ToFloat(byte[] bytes)
        {
            int sampleCount = bytes.Length / 2;
            float[] samples = new float[sampleCount];
            for (int i = 0; i < sampleCount; i++)
            {
                short value = BitConverter.ToInt16(bytes, i * 2);
                samples[i] = value / 32768f;
            }
            return samples;
        }

        public static string FloatToPcm16Base64(float[] samples)
        {
            return Convert.ToBase64String(FloatToPcm16(samples));
        }

        public static float[] ResampleLinear(float[] input, int inputRate, int outputRate)
        {
            if (inputRate == outputRate)
            {
                return (float[])input.Clone();
            }

            int outputLength = Mathf.Max(1, Mathf.RoundToInt(input.Length * (outputRate / (float)inputRate)));
            float[] output = new float[outputLength];
            float ratio = (input.Length - 1f) / Mathf.Max(1, outputLength - 1f);

            for (int i = 0; i < outputLength; i++)
            {
                float sourceIndex = i * ratio;
                int index = Mathf.FloorToInt(sourceIndex);
                int next = Mathf.Min(index + 1, input.Length - 1);
                float t = sourceIndex - index;
                output[i] = Mathf.Lerp(input[index], input[next], t);
            }

            return output;
        }
    }
}

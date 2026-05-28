using UnityEngine;

namespace TFG.InterviewAudio
{
    [CreateAssetMenu(menuName = "TFG/Interview Audio Config")]
    public sealed class InterviewAudioConfig : ScriptableObject
    {
        [Header("Capture")]
        public int microphoneSampleRate = 48000;
        public int targetSampleRate = 16000;
        public int frameMs = 20;

        [Header("Noise reduction")]
        [Range(40f, 180f)] public float highPassHz = 90f;
        [Range(0f, 1f)] public float silenceAttenuation = 0.08f;
        [Range(0f, 1f)] public float noiseFloorSmoothing = 0.96f;

        [Header("Voice activity detection")]
        [Range(-70f, -20f)] public float minSpeechDb = -42f;
        [Range(3f, 18f)] public float vadMarginDb = 8f;
        [Range(80, 800)] public int speechStartMs = 120;
        [Range(150, 1200)] public int speechEndSilenceMs = 420;
        [Range(100, 1000)] public int hangoverMs = 260;

        [Header("Gain")]
        public bool autoGainControl = true;
        [Range(-28f, -10f)] public float targetSpeechDb = -18f;
        [Range(1f, 8f)] public float maxGain = 3.5f;
        [Range(0.80f, 0.995f)] public float gainSmoothing = 0.94f;

        [Header("Transient reduction")]
        public bool reduceKeyboardClicks = true;
        [Range(0.1f, 0.95f)] public float transientAttenuation = 0.35f;
    }
}

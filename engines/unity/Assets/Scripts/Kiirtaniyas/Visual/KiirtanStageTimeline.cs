using System;
using System.Collections.Generic;
using UnityEngine;

namespace Kiirtaniyas.Visual
{
    [Serializable]
    public struct KiirtanStageMarker
    {
        public KiirtanStage stage;

        [Range(0f, 1f)]
        public float normalizedStart;

        public KiirtanStageMarker(KiirtanStage stage, float normalizedStart)
        {
            this.stage = stage;
            this.normalizedStart = normalizedStart;
        }
    }

    /// <summary>
    /// Maps the song clock to authored visual stages.
    /// Markers are normalized so a trimmed excerpt or a longer song can use the same timeline.
    /// </summary>
    [Serializable]
    public sealed class KiirtanStageTimeline
    {
        [Min(0.1f)]
        [SerializeField]
        private float durationSeconds = 210f;

        [SerializeField]
        private List<KiirtanStageMarker> markers = CreateDefaultMarkers();

        public float DurationSeconds
        {
            get { return durationSeconds; }
            set { durationSeconds = Mathf.Max(0.1f, value); }
        }

        public IReadOnlyList<KiirtanStageMarker> Markers
        {
            get { return markers; }
        }

        public void EnsureDefaults()
        {
            if (markers == null || markers.Count == 0)
            {
                markers = CreateDefaultMarkers();
            }

            durationSeconds = Mathf.Max(0.1f, durationSeconds);
        }

        public KiirtanStage Evaluate(float songSeconds)
        {
            EnsureDefaults();
            float normalizedTime = Normalize(songSeconds);
            KiirtanStage result = KiirtanStage.Intimate;

            for (int i = 0; i < markers.Count; i++)
            {
                KiirtanStageMarker marker = markers[i];
                if (marker.normalizedStart <= normalizedTime)
                {
                    result = marker.stage;
                }
            }

            return result;
        }

        public float GetStageProgress(float songSeconds)
        {
            EnsureDefaults();
            float normalizedTime = Normalize(songSeconds);
            int currentIndex = FindCurrentMarkerIndex(normalizedTime);
            if (currentIndex < 0)
            {
                return 0f;
            }

            float currentStart = Mathf.Clamp01(markers[currentIndex].normalizedStart);
            float nextStart = 1f;
            for (int i = currentIndex + 1; i < markers.Count; i++)
            {
                float candidate = Mathf.Clamp01(markers[i].normalizedStart);
                if (candidate > currentStart)
                {
                    nextStart = candidate;
                    break;
                }
            }

            if (nextStart <= currentStart)
            {
                return 1f;
            }

            return Mathf.InverseLerp(currentStart, nextStart, normalizedTime);
        }

        public float GetStageStartSeconds(KiirtanStage stage)
        {
            EnsureDefaults();
            for (int i = 0; i < markers.Count; i++)
            {
                if (markers[i].stage == stage)
                {
                    return Mathf.Clamp01(markers[i].normalizedStart) * durationSeconds;
                }
            }

            return -1f;
        }

        private int FindCurrentMarkerIndex(float normalizedTime)
        {
            int currentIndex = -1;
            float currentStart = -1f;

            for (int i = 0; i < markers.Count; i++)
            {
                float markerStart = Mathf.Clamp01(markers[i].normalizedStart);
                if (markerStart <= normalizedTime && markerStart >= currentStart)
                {
                    currentIndex = i;
                    currentStart = markerStart;
                }
            }

            return currentIndex;
        }

        private float Normalize(float songSeconds)
        {
            return Mathf.Clamp01(songSeconds / Mathf.Max(0.1f, durationSeconds));
        }

        private static List<KiirtanStageMarker> CreateDefaultMarkers()
        {
            return new List<KiirtanStageMarker>
            {
                new KiirtanStageMarker(KiirtanStage.Intimate, 0f),
                new KiirtanStageMarker(KiirtanStage.Heavenly, 0.25f),
                new KiirtanStageMarker(KiirtanStage.CosmicSpace, 0.5f),
                new KiirtanStageMarker(KiirtanStage.CosmicFractal, 0.75f),
                new KiirtanStageMarker(KiirtanStage.SoloCosmic, 0.95f),
            };
        }
    }
}

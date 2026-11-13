using System;
using UnityEngine;

namespace Kiirtaniyas.Visual
{
    /// <summary>
    /// Drives the authored real-time world from the song clock.
    /// Attach this to a scene root and assign stage layers in the Inspector.
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class KiirtanWorldDirector : MonoBehaviour
    {
        [SerializeField]
        private AudioSource songAudioSource;

        [Tooltip("Use the AudioSource clock. Disable this for timeline preview or external chart control.")]
        [SerializeField]
        private bool driveFromAudioSource = true;

        [Tooltip("Start the assigned song automatically when this world enters Play Mode.")]
        [SerializeField]
        private bool playAudioOnEnable;

        [Tooltip("When automatic playback starts, rewind the assigned song to the beginning first.")]
        [SerializeField]
        private bool restartAudioOnEnable = true;

        [Tooltip("Subtract this from AudioSource.time when the source contains the full recording.")]
        [Min(0f)]
        [SerializeField]
        private float songStartOffsetSeconds;

        [SerializeField]
        private KiirtanStageTimeline timeline = new KiirtanStageTimeline();

        [SerializeField]
        private KiirtanCrowdDirector crowdDirector;

        [SerializeField]
        private KiirtanStageLayer[] stageLayers = Array.Empty<KiirtanStageLayer>();

        [Min(0f)]
        [SerializeField]
        private float transitionSeconds = 2f;

        [SerializeField]
        private bool controlRenderSettings = true;

        [SerializeField]
        private bool advanceManualClock;

        private KiirtanStage currentStage = KiirtanStage.Intimate;
        private float manualSongSeconds;
        private float transitionElapsed;
        private Color fromAmbient;
        private Color targetAmbient;
        private Color fromFogColor;
        private Color targetFogColor;
        private float fromFogDensity;
        private float targetFogDensity;
        private bool fromFogEnabled;
        private bool targetFogEnabled;
        private bool initialized;

        private Color defaultAmbient;
        private Color defaultFogColor;
        private float defaultFogDensity;
        private bool defaultFogEnabled;

        public event Action<KiirtanStage> StageChanged;

        public KiirtanStage CurrentStage
        {
            get { return currentStage; }
        }

        public float SongSeconds
        {
            get { return ResolveSongSeconds(); }
        }

        public float StageProgress
        {
            get { return timeline == null ? 0f : timeline.GetStageProgress(SongSeconds); }
        }

        public KiirtanStageTimeline Timeline
        {
            get { return timeline; }
        }

        public void SetSongSeconds(float seconds)
        {
            driveFromAudioSource = false;
            manualSongSeconds = Mathf.Clamp(seconds, 0f, GetTimelineDuration());
            EvaluateAt(manualSongSeconds, true);
        }

        public void SetAudioSource(AudioSource source)
        {
            songAudioSource = source;
            driveFromAudioSource = source != null;
        }

        public void PlaySong(bool restart = false)
        {
            if (songAudioSource == null || songAudioSource.clip == null)
            {
                return;
            }

            driveFromAudioSource = true;
            if (restart)
            {
                songAudioSource.time = 0f;
            }

            if (!songAudioSource.isPlaying)
            {
                songAudioSource.Play();
            }
        }

        public void StopSong()
        {
            if (songAudioSource != null)
            {
                songAudioSource.Stop();
            }
        }

        public void SetStage(KiirtanStage stage)
        {
            ApplyStage(stage, false);
        }

        public void ResetWorld()
        {
            manualSongSeconds = 0f;
            EvaluateAt(0f, true);
        }

        private void Awake()
        {
            if (timeline == null)
            {
                timeline = new KiirtanStageTimeline();
            }

            timeline.EnsureDefaults();
            defaultAmbient = RenderSettings.ambientLight;
            defaultFogColor = RenderSettings.fogColor;
            defaultFogDensity = RenderSettings.fogDensity;
            defaultFogEnabled = RenderSettings.fog;
            initialized = true;
            ApplyStage(timeline.Evaluate(0f), true);
        }

        private void OnEnable()
        {
            if (initialized)
            {
                ApplyStage(currentStage, true);
            }

            if (Application.isPlaying && playAudioOnEnable)
            {
                PlaySong(restartAudioOnEnable);
            }
        }

        private void OnDisable()
        {
            RestoreRenderSettings();
        }

        private void Update()
        {
            if (!Application.isPlaying)
            {
                return;
            }

            if (!driveFromAudioSource && advanceManualClock)
            {
                manualSongSeconds = Mathf.Min(GetTimelineDuration(), manualSongSeconds + Time.deltaTime);
            }

            EvaluateAt(ResolveSongSeconds(), false);
            UpdateRenderTransition();
        }

        private void EvaluateAt(float seconds, bool immediate)
        {
            if (timeline == null)
            {
                return;
            }

            KiirtanStage nextStage = timeline.Evaluate(seconds);
            if (nextStage != currentStage || immediate)
            {
                ApplyStage(nextStage, immediate);
            }
        }

        private void ApplyStage(KiirtanStage stage, bool immediate)
        {
            KiirtanStage previousStage = currentStage;
            currentStage = stage;

            KiirtanStageLayer layer = FindLayer(stage);
            fromAmbient = RenderSettings.ambientLight;
            fromFogColor = RenderSettings.fogColor;
            fromFogDensity = RenderSettings.fogDensity;
            fromFogEnabled = RenderSettings.fog;
            targetAmbient = layer == null ? defaultAmbient : layer.ambientLight;
            targetFogColor = layer == null ? defaultFogColor : layer.fogColor;
            targetFogDensity = layer == null ? defaultFogDensity : Mathf.Clamp01(layer.fogDensity);
            targetFogEnabled = layer != null && targetFogDensity > 0.0001f;
            transitionElapsed = immediate ? transitionSeconds : 0f;

            ActivateLayer(stage);
            if (crowdDirector != null)
            {
                crowdDirector.SetStage(stage);
            }

            if (immediate)
            {
                UpdateRenderTransition();
            }

            if (previousStage != stage)
            {
                StageChanged?.Invoke(stage);
            }
        }

        private void UpdateRenderTransition()
        {
            if (!controlRenderSettings)
            {
                return;
            }

            transitionElapsed += Time.deltaTime;
            float progress = transitionSeconds <= 0f
                ? 1f
                : Mathf.Clamp01(transitionElapsed / transitionSeconds);
            RenderSettings.ambientLight = Color.Lerp(fromAmbient, targetAmbient, progress);
            RenderSettings.fogColor = Color.Lerp(fromFogColor, targetFogColor, progress);
            RenderSettings.fogDensity = Mathf.Lerp(fromFogDensity, targetFogDensity, progress);
            RenderSettings.fog = progress < 1f ? fromFogEnabled || targetFogEnabled : targetFogEnabled;
        }

        private void ActivateLayer(KiirtanStage stage)
        {
            if (stageLayers == null)
            {
                return;
            }

            for (int i = 0; i < stageLayers.Length; i++)
            {
                KiirtanStageLayer layer = stageLayers[i];
                if (layer == null)
                {
                    continue;
                }

                bool active = layer.stage == stage;
                if (layer.root != null && layer.root != gameObject)
                {
                    layer.root.SetActive(active);
                }

                if (layer.lights != null)
                {
                    for (int j = 0; j < layer.lights.Length; j++)
                    {
                        if (layer.lights[j] != null)
                        {
                            layer.lights[j].enabled = active;
                        }
                    }
                }

                if (layer.particles == null)
                {
                    continue;
                }

                for (int j = 0; j < layer.particles.Length; j++)
                {
                    ParticleSystem particles = layer.particles[j];
                    if (particles == null)
                    {
                        continue;
                    }

                    if (active)
                    {
                        if (!particles.isPlaying)
                        {
                            particles.Play();
                        }
                    }
                    else
                    {
                        particles.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
                    }
                }
            }
        }

        private KiirtanStageLayer FindLayer(KiirtanStage stage)
        {
            if (stageLayers == null)
            {
                return null;
            }

            for (int i = 0; i < stageLayers.Length; i++)
            {
                if (stageLayers[i] != null && stageLayers[i].stage == stage)
                {
                    return stageLayers[i];
                }
            }

            return null;
        }

        private float ResolveSongSeconds()
        {
            if (driveFromAudioSource && songAudioSource != null && songAudioSource.clip != null)
            {
                float sourceSeconds = songAudioSource.time - songStartOffsetSeconds;
                return Mathf.Clamp(sourceSeconds, 0f, GetTimelineDuration());
            }

            return Mathf.Clamp(manualSongSeconds, 0f, GetTimelineDuration());
        }

        private float GetTimelineDuration()
        {
            return timeline == null ? 210f : Mathf.Max(0.1f, timeline.DurationSeconds);
        }

        private void RestoreRenderSettings()
        {
            if (!controlRenderSettings)
            {
                return;
            }

            RenderSettings.ambientLight = defaultAmbient;
            RenderSettings.fogColor = defaultFogColor;
            RenderSettings.fogDensity = defaultFogDensity;
            RenderSettings.fog = defaultFogEnabled;
        }
    }
}

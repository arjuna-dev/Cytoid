using UnityEngine;

namespace Kiirtaniyas.Visual
{
    /// <summary>Plays the Blender-authored two-beat dance beneath the orbit root.</summary>
    [DisallowMultipleComponent]
    public sealed class KiirtanDancePlayer : MonoBehaviour
    {
        [SerializeField, Min(0.1f)] private float playbackSpeed = 1f;
        [SerializeField, Range(0f, 1f)] private float phaseOffset;

        public void SetPhase(float phase)
        {
            phaseOffset = Mathf.Repeat(phase, 1f);
            if (isActiveAndEnabled)
            {
                ApplyPlaybackPhase();
            }
        }

        private void OnEnable()
        {
            ApplyPlaybackPhase();
        }

        private void ApplyPlaybackPhase()
        {
            var dance = GetComponentInChildren<Animation>(true);
            if (dance == null || dance.clip == null) return;
            dance.wrapMode = WrapMode.Loop;
            dance.playAutomatically = true;
            AnimationState state = dance[dance.clip.name];
            if (state == null) return;
            state.wrapMode = WrapMode.Loop;
            state.speed = playbackSpeed;
            state.normalizedTime = phaseOffset;
            dance.Play(dance.clip.name);
        }
    }
}

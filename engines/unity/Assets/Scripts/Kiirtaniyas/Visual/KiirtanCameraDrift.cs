using UnityEngine;

namespace Kiirtaniyas.Visual
{
    /// <summary>
    /// Adds a restrained camera drift so the real-time scene does not feel static.
    /// Keep amplitudes small to preserve the close isometric composition.
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class KiirtanCameraDrift : MonoBehaviour
    {
        [Min(0f)]
        [SerializeField]
        private float positionAmplitude = 0.04f;

        [Min(0f)]
        [SerializeField]
        private float rotationAmplitudeDegrees = 1.2f;

        [Min(0.01f)]
        [SerializeField]
        private float frequency = 0.12f;

        [SerializeField]
        private bool useUnscaledTime;

        private Vector3 baseLocalPosition;
        private Quaternion baseLocalRotation;

        public float MotionScale { get; set; } = 1f;

        private void Awake()
        {
            baseLocalPosition = transform.localPosition;
            baseLocalRotation = transform.localRotation;
        }

        private void LateUpdate()
        {
            float time = (useUnscaledTime ? Time.unscaledTime : Time.time) * frequency;
            float scale = Mathf.Max(0f, MotionScale);
            float sway = Mathf.Sin(time * Mathf.PI * 2f) * scale;
            float drift = Mathf.Sin(time * Mathf.PI * 1.37f + 0.8f) * scale;

            transform.localPosition = baseLocalPosition + new Vector3(
                sway * positionAmplitude,
                drift * positionAmplitude * 0.6f,
                0f);
            transform.localRotation = baseLocalRotation * Quaternion.Euler(
                drift * rotationAmplitudeDegrees,
                sway * rotationAmplitudeDegrees,
                sway * rotationAmplitudeDegrees * 0.35f);
        }
    }
}

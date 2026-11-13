using UnityEngine;

namespace Kiirtaniyas.Visual
{
    /// <summary>
    /// Moves a character around the central table on the XZ plane.
    /// A negative angle direction is clockwise when viewed from above.
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class KiirtanOrbitActor : MonoBehaviour
    {
        [SerializeField]
        private Transform orbitCenter;

        [Min(0f)]
        [SerializeField]
        private float radius = 2.2f;

        [SerializeField]
        private float heightOffset;

        [SerializeField]
        private float angularSpeedDegrees = 14f;

        [SerializeField]
        private bool clockwise = true;

        [SerializeField]
        private float phaseOffsetDegrees;

        [SerializeField]
        private bool faceDirection = true;

        [SerializeField]
        private float facingOffsetDegrees;

        [SerializeField]
        private float floatingAmplitude = 0.12f;

        [SerializeField]
        private float floatingFrequency = 0.65f;

        private float currentAngleDegrees;
        private bool orbitMotionEnabled = true;
        private Vector3 floatingAnchor;

        public Transform OrbitCenter
        {
            get { return orbitCenter; }
        }

        public bool Clockwise
        {
            get { return clockwise; }
        }

        public float Radius
        {
            get { return radius; }
            set { radius = Mathf.Max(0f, value); }
        }

        public float AngularSpeedDegrees
        {
            get { return angularSpeedDegrees; }
            set { angularSpeedDegrees = value; }
        }

        public bool OrbitMotionEnabled
        {
            get { return orbitMotionEnabled; }
        }

        public void SetOrbitCenter(Transform center)
        {
            orbitCenter = center;
            ApplyTransform();
        }

        public void SetPhase(float degrees)
        {
            phaseOffsetDegrees = degrees;
            currentAngleDegrees = degrees;
            ApplyTransform();
        }

        public void ResetOrbit()
        {
            orbitMotionEnabled = true;
            currentAngleDegrees = phaseOffsetDegrees;
            ApplyTransform();
        }

        public void SetOrbitMotionEnabled(bool enabled)
        {
            orbitMotionEnabled = enabled;
            if (!enabled)
            {
                floatingAnchor = transform.position;
            }
            else
            {
                ApplyTransform();
            }
        }

        public void SetFloatingAnchor(Vector3 worldPosition)
        {
            floatingAnchor = worldPosition;
            if (!orbitMotionEnabled)
            {
                ApplyFloatingTransform();
            }
        }

        private void Awake()
        {
            currentAngleDegrees = phaseOffsetDegrees;
            ApplyTransform();
        }

        private void Update()
        {
            if (!orbitMotionEnabled)
            {
                ApplyFloatingTransform();
                return;
            }

            if (orbitCenter == null || !isActiveAndEnabled)
            {
                return;
            }

            float direction = clockwise ? -1f : 1f;
            currentAngleDegrees = Mathf.Repeat(
                currentAngleDegrees + direction * angularSpeedDegrees * Time.deltaTime,
                360f);
            ApplyTransform();
        }

        private void ApplyFloatingTransform()
        {
            float wave = Mathf.Sin(Time.time * Mathf.PI * 2f * Mathf.Max(0.01f, floatingFrequency));
            transform.position = floatingAnchor + Vector3.up * (wave * floatingAmplitude);
        }

        private void ApplyTransform()
        {
            if (orbitCenter == null)
            {
                return;
            }

            float radians = currentAngleDegrees * Mathf.Deg2Rad;
            Vector3 radial = new Vector3(Mathf.Cos(radians), 0f, Mathf.Sin(radians)) * radius;
            Vector3 position = orbitCenter.position + radial;
            position.y += heightOffset;
            transform.position = position;

            if (!faceDirection)
            {
                return;
            }

            float direction = clockwise ? -1f : 1f;
            Vector3 tangent = new Vector3(-Mathf.Sin(radians), 0f, Mathf.Cos(radians)) * direction;
            if (tangent.sqrMagnitude < 0.0001f)
            {
                return;
            }

            transform.rotation = Quaternion.LookRotation(tangent, Vector3.up)
                * Quaternion.Euler(0f, facingOffsetDegrees, 0f);
        }
    }
}

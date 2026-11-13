using System.Collections.Generic;
using UnityEngine;

namespace Kiirtaniyas.Visual
{
    /// <summary>
    /// Lightweight procedural sacred geometry for the trippy cosmic stage.
    /// It is generated at runtime so the effect stays small on mobile and does not
    /// require a video or a large texture sequence.
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class KiirtanSacredGeometry : MonoBehaviour
    {
        [Range(1, 8)]
        [SerializeField]
        private int ringCount = 5;

        [Range(3, 12)]
        [SerializeField]
        private int sides = 6;

        [Min(0.1f)]
        [SerializeField]
        private float radius = 3.6f;

        [Min(0f)]
        [SerializeField]
        private float rotationSpeedDegrees = 4f;

        [Min(0f)]
        [SerializeField]
        private float pulseSpeed = 0.45f;

        [SerializeField]
        private Color geometryColor = new Color(0.35f, 0.85f, 1f, 0.9f);

        [SerializeField]
        private Color pulseColor = new Color(1f, 0.2f, 0.8f, 0.9f);

        private readonly List<LineRenderer> lines = new List<LineRenderer>();
        private Material lineMaterial;

        private void Awake()
        {
            BuildGeometry();
        }

        private void OnEnable()
        {
            if (lines.Count == 0)
            {
                BuildGeometry();
            }
        }

        private void OnDestroy()
        {
            for (int i = 0; i < lines.Count; i++)
            {
                if (lines[i] != null)
                {
                    DestroyObject(lines[i].gameObject);
                }
            }

            lines.Clear();
            if (lineMaterial != null)
            {
                DestroyObject(lineMaterial);
            }
        }

        private void Update()
        {
            transform.Rotate(Vector3.up, rotationSpeedDegrees * Time.deltaTime, Space.Self);
            float pulse = (Mathf.Sin(Time.time * Mathf.PI * 2f * pulseSpeed) + 1f) * 0.5f;
            if (lineMaterial != null)
            {
                lineMaterial.color = Color.Lerp(geometryColor, pulseColor, pulse);
            }
        }

        private void BuildGeometry()
        {
            ClearGeometry();
            Shader shader = Shader.Find("Sprites/Default");
            if (shader == null)
            {
                shader = Shader.Find("Unlit/Color");
            }

            if (shader == null)
            {
                return;
            }

            lineMaterial = new Material(shader)
            {
                color = geometryColor,
                name = "Kiirtan Sacred Geometry Runtime Material",
            };

            int safeRingCount = Mathf.Clamp(ringCount, 1, 8);
            int safeSides = Mathf.Clamp(sides, 3, 12);
            for (int ring = 0; ring < safeRingCount; ring++)
            {
                float ringRadius = radius * (ring + 1) / safeRingCount;
                LineRenderer line = CreateLine("Sacred Ring " + (ring + 1), lineMaterial);
                line.positionCount = safeSides;
                line.loop = true;
                for (int i = 0; i < safeSides; i++)
                {
                    float angle = (i / (float)safeSides) * Mathf.PI * 2f;
                    line.SetPosition(i, new Vector3(
                        Mathf.Cos(angle) * ringRadius,
                        0f,
                        Mathf.Sin(angle) * ringRadius));
                }
            }

            CreateStar("Sacred Star A", safeSides, 0f, lineMaterial);
            CreateStar("Sacred Star B", safeSides, Mathf.PI / safeSides, lineMaterial);
        }

        private LineRenderer CreateLine(string objectName, Material material)
        {
            GameObject lineObject = new GameObject(objectName);
            lineObject.transform.SetParent(transform, false);
            LineRenderer line = lineObject.AddComponent<LineRenderer>();
            line.useWorldSpace = false;
            line.widthMultiplier = 0.018f;
            line.numCapVertices = 2;
            line.material = material;
            lines.Add(line);
            return line;
        }

        private void CreateStar(string objectName, int pointCount, float phase, Material material)
        {
            LineRenderer line = CreateLine(objectName, material);
            line.positionCount = pointCount;
            line.loop = true;
            for (int i = 0; i < pointCount; i++)
            {
                float angle = phase + (i / (float)pointCount) * Mathf.PI * 2f;
                float starRadius = (i % 2 == 0) ? radius : radius * 0.42f;
                line.SetPosition(i, new Vector3(
                    Mathf.Cos(angle) * starRadius,
                    0f,
                    Mathf.Sin(angle) * starRadius));
            }
        }

        private void ClearGeometry()
        {
            for (int i = 0; i < lines.Count; i++)
            {
                if (lines[i] != null)
                {
                    DestroyObject(lines[i].gameObject);
                }
            }

            lines.Clear();
            if (lineMaterial != null)
            {
                DestroyObject(lineMaterial);
                lineMaterial = null;
            }
        }

        private static void DestroyObject(Object target)
        {
            if (target == null)
            {
                return;
            }

            if (Application.isPlaying)
            {
                Object.Destroy(target);
            }
            else
            {
                Object.DestroyImmediate(target);
            }
        }
    }
}

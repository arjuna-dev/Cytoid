using System;
using UnityEngine;

namespace Kiirtaniyas.Visual
{
    [Serializable]
    public sealed class KiirtanStageLayer
    {
        public KiirtanStage stage;
        public GameObject root;
        public Light[] lights = Array.Empty<Light>();
        public ParticleSystem[] particles = Array.Empty<ParticleSystem>();
        public Color ambientLight = Color.gray;
        public Color fogColor = Color.black;

        [Range(0f, 1f)]
        public float fogDensity;
    }
}

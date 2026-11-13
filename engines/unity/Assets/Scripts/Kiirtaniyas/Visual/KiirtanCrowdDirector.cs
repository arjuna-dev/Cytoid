using System;
using UnityEngine;

namespace Kiirtaniyas.Visual
{
    /// <summary>
    /// Owns the visible singers and keeps their count aligned with the visual stage.
    /// The main character remains visible until the final solo-cosmic stage.
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class KiirtanCrowdDirector : MonoBehaviour
    {
        [SerializeField]
        private Transform orbitCenter;

        [SerializeField]
        private KiirtanOrbitActor mainCharacter;

        [SerializeField]
        private KiirtanOrbitActor[] singers = Array.Empty<KiirtanOrbitActor>();

        [Tooltip("Singer counts for Intimate, Heavenly, CosmicSpace, CosmicFractal, and SoloCosmic.")]
        [SerializeField]
        private int[] singerCountsByStage = { 1, 2, 3, 8, 0 };

        private KiirtanStage currentStage = KiirtanStage.Intimate;

        public KiirtanStage CurrentStage
        {
            get { return currentStage; }
        }

        public int ActiveSingerCount { get; private set; }

        public void SetOrbitCenter(Transform center)
        {
            orbitCenter = center;
            ConfigureActor(mainCharacter);
            for (int i = 0; i < singers.Length; i++)
            {
                ConfigureActor(singers[i]);
            }
        }

        public void SetStage(KiirtanStage stage)
        {
            currentStage = stage;
            int desiredSingerCount = GetSingerCount(stage);
            ActiveSingerCount = 0;

            bool solo = stage == KiirtanStage.SoloCosmic;
            if (mainCharacter != null)
            {
                mainCharacter.gameObject.SetActive(true);
                ConfigureActor(mainCharacter);
                mainCharacter.SetOrbitMotionEnabled(!solo);
                if (solo)
                {
                    Vector3 anchor = mainCharacter.transform.position;
                    if (orbitCenter != null)
                    {
                        anchor = orbitCenter.position + Vector3.up * 1.8f;
                    }

                    mainCharacter.SetFloatingAnchor(anchor);
                }
                else
                {
                    mainCharacter.ResetOrbit();
                }
            }

            for (int i = 0; i < singers.Length; i++)
            {
                KiirtanOrbitActor singer = singers[i];
                if (singer == null)
                {
                    continue;
                }

                bool shouldBeActive = !solo && ActiveSingerCount < desiredSingerCount;
                singer.gameObject.SetActive(shouldBeActive);
                ConfigureActor(singer);
                if (shouldBeActive)
                {
                    ActiveSingerCount++;
                }
            }

        }

        private void Awake()
        {
            SetOrbitCenter(orbitCenter);
            SetStage(currentStage);
        }

        private int GetSingerCount(KiirtanStage stage)
        {
            if (singerCountsByStage == null || singerCountsByStage.Length == 0)
            {
                return 0;
            }

            int index = Mathf.Clamp((int)stage, 0, singerCountsByStage.Length - 1);
            return Mathf.Clamp(singerCountsByStage[index], 0, singers.Length);
        }

        private void ConfigureActor(KiirtanOrbitActor actor)
        {
            if (actor != null && orbitCenter != null)
            {
                actor.SetOrbitCenter(orbitCenter);
            }
        }
    }
}

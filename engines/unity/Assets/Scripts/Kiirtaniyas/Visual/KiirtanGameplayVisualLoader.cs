using Cysharp.Threading.Tasks;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace Kiirtaniyas.Visual
{
    /// <summary>
    /// Adds the authored Kiirtaniyas world to the inherited gameplay scene for
    /// standalone Android and Editor debugging.
    ///
    /// The gameplay scene remains authoritative for notes, input, and audio.
    /// This loader only composes the visual scene and binds its stage clock to
    /// the music AudioSource that the rhythm engine already schedules.
    /// </summary>
    public static class KiirtanGameplayVisualLoader
    {
        private const string VisualSceneName = "KiirtanMvp";
        private const string GameSceneName = "Game";
        private const string WorldRootName = "Kiirtan MVP World";
        private const string VisualLayerName = "KiirtanVisual";

        public static async UniTask LoadStandaloneForGame()
        {
            if (!Application.isPlaying || !GameEmbedMode.IsStandaloneDebug)
            {
                return;
            }

            Scene visualScene = SceneManager.GetSceneByName(VisualSceneName);
            if (!visualScene.IsValid() || !visualScene.isLoaded)
            {
                AsyncOperation loadOperation = SceneManager.LoadSceneAsync(
                    VisualSceneName,
                    LoadSceneMode.Additive);
                if (loadOperation == null)
                {
                    Debug.LogError("[Kiirtaniyas] Could not start additive load for " + VisualSceneName);
                    return;
                }

                await loadOperation;
                visualScene = SceneManager.GetSceneByName(VisualSceneName);
            }

            Scene gameScene = SceneManager.GetSceneByName(GameSceneName);
            if (gameScene.IsValid() && gameScene.isLoaded)
            {
                SceneManager.SetActiveScene(gameScene);
            }

            GameObject worldRoot = FindWorldRoot(visualScene);
            if (worldRoot == null)
            {
                Debug.LogError("[Kiirtaniyas] Additive visual scene has no '" + WorldRootName + "' root.");
                return;
            }

            int visualLayer = LayerMask.NameToLayer(VisualLayerName);
            if (visualLayer >= 0)
            {
                SetLayerRecursively(worldRoot, visualLayer);
            }

            Camera visualCamera = worldRoot.GetComponentInChildren<Camera>(true);
            ConfigureVisualCamera(visualCamera, visualLayer);

            Game gameplay = UnityEngine.Object.FindFirstObjectByType<Game>();
            Camera gameplayCamera = gameplay != null ? gameplay.camera : Camera.main;
            ConfigureGameplayCamera(gameplayCamera, visualLayer);

            KiirtanWorldDirector director = worldRoot.GetComponent<KiirtanWorldDirector>();
            if (director != null)
            {
                // The standalone preview scene starts its own source on enable.
                // Stop that source before handing the director the rhythm engine's
                // already scheduled source, so the world never creates a second
                // unsynchronised copy of the song.
                director.StopSong();
                await BindGameplayAudio(director);
            }

            Debug.Log("[Kiirtaniyas] Added KiirtanMvp to Game with visual camera "
                + (visualCamera == null ? "missing" : "ready")
                + " and gameplay audio binding "
                + (director == null ? "missing" : "ready") + ".");
        }

        private static async UniTask BindGameplayAudio(KiirtanWorldDirector director)
        {
            // Game.Initialize owns the source and schedules the clip shortly
            // after this bind. Do not wait for source.clip here, because the
            // inherited StartGame path schedules playback only after Initialize
            // returns. Keep the wait bounded so a malformed scene cannot hold
            // the navigation flow forever.
            for (int frame = 0; frame < 600; frame++)
            {
                AudioManager audioManager = Context.AudioManager;
                if (audioManager != null
                    && audioManager.IsInitialized
                    && audioManager.audioSources != null
                    && audioManager.audioSources.Length > 0
                    && audioManager.audioSources[0] != null)
                {
                    director.SetAudioSource(audioManager.audioSources[0]);
                    director.StopSong();
                    return;
                }

                await UniTask.DelayFrame(1);
            }

            Debug.LogWarning("[Kiirtaniyas] Timed out waiting for the gameplay audio source; "
                + "the visual world will remain at its initial stage.");
        }

        private static GameObject FindWorldRoot(Scene scene)
        {
            if (!scene.IsValid() || !scene.isLoaded)
            {
                return null;
            }

            GameObject[] roots = scene.GetRootGameObjects();
            for (int i = 0; i < roots.Length; i++)
            {
                if (roots[i] != null && roots[i].name == WorldRootName)
                {
                    return roots[i];
                }
            }

            return null;
        }

        private static void ConfigureVisualCamera(Camera camera, int visualLayer)
        {
            if (camera == null)
            {
                return;
            }

            camera.tag = "Untagged";
            camera.depth = -10f;
            camera.enabled = true;
            if (visualLayer >= 0)
            {
                camera.cullingMask = 1 << visualLayer;
            }
        }

        private static void ConfigureGameplayCamera(Camera camera, int visualLayer)
        {
            if (camera == null)
            {
                return;
            }

            camera.depth = 0f;
            camera.clearFlags = CameraClearFlags.Depth;
            if (visualLayer >= 0)
            {
                camera.cullingMask &= ~(1 << visualLayer);
            }
        }

        private static void SetLayerRecursively(GameObject root, int layer)
        {
            if (root == null)
            {
                return;
            }

            root.layer = layer;
            Transform transform = root.transform;
            for (int i = 0; i < transform.childCount; i++)
            {
                SetLayerRecursively(transform.GetChild(i).gameObject, layer);
            }
        }
    }
}

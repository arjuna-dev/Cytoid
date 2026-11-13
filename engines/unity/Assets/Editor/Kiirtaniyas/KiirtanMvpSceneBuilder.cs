#if UNITY_EDITOR
using System;
using System.Collections.Generic;
using Kiirtaniyas.Visual;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace Kiirtaniyas.Editor
{
    /// <summary>
    /// Builds a repeatable, asset-backed scene for the first Kiirtaniyas vertical slice.
    /// The generated scene stays separate from the inherited Cytoid gameplay scenes.
    /// </summary>
    public static class KiirtanMvpSceneBuilder
    {
        private const string ScenePath = "Assets/Scenes/KiirtanMvp.unity";
        private const string PrefabPath = "Assets/Kiirtaniyas/Art/KiirtanMvpWorld.prefab";
        private const string ModelRoot = "Assets/Kiirtaniyas/Art/Models/";
        private const string MaterialRoot = "Assets/Kiirtaniyas/Art/Materials/";
        private const string AudioPath = "Assets/Kiirtaniyas/Audio/Hladini_shakti_excerpt.mp3";

        [MenuItem("Kiirtaniyas/Build MVP World Scene")]
        public static void BuildMvpScene()
        {
            EnsureFolder("Assets/Kiirtaniyas");
            EnsureFolder("Assets/Kiirtaniyas/Art");
            EnsureFolder(MaterialRoot.TrimEnd('/'));

            Scene scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            GameObject world = new GameObject("Kiirtan MVP World");
            Transform center = CreateEmpty(world.transform, "Central Table Orbit Center");
            Transform charactersRoot = CreateEmpty(world.transform, "Characters");
            Transform intimateRoot = CreateEmpty(world.transform, "Stage - Intimate Courtyard");
            Transform heavenlyRoot = CreateEmpty(world.transform, "Stage - Heavenly");
            Transform cosmicSpaceRoot = CreateEmpty(world.transform, "Stage - Cosmic Space");
            Transform cosmicFractalRoot = CreateEmpty(world.transform, "Stage - Cosmic Fractal");
            Transform soloCosmicRoot = CreateEmpty(world.transform, "Stage - Solo Cosmic");

            BuildCourtyard(intimateRoot);
            BuildHeavenlyLayer(heavenlyRoot);
            BuildCosmicSpaceLayer(cosmicSpaceRoot);
            BuildCosmicFractalLayer(cosmicFractalRoot);

            CreateKeyLight(world.transform);
            Camera camera = CreateCamera(world.transform, center);
            AudioSource audioSource = CreateAudioSource(world.transform);

            KiirtanOrbitActor mainCharacter = BuildCharacter(
                "MC - Raised Hands",
                "SingerRaised.fbx",
                charactersRoot,
                center,
                2.7f,
                0f,
                14f);

            List<KiirtanOrbitActor> singers = new List<KiirtanOrbitActor>();
            singers.Add(BuildCharacter(
                "Singer 01 - Raised Hands",
                "SingerRaised.fbx",
                charactersRoot,
                center,
                2.7f,
                180f,
                14f));

            for (int i = 1; i < 8; i++)
            {
                singers.Add(BuildCharacter(
                    "Singer " + (i + 1).ToString("00") + " - Joined Palms",
                    "SingerJoined.fbx",
                    charactersRoot,
                    center,
                    2.7f,
                    180f + ((i - 1) * 45f),
                    14f));
            }

            KiirtanCrowdDirector crowd = world.AddComponent<KiirtanCrowdDirector>();
            ConfigureCrowd(crowd, center, mainCharacter, singers);

            KiirtanWorldDirector director = world.AddComponent<KiirtanWorldDirector>();
            ConfigureWorldDirector(
                director,
                audioSource,
                crowd,
                intimateRoot,
                heavenlyRoot,
                cosmicSpaceRoot,
                cosmicFractalRoot,
                soloCosmicRoot);

            PrefabUtility.SaveAsPrefabAsset(world, PrefabPath);
            Selection.activeGameObject = world;
            EditorSceneManager.SaveScene(scene, ScenePath);
            AddSceneToBuildSettings(ScenePath);
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            Debug.Log("[Kiirtaniyas] Built MVP world scene at " + ScenePath + " and prefab " + PrefabPath + " with camera " + camera.name + ".");
        }

        [MenuItem("Kiirtaniyas/Validate Singer Animation Imports")]
        public static void ValidateSingerAnimationImports()
        {
            foreach (string modelName in new[] { "SingerRaised.fbx", "SingerJoined.fbx" })
            {
                string assetPath = ModelRoot + modelName;
                GameObject prefab = AssetDatabase.LoadAssetAtPath<GameObject>(assetPath);
                Animation animation = prefab == null ? null : prefab.GetComponentInChildren<Animation>(true);
                if (animation == null || animation.clip == null)
                {
                    throw new InvalidOperationException("No legacy animation clip was imported for " + assetPath);
                }

                Debug.Log("[Kiirtaniyas] " + modelName + " animation clip " + animation.clip.name
                    + " length=" + animation.clip.length.ToString("F3") + "s wrap=" + animation.clip.wrapMode);
            }
        }

        private static void BuildCourtyard(Transform parent)
        {
            GameObject courtyard = InstantiateModel("Courtyard.fbx", parent, "Courtyard - Blender MVP");
            if (courtyard == null)
            {
                CreatePrimitiveFallback(parent, PrimitiveType.Cylinder, "Courtyard Placeholder", new Vector3(5f, 0.15f, 5f));
            }
        }

        private static void BuildHeavenlyLayer(Transform parent)
        {
            GameObject fireflies = new GameObject("Heavenly Fireflies");
            fireflies.transform.SetParent(parent, false);
            ParticleSystem particles = fireflies.AddComponent<ParticleSystem>();
            ParticleSystem.MainModule main = particles.main;
            main.loop = true;
            main.playOnAwake = true;
            main.maxParticles = 80;
            main.startLifetime = 6f;
            main.startSpeed = 0.08f;
            main.startSize = 0.04f;
            main.startColor = new Color(1f, 0.72f, 0.28f, 0.8f);
            main.simulationSpace = ParticleSystemSimulationSpace.Local;
            ParticleSystem.EmissionModule emission = particles.emission;
            emission.rateOverTime = 7f;
            ParticleSystem.ShapeModule shape = particles.shape;
            shape.shapeType = ParticleSystemShapeType.Sphere;
            shape.radius = 4.2f;

            ParticleSystemRenderer renderer = fireflies.GetComponent<ParticleSystemRenderer>();
            renderer.renderMode = ParticleSystemRenderMode.Billboard;
            renderer.material = GetOrCreateMaterial(
                "HeavenlyFireflies.mat",
                new[] { "Particles/Standard Unlit", "Legacy Shaders/Particles/Alpha Blended Premultiply", "Sprites/Default" },
                new Color(1f, 0.72f, 0.28f, 0.8f));

            CreateStageLight(
                parent,
                "Heavenly Warm Light",
                new Color(1f, 0.64f, 0.38f),
                3.5f,
                12f,
                new Vector3(0f, 4f, -1f));
            CreateStageLight(
                parent,
                "Heavenly Rim Light",
                new Color(0.52f, 0.72f, 1f),
                2.2f,
                10f,
                new Vector3(-4f, 2.5f, 3f));
        }

        private static void BuildCosmicSpaceLayer(Transform parent)
        {
            GameObject stars = new GameObject("Cosmic Starfield");
            stars.transform.SetParent(parent, false);
            ParticleSystem particles = stars.AddComponent<ParticleSystem>();
            ParticleSystem.MainModule main = particles.main;
            main.loop = true;
            main.playOnAwake = true;
            main.maxParticles = 220;
            main.startLifetime = 90f;
            main.startSpeed = 0f;
            main.startSize = 0.035f;
            main.startColor = new Color(0.55f, 0.78f, 1f, 0.9f);
            main.simulationSpace = ParticleSystemSimulationSpace.Local;
            ParticleSystem.EmissionModule emission = particles.emission;
            emission.rateOverTime = 20f;
            ParticleSystem.ShapeModule shape = particles.shape;
            shape.shapeType = ParticleSystemShapeType.Sphere;
            shape.radius = 6f;

            ParticleSystemRenderer renderer = stars.GetComponent<ParticleSystemRenderer>();
            renderer.renderMode = ParticleSystemRenderMode.Billboard;
            renderer.material = GetOrCreateMaterial(
                "CosmicStars.mat",
                new[] { "Particles/Standard Unlit", "Legacy Shaders/Particles/Alpha Blended Premultiply", "Sprites/Default" },
                new Color(0.55f, 0.78f, 1f, 0.9f));

            CreateStageLight(
                parent,
                "Cosmic Blue Light",
                new Color(0.16f, 0.34f, 1f),
                2.5f,
                14f,
                new Vector3(0f, 3f, 0f));
        }

        private static void BuildCosmicFractalLayer(Transform parent)
        {
            GameObject geometry = new GameObject("Sacred Geometry Field");
            geometry.transform.SetParent(parent, false);
            geometry.AddComponent<KiirtanSacredGeometry>();
            CreateStageLight(
                parent,
                "Fractal Magenta Light",
                new Color(0.82f, 0.16f, 0.9f),
                2.4f,
                13f,
                new Vector3(0f, 2.5f, 0f));
        }

        private static void CreateKeyLight(Transform parent)
        {
            GameObject lightObject = new GameObject("Key Light");
            lightObject.transform.SetParent(parent, false);
            lightObject.transform.rotation = Quaternion.Euler(48f, -28f, 0f);
            Light light = lightObject.AddComponent<Light>();
            light.type = LightType.Directional;
            light.intensity = 1.15f;
            light.color = new Color(1f, 0.83f, 0.68f);
        }

        private static Camera CreateCamera(Transform parent, Transform target)
        {
            GameObject cameraObject = new GameObject("Isometric Camera");
            cameraObject.transform.SetParent(parent, false);
            cameraObject.transform.position = new Vector3(8.2f, 8.2f, -8.2f);
            cameraObject.transform.rotation = LookAt(cameraObject.transform.position, target.position + Vector3.up * 0.6f);
            Camera camera = cameraObject.AddComponent<Camera>();
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = new Color(0.015f, 0.02f, 0.045f, 1f);
            camera.orthographic = true;
            camera.orthographicSize = 6.4f;
            camera.nearClipPlane = 0.05f;
            camera.farClipPlane = 100f;
            cameraObject.AddComponent<KiirtanCameraDrift>();
            return camera;
        }

        private static AudioSource CreateAudioSource(Transform parent)
        {
            GameObject audioObject = new GameObject("Kiirtan Song Audio");
            audioObject.transform.SetParent(parent, false);
            AudioSource source = audioObject.AddComponent<AudioSource>();
            source.playOnAwake = false;
            source.loop = false;
            source.spatialBlend = 0f;
            source.volume = 1f;
            source.clip = AssetDatabase.LoadAssetAtPath<AudioClip>(AudioPath);
            return source;
        }

        private static KiirtanOrbitActor BuildCharacter(
            string name,
            string modelName,
            Transform parent,
            Transform center,
            float radius,
            float phase,
            float speed)
        {
            GameObject wrapper = new GameObject(name);
            wrapper.transform.SetParent(parent, false);
            GameObject model = InstantiateModel(modelName, wrapper.transform, modelName.Replace(".fbx", string.Empty));
            if (model == null)
            {
                CreatePrimitiveFallback(wrapper.transform, PrimitiveType.Capsule, "Character Placeholder", new Vector3(0.45f, 0.9f, 0.45f));
            }

            // The model carries the Blender-authored looping Lalita Marmika
            // clip. Keep the phase slightly different per singer so the orbit
            // reads as a living gathering rather than a synchronized loop.
            KiirtanDancePlayer dance = wrapper.AddComponent<KiirtanDancePlayer>();
            dance.SetPhase(Mathf.Repeat(phase / 360f, 1f));

            KiirtanOrbitActor actor = wrapper.AddComponent<KiirtanOrbitActor>();
            actor.Radius = radius;
            actor.AngularSpeedDegrees = speed;
            actor.SetOrbitCenter(center);
            actor.SetPhase(phase);
            EditorUtility.SetDirty(actor);
            return actor;
        }

        private static void ConfigureCrowd(
            KiirtanCrowdDirector crowd,
            Transform center,
            KiirtanOrbitActor mainCharacter,
            List<KiirtanOrbitActor> singers)
        {
            SerializedObject serialized = new SerializedObject(crowd);
            serialized.FindProperty("orbitCenter").objectReferenceValue = center;
            serialized.FindProperty("mainCharacter").objectReferenceValue = mainCharacter;
            SerializedProperty singerArray = serialized.FindProperty("singers");
            singerArray.arraySize = singers.Count;
            for (int i = 0; i < singers.Count; i++)
            {
                singerArray.GetArrayElementAtIndex(i).objectReferenceValue = singers[i];
            }

            SerializedProperty counts = serialized.FindProperty("singerCountsByStage");
            int[] desiredCounts = { 1, 2, 3, 8, 0 };
            counts.arraySize = desiredCounts.Length;
            for (int i = 0; i < desiredCounts.Length; i++)
            {
                counts.GetArrayElementAtIndex(i).intValue = desiredCounts[i];
            }

            serialized.ApplyModifiedPropertiesWithoutUndo();
            crowd.SetOrbitCenter(center);
            crowd.SetStage(KiirtanStage.Intimate);
            EditorUtility.SetDirty(crowd);
        }

        private static void ConfigureWorldDirector(
            KiirtanWorldDirector director,
            AudioSource audioSource,
            KiirtanCrowdDirector crowd,
            Transform intimateRoot,
            Transform heavenlyRoot,
            Transform cosmicSpaceRoot,
            Transform cosmicFractalRoot,
            Transform soloCosmicRoot)
        {
            SerializedObject serialized = new SerializedObject(director);
            serialized.FindProperty("songAudioSource").objectReferenceValue = audioSource;
            serialized.FindProperty("driveFromAudioSource").boolValue = true;
            serialized.FindProperty("playAudioOnEnable").boolValue = true;
            serialized.FindProperty("restartAudioOnEnable").boolValue = true;
            serialized.FindProperty("advanceManualClock").boolValue = false;
            serialized.FindProperty("transitionSeconds").floatValue = 2f;
            serialized.FindProperty("controlRenderSettings").boolValue = true;

            SerializedProperty timeline = serialized.FindProperty("timeline");
            timeline.FindPropertyRelative("durationSeconds").floatValue = 210f;
            SerializedProperty markers = timeline.FindPropertyRelative("markers");
            KiirtanStageMarker[] defaults =
            {
                new KiirtanStageMarker(KiirtanStage.Intimate, 0f),
                new KiirtanStageMarker(KiirtanStage.Heavenly, 0.25f),
                new KiirtanStageMarker(KiirtanStage.CosmicSpace, 0.5f),
                new KiirtanStageMarker(KiirtanStage.CosmicFractal, 0.75f),
                new KiirtanStageMarker(KiirtanStage.SoloCosmic, 0.95f),
            };
            markers.arraySize = defaults.Length;
            for (int i = 0; i < defaults.Length; i++)
            {
                SerializedProperty marker = markers.GetArrayElementAtIndex(i);
                marker.FindPropertyRelative("stage").enumValueIndex = (int)defaults[i].stage;
                marker.FindPropertyRelative("normalizedStart").floatValue = defaults[i].normalizedStart;
            }

            serialized.FindProperty("crowdDirector").objectReferenceValue = crowd;
            SerializedProperty layers = serialized.FindProperty("stageLayers");
            layers.arraySize = 5;
            ConfigureLayer(layers.GetArrayElementAtIndex(0), KiirtanStage.Intimate, intimateRoot, new Color(0.42f, 0.32f, 0.25f), new Color(0.08f, 0.06f, 0.09f), 0.015f);
            ConfigureLayer(layers.GetArrayElementAtIndex(1), KiirtanStage.Heavenly, heavenlyRoot, new Color(0.82f, 0.52f, 0.32f), new Color(0.19f, 0.08f, 0.18f), 0.02f);
            ConfigureLayer(layers.GetArrayElementAtIndex(2), KiirtanStage.CosmicSpace, cosmicSpaceRoot, new Color(0.08f, 0.13f, 0.42f), Color.black, 0.008f);
            ConfigureLayer(layers.GetArrayElementAtIndex(3), KiirtanStage.CosmicFractal, cosmicFractalRoot, new Color(0.12f, 0.03f, 0.18f), Color.black, 0.004f);
            ConfigureLayer(layers.GetArrayElementAtIndex(4), KiirtanStage.SoloCosmic, soloCosmicRoot, Color.black, Color.black, 0f);
            serialized.ApplyModifiedPropertiesWithoutUndo();

            intimateRoot.gameObject.SetActive(true);
            heavenlyRoot.gameObject.SetActive(false);
            cosmicSpaceRoot.gameObject.SetActive(false);
            cosmicFractalRoot.gameObject.SetActive(false);
            soloCosmicRoot.gameObject.SetActive(false);
            EditorUtility.SetDirty(director);
        }

        private static void ConfigureLayer(
            SerializedProperty layer,
            KiirtanStage stage,
            Transform root,
            Color ambient,
            Color fog,
            float fogDensity)
        {
            layer.FindPropertyRelative("stage").enumValueIndex = (int)stage;
            layer.FindPropertyRelative("root").objectReferenceValue = root.gameObject;
            layer.FindPropertyRelative("ambientLight").colorValue = ambient;
            layer.FindPropertyRelative("fogColor").colorValue = fog;
            layer.FindPropertyRelative("fogDensity").floatValue = fogDensity;
        }

        private static GameObject InstantiateModel(string modelName, Transform parent, string objectName)
        {
            string assetPath = ModelRoot + modelName;
            GameObject prefab = AssetDatabase.LoadAssetAtPath<GameObject>(assetPath);
            if (prefab == null)
            {
                Debug.LogWarning("[Kiirtaniyas] Blender model not imported yet: " + assetPath);
                return null;
            }

            GameObject instance = PrefabUtility.InstantiatePrefab(prefab) as GameObject;
            if (instance == null)
            {
                Debug.LogWarning("[Kiirtaniyas] Could not instantiate model: " + assetPath);
                return null;
            }

            instance.name = objectName;
            instance.transform.SetParent(parent, false);
            return instance;
        }

        private static void CreateStageLight(
            Transform parent,
            string name,
            Color color,
            float intensity,
            float range,
            Vector3 position)
        {
            GameObject lightObject = new GameObject(name);
            lightObject.transform.SetParent(parent, false);
            lightObject.transform.localPosition = position;
            Light light = lightObject.AddComponent<Light>();
            light.type = LightType.Point;
            light.color = color;
            light.intensity = intensity;
            light.range = range;
            light.shadows = LightShadows.None;
        }

        private static GameObject CreatePrimitiveFallback(
            Transform parent,
            PrimitiveType type,
            string name,
            Vector3 scale)
        {
            GameObject primitive = GameObject.CreatePrimitive(type);
            primitive.name = name;
            primitive.transform.SetParent(parent, false);
            primitive.transform.localScale = scale;
            return primitive;
        }

        private static Transform CreateEmpty(Transform parent, string name)
        {
            GameObject gameObject = new GameObject(name);
            gameObject.transform.SetParent(parent, false);
            return gameObject.transform;
        }

        private static Quaternion LookAt(Vector3 position, Vector3 target)
        {
            Vector3 direction = target - position;
            return direction.sqrMagnitude < 0.0001f
                ? Quaternion.identity
                : Quaternion.LookRotation(direction.normalized, Vector3.up);
        }

        private static Material GetOrCreateMaterial(string fileName, string[] shaderNames, Color color)
        {
            string path = MaterialRoot + fileName;
            Material material = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (material == null)
            {
                Shader shader = null;
                for (int i = 0; i < shaderNames.Length && shader == null; i++)
                {
                    shader = Shader.Find(shaderNames[i]);
                }

                if (shader == null)
                {
                    return null;
                }

                material = new Material(shader);
                AssetDatabase.CreateAsset(material, path);
            }

            material.color = color;
            EditorUtility.SetDirty(material);
            return material;
        }

        private static void EnsureFolder(string path)
        {
            if (AssetDatabase.IsValidFolder(path))
            {
                return;
            }

            string parent = System.IO.Path.GetDirectoryName(path)?.Replace("\\", "/");
            string name = System.IO.Path.GetFileName(path);
            if (string.IsNullOrEmpty(parent) || string.IsNullOrEmpty(name))
            {
                return;
            }

            EnsureFolder(parent);
            AssetDatabase.CreateFolder(parent, name);
        }

        private static void AddSceneToBuildSettings(string scenePath)
        {
            List<EditorBuildSettingsScene> scenes = new List<EditorBuildSettingsScene>(EditorBuildSettings.scenes);
            for (int i = 0; i < scenes.Count; i++)
            {
                if (scenes[i].path == scenePath)
                {
                    scenes[i].enabled = true;
                    EditorBuildSettings.scenes = scenes.ToArray();
                    return;
                }
            }

            scenes.Add(new EditorBuildSettingsScene(scenePath, true));
            EditorBuildSettings.scenes = scenes.ToArray();
        }
    }
}
#endif

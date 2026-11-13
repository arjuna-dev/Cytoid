#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;
using UnityEngine;

namespace Kiirtaniyas.Editor
{
    /// <summary>
    /// Builds the isolated Android presentation scene used to smoke-test the
    /// Blender exports, audio clock, and stage timeline on a device.
    /// </summary>
    public static class KiirtanMvpBuild
    {
        private const string ScenePath = "Assets/Scenes/KiirtanMvp.unity";
        private const string BootstrapperScenePath = "Assets/Scenes/Bootstrapper.unity";
        private const string NavigationScenePath = "Assets/Scenes/Navigation.unity";
        private const string GameScenePath = "Assets/Scenes/Game.unity";
        private const string ProductionApplicationIdentifier = "me.tigerhix.cytoid";

        [MenuItem("Kiirtaniyas/Build Android MVP APK")]
        public static void BuildAndroidMvpMenu()
        {
            BuildAndroid(ResolveOutputPath(), new[] { ScenePath });
        }

        /// <summary>
        /// Batch entry point for Unity CLI:
        /// -executeMethod Kiirtaniyas.Editor.KiirtanMvpBuild.BuildAndroidMvpBatch
        /// </summary>
        public static void BuildAndroidMvpBatch()
        {
            BuildAndroid(ResolveOutputPath(), new[] { ScenePath });
        }

        [MenuItem("Kiirtaniyas/Build Android Menu APK")]
        public static void BuildAndroidMenuMenu()
        {
            BuildAndroid(ResolveOutputPath(), GetMenuScenes());
        }

        /// <summary>
        /// Batch entry point for the inherited Cytoid navigation flow with the
        /// Kiirtaniyas built-in level selected by DebugNavigationController.
        /// </summary>
        public static void BuildAndroidMenuBatch()
        {
            BuildAndroid(ResolveOutputPath(), GetMenuScenes());
        }

        private static void BuildAndroid(string outputPath, string[] scenes)
        {
            foreach (string scene in scenes)
            {
                if (!File.Exists(scene))
                {
                    throw new FileNotFoundException("Required Unity scene was not found.", scene);
                }
            }

            string fullOutputPath = Path.GetFullPath(outputPath);
            Directory.CreateDirectory(Path.GetDirectoryName(fullOutputPath));
            string previousApplicationIdentifier = PlayerSettings.GetApplicationIdentifier(NamedBuildTarget.Android);
            string previousAndroidDefines = PlayerSettings.GetScriptingDefineSymbols(NamedBuildTarget.Android);
            try
            {
                EditorUserBuildSettings.SwitchActiveBuildTarget(BuildTargetGroup.Android, BuildTarget.Android);
                EditorUserBuildSettings.exportAsGoogleAndroidProject = false;
                EditorUserBuildSettings.buildAppBundle = false;
                PlayerSettings.SetApplicationIdentifier(NamedBuildTarget.Android, ProductionApplicationIdentifier);
                // This APK contains the standalone Navigation scene. If a prior
                // plugin export left CYTOID_FLUTTER_HOST enabled, GameEmbedMode
                // switches to bridge mode, disables DebugNavigationController,
                // and attempts to call a Flutter callback that is not present in
                // this APK. Keep the standalone build isolated from that state.
                PlayerSettings.SetScriptingDefineSymbols(
                    NamedBuildTarget.Android,
                    RemoveDefineSymbol(previousAndroidDefines, "CYTOID_FLUTTER_HOST"));
                PlayerSettings.Android.targetArchitectures = AndroidArchitecture.ARM64;
                PlayerSettings.Android.useCustomKeystore = false;

                BuildPlayerOptions options = new BuildPlayerOptions
                {
                    scenes = scenes,
                    locationPathName = fullOutputPath,
                    target = BuildTarget.Android,
                    targetGroup = BuildTargetGroup.Android,
                    options = BuildOptions.Development,
                };

                BuildReport report = BuildPipeline.BuildPlayer(options);
                if (report.summary.result != BuildResult.Succeeded)
                {
                    foreach (BuildStep step in report.steps)
                    {
                        foreach (BuildStepMessage message in step.messages.Where(item => item.type == LogType.Error || item.type == LogType.Exception))
                        {
                            Debug.LogError("[Kiirtaniyas] Android build: " + message.content);
                        }
                    }

                    throw new InvalidOperationException("Kiirtan MVP Android build failed: " + report.summary.result);
                }

                Debug.Log("[Kiirtaniyas] Android MVP APK built at " + fullOutputPath);
            }
            finally
            {
                PlayerSettings.SetApplicationIdentifier(NamedBuildTarget.Android, previousApplicationIdentifier);
                PlayerSettings.SetScriptingDefineSymbols(NamedBuildTarget.Android, previousAndroidDefines);
                AssetDatabase.SaveAssets();
            }
        }

        private static string RemoveDefineSymbol(string defines, string symbolToRemove)
        {
            return string.Join(
                ";",
                (defines ?? string.Empty)
                    .Split(new[] { ';' }, StringSplitOptions.RemoveEmptyEntries)
                    .Select(symbol => symbol.Trim())
                    .Where(symbol => !string.Equals(symbol, symbolToRemove, StringComparison.Ordinal)));
        }

        private static string[] GetMenuScenes()
        {
            return new[]
            {
                BootstrapperScenePath,
                NavigationScenePath,
                GameScenePath,
                ScenePath,
            };
        }

        private static string ResolveOutputPath()
        {
            string[] args = Environment.GetCommandLineArgs();
            for (int i = 0; i + 1 < args.Length; i++)
            {
                if (args[i] == "-buildOutput")
                {
                    return args[i + 1];
                }
            }

            string environmentPath = Environment.GetEnvironmentVariable("KIIRTAN_ANDROID_OUTPUT");
            return string.IsNullOrWhiteSpace(environmentPath)
                ? "Builds/KiirtaniyasMvp.apk"
                : environmentPath;
        }
    }
}
#endif

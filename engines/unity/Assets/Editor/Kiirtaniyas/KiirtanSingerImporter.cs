using System;
using UnityEditor;
using UnityEngine;

namespace Kiirtaniyas.Editor
{
    /// <summary>Imports the Blender transform dance as an automatically looping clip.</summary>
    public sealed class KiirtanSingerImporter : AssetPostprocessor
    {
        private void OnPreprocessModel()
        {
            if (!IsSinger(assetPath)) return;
            var importer = (ModelImporter)assetImporter;
            importer.importAnimation = true;
            importer.animationType = ModelImporterAnimationType.Legacy;
            importer.animationWrapMode = WrapMode.Loop;
        }

        private void OnPostprocessAnimation(GameObject root, AnimationClip clip)
        {
            if (!IsSinger(assetPath)) return;
            clip.wrapMode = WrapMode.Loop;
        }

        private static bool IsSinger(string path)
        {
            return string.Equals(path, "Assets/Kiirtaniyas/Art/Models/SingerRaised.fbx", StringComparison.Ordinal)
                || string.Equals(path, "Assets/Kiirtaniyas/Art/Models/SingerJoined.fbx", StringComparison.Ordinal);
        }
    }
}

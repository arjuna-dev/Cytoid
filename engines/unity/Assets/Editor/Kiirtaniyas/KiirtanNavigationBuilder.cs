#if UNITY_EDITOR
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

namespace Kiirtaniyas.Editor
{
    /// <summary>
    /// Keeps the inherited debug navigation logic while giving the first song
    /// a readable Kiirtaniyas title and track card.
    /// </summary>
    public static class KiirtanNavigationBuilder
    {
        private const string ScenePath = "Assets/Scenes/Navigation.unity";
        private const string CanvasName = "Debug Navigation Canvas";
        private const string BackgroundName = "Kiirtaniyas Menu Background";
        private const string HeaderName = "Kiirtaniyas Menu Header";
        private const string TrackName = "Kiirtaniyas Track Card";

        [MenuItem("Kiirtaniyas/Prepare Navigation Menu")]
        public static void PrepareNavigationMenu()
        {
            Scene scene = EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
            GameObject canvasObject = GameObject.Find(CanvasName);
            if (canvasObject == null)
            {
                throw new System.InvalidOperationException("Could not find " + CanvasName + " in " + ScenePath);
            }

            RectTransform canvas = canvasObject.GetComponent<RectTransform>();
            canvas.localScale = Vector3.one;
            canvas.anchorMin = Vector2.zero;
            canvas.anchorMax = Vector2.one;
            canvas.offsetMin = Vector2.zero;
            canvas.offsetMax = Vector2.zero;

            CreateBackground(canvas);
            CreateText(canvas, HeaderName, "KIIRTANIYAS UNITED", new Vector2(0.5f, 1f), new Vector2(0f, -92f), new Vector2(1320f, 110f), 72, new Color(1f, 0.86f, 0.58f, 1f), true);
            CreateText(canvas, TrackName, "Hladini shakti kiirtana  |  3:00 - 6:30 excerpt", new Vector2(0.5f, 1f), new Vector2(0f, -174f), new Vector2(1500f, 74f), 30, new Color(0.82f, 0.9f, 0.94f, 1f), false);
            CreateText(canvas, "Kiirtaniyas Menu Hint", "Choose a difficulty to begin", new Vector2(0.5f, 1f), new Vector2(0f, -226f), new Vector2(1200f, 56f), 24, new Color(0.72f, 0.78f, 0.84f, 1f), false);

            EditorSceneManager.MarkSceneDirty(scene);
            EditorSceneManager.SaveScene(scene);
            AssetDatabase.SaveAssets();
            Debug.Log("[Kiirtaniyas] Prepared Navigation menu with the first song card.");
        }

        public static void PrepareNavigationMenuBatch()
        {
            PrepareNavigationMenu();
        }

        private static void CreateBackground(RectTransform canvas)
        {
            Transform existing = canvas.Find(BackgroundName);
            GameObject background = existing == null
                ? new GameObject(BackgroundName, typeof(RectTransform), typeof(CanvasRenderer), typeof(Image))
                : existing.gameObject;
            RectTransform rect = background.GetComponent<RectTransform>();
            rect.SetParent(canvas, false);
            rect.anchorMin = Vector2.zero;
            rect.anchorMax = Vector2.one;
            rect.offsetMin = Vector2.zero;
            rect.offsetMax = Vector2.zero;
            rect.SetAsFirstSibling();

            Image image = background.GetComponent<Image>();
            image.color = new Color(0.025f, 0.04f, 0.075f, 0.97f);
            image.raycastTarget = false;
        }

        private static void CreateText(
            RectTransform canvas,
            string objectName,
            string value,
            Vector2 anchor,
            Vector2 position,
            Vector2 size,
            int fontSize,
            Color color,
            bool bold)
        {
            Transform existing = canvas.Find(objectName);
            GameObject textObject = existing == null
                ? new GameObject(objectName, typeof(RectTransform), typeof(CanvasRenderer), typeof(Text))
                : existing.gameObject;
            RectTransform rect = textObject.GetComponent<RectTransform>();
            rect.SetParent(canvas, false);
            rect.anchorMin = anchor;
            rect.anchorMax = anchor;
            rect.anchoredPosition = position;
            rect.sizeDelta = size;
            rect.localScale = Vector3.one;

            Text text = textObject.GetComponent<Text>();
            text.font = AssetDatabase.LoadAssetAtPath<Font>(bold
                ? "Assets/Resources/Fonts/Nunito-Bold.ttf"
                : "Assets/Resources/Fonts/Nunito-Regular.ttf");
            text.fontSize = fontSize;
            text.fontStyle = bold ? FontStyle.Bold : FontStyle.Normal;
            text.alignment = TextAnchor.MiddleCenter;
            text.horizontalOverflow = HorizontalWrapMode.Overflow;
            text.verticalOverflow = VerticalWrapMode.Overflow;
            text.color = color;
            text.raycastTarget = false;
            text.text = value;
        }
    }
}
#endif

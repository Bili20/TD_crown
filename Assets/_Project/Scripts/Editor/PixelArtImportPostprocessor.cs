using UnityEditor;
using UnityEngine;

namespace TDCrown.EditorTools
{
    // Aplica as regras de import da Art Bible (docs/ART_BIBLE.md §8) só na primeira importação,
    // para que ajustes manuais feitos depois no Inspector não sejam sobrescritos.
    public class PixelArtImportPostprocessor : AssetPostprocessor
    {
        private const string PixelArtRoot = "Assets/_Project/Art/";
        private const string VectorUiRoot = "Assets/_Project/Art/UI/";
        private const float PixelsPerUnit = 16f;

        private void OnPreprocessTexture()
        {
            if (!assetPath.StartsWith(PixelArtRoot) || assetPath.StartsWith(VectorUiRoot))
            {
                return;
            }

            var textureImporter = (TextureImporter)assetImporter;
            if (!textureImporter.importSettingsMissing)
            {
                return;
            }

            textureImporter.textureType = TextureImporterType.Sprite;
            textureImporter.spriteImportMode = SpriteImportMode.Multiple;
            textureImporter.spritePixelsPerUnit = PixelsPerUnit;
            textureImporter.filterMode = FilterMode.Point;
            textureImporter.textureCompression = TextureImporterCompression.Uncompressed;
            textureImporter.mipmapEnabled = false;
            textureImporter.alphaIsTransparency = true;
            textureImporter.wrapMode = TextureWrapMode.Clamp;
        }
    }
}

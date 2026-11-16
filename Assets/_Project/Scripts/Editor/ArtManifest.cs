using System;

namespace TDCrown.EditorTools
{
    // Espelho do Assets/_Project/Art/art-manifest.json escrito por ArtSource/art_export.py.
    // Os nomes dos campos são os do JSON (JsonUtility exige igualdade).
    [Serializable]
    public class ArtManifest
    {
        public int version;
        public ArtSheet[] sheets;
    }

    [Serializable]
    public class ArtSheet
    {
        public string sheetPath;
        public string assetId;
        public string animation;
        public string category;
        public string controller;
        public int frameWidth;
        public int frameHeight;
        public float pivotX;
        public float pivotY;
        public int[] durationsMs;
        public bool loop;
        public int impactFrame;
        public int[] turretAnchorPx;
        // Velocidade no chão (tile/s) em que o ciclo de andar desenhado não desliza, com o Animator em 1x.
        public float groundSpeedTilesPerSecond;

        public bool HasClip => !string.IsNullOrEmpty(controller) && durationsMs != null && durationsMs.Length > 0;

        public string SpriteName(int frameIndex) => $"{assetId}_{animation}_{frameIndex}";

        public int WindupMs()
        {
            var windup = 0;
            for (var frameIndex = 0; frameIndex < impactFrame; frameIndex++)
            {
                windup += durationsMs[frameIndex];
            }
            return windup;
        }
    }
}

using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using UnityEditor;
using UnityEditor.Animations;
using UnityEditor.U2D.Sprites;
using UnityEngine;

namespace TDCrown.EditorTools
{
    // Lê o art-manifest.json, fatia os sheets, gera um clip por arquivo de animação e um override por asset.
    // Rodar de novo atualiza os assets existentes no lugar, mantendo GUIDs e ids dos sprites.
    public static class AnimationGenerator
    {
        private const string ManifestPath = "Assets/_Project/Art/art-manifest.json";
        private const string AnimationRoot = "Assets/_Project/Animation";
        private const string ControllersFolder = AnimationRoot + "/Controllers";
        private const string PlaceholdersFolder = ControllersFolder + "/Placeholders";
        private const string AttackTrigger = "Attack";
        private const string MovingParameter = "Moving";
        private const float PixelsPerUnit = 16f;
        private const float ClipFrameRate = 60f;

        private static readonly Dictionary<string, string[]> StatesByController = new Dictionary<string, string[]>
        {
            { "Unit", new[] { "Idle", "Walk", "Attack" } },
            { "TowerTurret", new[] { "Idle", "Attack" } },
            { "TowerBase", new[] { "Idle" } },
        };

        [MenuItem("TD Crown/Arte/Gerar animações")]
        public static void GenerateAll()
        {
            AssetDatabase.Refresh();
            var manifest = LoadManifest();
            if (manifest == null)
            {
                return;
            }

            var report = new StringBuilder();
            try
            {
                for (var sheetIndex = 0; sheetIndex < manifest.sheets.Length; sheetIndex++)
                {
                    var sheet = manifest.sheets[sheetIndex];
                    EditorUtility.DisplayProgressBar("TD Crown", $"Fatiando {sheet.sheetPath}", (float)sheetIndex / manifest.sheets.Length);
                    SliceSheet(sheet);
                }

                var baseControllers = StatesByController.Keys.ToDictionary(controllerName => controllerName, EnsureBaseController);

                foreach (var assetSheets in manifest.sheets.Where(sheet => sheet.HasClip).GroupBy(sheet => sheet.assetId))
                {
                    EditorUtility.DisplayProgressBar("TD Crown", $"Clips de {assetSheets.Key}", 1f);
                    var clipsByState = new Dictionary<string, AnimationClip>();
                    foreach (var sheet in assetSheets)
                    {
                        clipsByState[StateName(sheet.animation)] = BuildClip(sheet, report);
                    }

                    var controllerName = assetSheets.First().controller;
                    if (!baseControllers.TryGetValue(controllerName, out var baseController))
                    {
                        report.AppendLine($"ERRO {assetSheets.Key}: controller '{controllerName}' não existe");
                        continue;
                    }
                    BuildOverride(assetSheets.First(), baseController, clipsByState, report);
                }

                AssetDatabase.SaveAssets();
            }
            finally
            {
                EditorUtility.ClearProgressBar();
            }

            Debug.Log($"[TD Crown] Animações geradas a partir de {ManifestPath}\n{report}");
        }

        private static ArtManifest LoadManifest()
        {
            if (!File.Exists(ManifestPath))
            {
                Debug.LogError($"[TD Crown] {ManifestPath} não existe. Rode os scripts de ArtSource/ primeiro.");
                return null;
            }

            var manifest = JsonUtility.FromJson<ArtManifest>(File.ReadAllText(ManifestPath));
            if (manifest?.sheets == null || manifest.sheets.Length == 0)
            {
                Debug.LogError($"[TD Crown] {ManifestPath} está vazio.");
                return null;
            }
            return manifest;
        }

        private static void SliceSheet(ArtSheet sheet)
        {
            if (!(AssetImporter.GetAtPath(sheet.sheetPath) is TextureImporter textureImporter))
            {
                Debug.LogError($"[TD Crown] {sheet.sheetPath} não foi importado como textura.");
                return;
            }

            textureImporter.textureType = TextureImporterType.Sprite;
            textureImporter.spriteImportMode = SpriteImportMode.Multiple;
            textureImporter.spritePixelsPerUnit = PixelsPerUnit;
            textureImporter.filterMode = FilterMode.Point;
            textureImporter.textureCompression = TextureImporterCompression.Uncompressed;
            textureImporter.mipmapEnabled = false;
            textureImporter.alphaIsTransparency = true;
            textureImporter.GetSourceTextureWidthAndHeight(out var textureWidth, out var textureHeight);

            var dataProviderFactories = new SpriteDataProviderFactories();
            dataProviderFactories.Init();
            var dataProvider = dataProviderFactories.GetSpriteEditorDataProviderFromObject(textureImporter);
            if (dataProvider == null)
            {
                Debug.LogError($"[TD Crown] Sem provedor de sprites para {sheet.sheetPath}.");
                return;
            }
            dataProvider.InitSpriteEditorDataProvider();

            // Reaproveita o spriteID de cada nome para os clips existentes continuarem apontando para o mesmo sprite.
            var existingIdsByName = dataProvider.GetSpriteRects()
                .GroupBy(spriteRect => spriteRect.name)
                .ToDictionary(group => group.Key, group => group.First().spriteID);

            var columns = textureWidth / sheet.frameWidth;
            var rows = textureHeight / sheet.frameHeight;
            var spriteRects = new List<SpriteRect>();
            for (var row = 0; row < rows; row++)
            {
                for (var column = 0; column < columns; column++)
                {
                    var frameIndex = row * columns + column;
                    var spriteName = sheet.SpriteName(frameIndex);
                    var spriteRect = new SpriteRect
                    {
                        name = spriteName,
                        // A textura tem a origem embaixo; a linha 0 do sheet é a de cima.
                        rect = new Rect(column * sheet.frameWidth, textureHeight - (row + 1) * sheet.frameHeight,
                            sheet.frameWidth, sheet.frameHeight),
                        alignment = SpriteAlignment.Custom,
                        pivot = new Vector2(sheet.pivotX, sheet.pivotY),
                        spriteID = existingIdsByName.TryGetValue(spriteName, out var existingId) ? existingId : GUID.Generate(),
                    };
                    spriteRects.Add(spriteRect);
                }
            }

            dataProvider.SetSpriteRects(spriteRects.ToArray());
            var nameFileIdProvider = dataProvider.GetDataProvider<ISpriteNameFileIdDataProvider>();
            nameFileIdProvider?.SetNameFileIdPairs(spriteRects.Select(spriteRect => new SpriteNameFileIdPair(spriteRect.name, spriteRect.spriteID)).ToList());
            dataProvider.Apply();
            textureImporter.SaveAndReimport();
        }

        private static AnimationClip BuildClip(ArtSheet sheet, StringBuilder report)
        {
            var sprites = AssetDatabase.LoadAllAssetsAtPath(sheet.sheetPath)
                .OfType<Sprite>()
                .ToDictionary(sprite => sprite.name);

            var keyframes = new List<ObjectReferenceKeyframe>();
            var time = 0f;
            for (var frameIndex = 0; frameIndex < sheet.durationsMs.Length; frameIndex++)
            {
                if (!sprites.TryGetValue(sheet.SpriteName(frameIndex), out var sprite))
                {
                    report.AppendLine($"ERRO {sheet.sheetPath}: falta o sprite {sheet.SpriteName(frameIndex)}");
                    return null;
                }
                keyframes.Add(new ObjectReferenceKeyframe { time = time, value = sprite });
                time += sheet.durationsMs[frameIndex] / 1000f;
            }
            // Chave repetida no fim: sem ela o último frame dura zero.
            keyframes.Add(new ObjectReferenceKeyframe { time = time, value = keyframes[keyframes.Count - 1].value });

            var clipFolder = $"{AnimationRoot}/{sheet.category}/{sheet.assetId}";
            EnsureFolder(clipFolder);
            var clipPath = $"{clipFolder}/{sheet.assetId}_{sheet.animation}.anim";
            var clip = AssetDatabase.LoadAssetAtPath<AnimationClip>(clipPath);
            if (clip == null)
            {
                clip = new AnimationClip();
                AssetDatabase.CreateAsset(clip, clipPath);
            }

            foreach (var existingBinding in AnimationUtility.GetObjectReferenceCurveBindings(clip))
            {
                AnimationUtility.SetObjectReferenceCurve(clip, existingBinding, null);
            }
            clip.ClearCurves();
            clip.frameRate = ClipFrameRate;
            var spriteBinding = EditorCurveBinding.PPtrCurve("", typeof(SpriteRenderer), "m_Sprite");
            AnimationUtility.SetObjectReferenceCurve(clip, spriteBinding, keyframes.ToArray());

            var clipSettings = AnimationUtility.GetAnimationClipSettings(clip);
            clipSettings.loopTime = sheet.loop;
            AnimationUtility.SetAnimationClipSettings(clip, clipSettings);
            EditorUtility.SetDirty(clip);

            report.Append($"{clipPath}: {sheet.durationsMs.Length} frames, {Mathf.RoundToInt(time * 1000)} ms");
            if (sheet.impactFrame >= 0)
            {
                report.Append($", attackWindup = {sheet.WindupMs()} ms (frame de impacto {sheet.impactFrame})");
            }
            if (sheet.groundSpeedTilesPerSecond > 0f)
            {
                report.Append($", andar sem deslizar a {sheet.groundSpeedTilesPerSecond:0.##} tile/s");
            }
            if (sheet.turretAnchorPx != null && sheet.turretAnchorPx.Length == 2)
            {
                report.Append($", âncora da besta = ({sheet.turretAnchorPx[0]}, {sheet.turretAnchorPx[1]}) px");
            }
            report.AppendLine();
            return clip;
        }

        private static void BuildOverride(ArtSheet firstSheet, AnimatorController baseController,
            Dictionary<string, AnimationClip> clipsByState, StringBuilder report)
        {
            var overridePath = $"{AnimationRoot}/{firstSheet.category}/{firstSheet.assetId}/{firstSheet.assetId}.overrideController";
            var overrideController = AssetDatabase.LoadAssetAtPath<AnimatorOverrideController>(overridePath);
            if (overrideController == null)
            {
                overrideController = new AnimatorOverrideController(baseController);
                AssetDatabase.CreateAsset(overrideController, overridePath);
            }
            overrideController.runtimeAnimatorController = baseController;

            var overrides = new List<KeyValuePair<AnimationClip, AnimationClip>>();
            overrideController.GetOverrides(overrides);
            var updatedOverrides = new List<KeyValuePair<AnimationClip, AnimationClip>>();
            foreach (var placeholderAndClip in overrides)
            {
                var placeholder = placeholderAndClip.Key;
                var stateName = placeholder.name.Substring(placeholder.name.LastIndexOf('_') + 1);
                clipsByState.TryGetValue(stateName, out var clip);
                if (clip == null && stateName == "Walk" && clipsByState.TryGetValue("Idle", out var idleClip))
                {
                    // Todo inimigo e minion precisa de walk; o idle só tampa o buraco até o sheet chegar.
                    report.AppendLine($"AVISO {firstSheet.assetId}: falta o sheet de walk; usando o idle no estado Walk");
                    clip = idleClip;
                }
                if (clip == null)
                {
                    report.AppendLine($"AVISO {firstSheet.assetId}: sem clip para o estado {stateName}");
                }
                updatedOverrides.Add(new KeyValuePair<AnimationClip, AnimationClip>(placeholder, clip));
            }
            overrideController.ApplyOverrides(updatedOverrides);
            EditorUtility.SetDirty(overrideController);
        }

        private static AnimatorController EnsureBaseController(string controllerName)
        {
            EnsureFolder(PlaceholdersFolder);
            var controllerPath = $"{ControllersFolder}/{controllerName}.controller";
            var controller = AssetDatabase.LoadAssetAtPath<AnimatorController>(controllerPath);
            if (controller == null)
            {
                controller = AnimatorController.CreateAnimatorControllerAtPath(controllerPath);
            }

            // Um controller que já existe ganha só os estados que faltam, no lugar: os overrides e as
            // views que apontam para ele continuam valendo.
            var stateMachine = controller.layers[0].stateMachine;
            var statesByName = stateMachine.states.ToDictionary(childState => childState.state.name, childState => childState.state);
            var addedStates = new List<string>();
            foreach (var stateName in StatesByController[controllerName])
            {
                if (statesByName.ContainsKey(stateName))
                {
                    continue;
                }
                var state = stateMachine.AddState(stateName);
                state.motion = EnsurePlaceholder(controllerName, stateName);
                statesByName[stateName] = state;
                addedStates.Add(stateName);
            }
            stateMachine.defaultState = statesByName["Idle"];

            if (addedStates.Contains("Attack"))
            {
                ConnectAttack(controller, statesByName);
            }
            if (addedStates.Contains("Walk"))
            {
                ConnectWalk(controller, statesByName);
            }

            EditorUtility.SetDirty(controller);
            return controller;
        }

        private static AnimationClip EnsurePlaceholder(string controllerName, string stateName)
        {
            var placeholderPath = $"{PlaceholdersFolder}/{controllerName}_{stateName}.anim";
            var placeholder = AssetDatabase.LoadAssetAtPath<AnimationClip>(placeholderPath);
            if (placeholder == null)
            {
                placeholder = new AnimationClip();
                AssetDatabase.CreateAsset(placeholder, placeholderPath);
            }
            return placeholder;
        }

        private static void ConnectAttack(AnimatorController controller, Dictionary<string, AnimatorState> statesByName)
        {
            EnsureParameter(controller, AttackTrigger, AnimatorControllerParameterType.Trigger);
            var idleState = statesByName["Idle"];
            var attackState = statesByName["Attack"];

            var startAttack = idleState.AddTransition(attackState);
            startAttack.AddCondition(AnimatorConditionMode.If, 0f, AttackTrigger);
            ConfigureInstantTransition(startAttack, hasExitTime: false);

            // Um ataque novo antes do clip acabar recomeça o golpe em vez de esperar.
            var restartAttack = attackState.AddTransition(attackState);
            restartAttack.AddCondition(AnimatorConditionMode.If, 0f, AttackTrigger);
            ConfigureInstantTransition(restartAttack, hasExitTime: false);

            // Volta sempre pelo Idle: se a unidade ainda estiver andando, o Idle passa para o Walk no mesmo quadro.
            var backToIdle = attackState.AddTransition(idleState);
            ConfigureInstantTransition(backToIdle, hasExitTime: true);
        }

        private static void ConnectWalk(AnimatorController controller, Dictionary<string, AnimatorState> statesByName)
        {
            EnsureParameter(controller, MovingParameter, AnimatorControllerParameterType.Bool);
            var idleState = statesByName["Idle"];
            var walkState = statesByName["Walk"];

            var startWalking = idleState.AddTransition(walkState);
            startWalking.AddCondition(AnimatorConditionMode.If, 0f, MovingParameter);
            ConfigureInstantTransition(startWalking, hasExitTime: false);

            var stopWalking = walkState.AddTransition(idleState);
            stopWalking.AddCondition(AnimatorConditionMode.IfNot, 0f, MovingParameter);
            ConfigureInstantTransition(stopWalking, hasExitTime: false);

            if (statesByName.TryGetValue("Attack", out var attackState))
            {
                var attackWhileWalking = walkState.AddTransition(attackState);
                attackWhileWalking.AddCondition(AnimatorConditionMode.If, 0f, AttackTrigger);
                ConfigureInstantTransition(attackWhileWalking, hasExitTime: false);
            }
        }

        private static void EnsureParameter(AnimatorController controller, string parameterName, AnimatorControllerParameterType parameterType)
        {
            if (controller.parameters.All(parameter => parameter.name != parameterName))
            {
                controller.AddParameter(parameterName, parameterType);
            }
        }

        private static void ConfigureInstantTransition(AnimatorStateTransition transition, bool hasExitTime)
        {
            transition.hasExitTime = hasExitTime;
            transition.exitTime = 1f;
            transition.hasFixedDuration = true;
            transition.duration = 0f;
        }

        private static string StateName(string animation) =>
            char.ToUpperInvariant(animation[0]) + animation.Substring(1);

        private static void EnsureFolder(string folderPath)
        {
            if (AssetDatabase.IsValidFolder(folderPath))
            {
                return;
            }
            var parentFolder = Path.GetDirectoryName(folderPath).Replace('\\', '/');
            EnsureFolder(parentFolder);
            AssetDatabase.CreateFolder(parentFolder, Path.GetFileName(folderPath));
        }
    }
}

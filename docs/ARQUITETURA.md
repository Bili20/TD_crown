# TD Crown na Unity: arquitetura

## Decisões principais

| Decisão | Escolha | Por quê |
|---|---|---|
| Versão e plataforma | Unity 6 (LTS), **Windows x64** | Lançamento na Steam |
| Backend de script | Mono | Build rápida, jogo leve |
| Render | URP com Renderer 2D (template Universal 2D) + **Pixel Perfect Camera** | Pixel art nítido em escala inteira |
| Combate | **Simulação própria em C# puro** (`TDCrown.Core`), sem física da Unity | Regras exatas do GDD (faixas de defesa, ordem de resolução, status), testes EditMode e ferramenta de balanceamento sem tela |
| Passo e velocidade | Passo fixo de **1/60 s** com acumulador sobre o `Time.deltaTime`, no máximo 8 passos por quadro. 1x/2x e pausa pelo `Time.timeScale` | Mesmo resultado em qualquer taxa de quadros; Animator e partículas seguem a velocidade sozinhos; a UI usa tempo sem escala |
| Caminhos | Polilinhas de waypoints feitas na cena da fase e gravadas no `LevelDefinition` | Pontos fixos e rotas fixas: NavMesh e pathfinding não são necessários |
| Dados | ScriptableObjects para config, torres, inimigos, fases, itens, poderes e árvore | Ajuste no Inspector sem mexer no código |
| UI | UI Toolkit (UXML/USS) | Decidido no GDD; menu radial e tooltips ancorados no mundo |
| Entrada | Input System | Mouse + atalhos remapeáveis |
| Animação de sprite | **Animator da Unity** com Override Controllers | Decidido em 14/11. Um controller base por categoria e um override por asset; um clip por arquivo de animação da Art Bible, gerado por ferramenta. Andar desenhado (`walk`) em todo inimigo e minion; o andar procedural foi abolido em 16/11. Morte continua procedural |
| Recolor | Shader HLSL próprio com textura de paleta | Torres e unidades do jogador em cinza indexado (Art Bible §4.1) |
| Áudio | Audio Mixer da Unity no começo | FMOD só se entrar um sonoplasta (decisão no PLANO) |
| Localização | `com.unity.localization`, pt-BR de origem | Texto nunca no código |
| Salvamento | JSON em `Application.persistentDataPath` | Fácil de inspecionar e apagar |

## Tela, câmera e escala

- **1 tile = 16 px = 1 unidade de mundo** (PPU 16). A simulação usa as mesmas unidades do mundo, em tiles; não há conversão.
- Pixel Perfect Camera com resolução de referência **640×360**, escala inteira (×3 em 1080p, ×4 em 1440p). Upscale Render Texture ligado, para o shader de recolor e os efeitos ficarem na grade de pixel.
- Padrão: 1920×1080 em Fullscreen Window, janela redimensionável. `vSyncCount = 1`; sem V-Sync, `targetFrameRate` = 144.
- Ao perder o foco, pausa a fase (opção, ligada por padrão).
- **Velocidade:** 1x/2x e pausa mudam o `Time.timeScale`. O `LevelSim` acumula o `Time.deltaTime` (escalado), então Animator, partículas e simulação andam juntos; a UI anima com tempo sem escala.
- **Ordem de desenho:** Transparency Sort Mode = Custom Axis `(0, 1, 0)`. Torres, inimigos e soldados têm **Sorting Group** na raiz, posicionada no ponto do chão.
- **Camadas de sorting**, de trás para frente:
  1. `Ground`: tilemap.
  2. `GroundFx`: poças, zonas consagradas, linhas do bastião, alcance.
  3. `World`: torres, inimigos de chão e soldados, ordenados pelo eixo.
  4. `Air`: voadores e projéteis.
  5. `Overlay`: barras de vida, ícones de status, números.
- A UI Toolkit desenha por cima de tudo, em resolução nativa (não na 640×360).

## Pastas

```
Assets/_Project/
  Art/                    sprites (Art Bible): Enemies/ PlayerUnits/ Towers/ Projectiles/ Tiles/ VFX/; UI/ é vetor
  Animation/              Controllers/ (Unit, TowerTurret, TowerBase); por asset, os clips gerados
                          ({asset_id}_{animação}.anim) e o override ({asset_id}.overrideController)
  Audio/Music/ Audio/SFX/
  Data/                   ScriptableObjects: CombatConfig.asset, GameDatabase.asset,
                          Towers/ Enemies/ Levels/ Items/ Powers/ CrownTree/ Palettes/ Animations/
  Localization/           LocalizationSettings e tabelas (geradas de localization/*.csv)
  Materials/              M_SpriteRecolor e materiais de efeito
  Prefabs/                Towers/ Enemies/ Units/ Projectiles/ UI/
  Scenes/                 Boot.unity, Game.unity; Levels/ (uma cena por fase: r1_f01.unity ...); Debug/
  Scripts/                TDCrown.asmdef (assembly do jogo)
    Core/                 TDCrown.Core.asmdef: simulação em C# puro (sem UnityEngine)
      Simulation/         LevelSim, FixedStepper, eventos
      Combat/             DamageResolver, StatusSet, StatSheet (pipeline), Hit
      Towers/             TowerState e um comportamento por torre (BallistaBehaviour, ...)
      Units/              SoldierState, bloqueio, rally point, Veterania
      Enemies/            EnemyState, movimento no caminho, habilidades de boss
      Bastions/           BastionMap e aplicação dos Doms
      Waves/              WaveRunner, chamada antecipada
      Economy/            ouro, vidas, Fé
      Powers/ Items/      efeitos dos poderes e dos itens mecânicos
      Balance/            BalanceRunner (fase sem tela com uma build roteirizada)
    Game/                 definições (ScriptableObjects) e conversão para os settings do Core,
                          progresso, Selos e árvore, save, opções, entrada, Loc
    Presentation/         MonoBehaviours que desenham o estado: views, SpriteAnimator, recolor
    Audio/                AudioDirector (eventos → sons)
    App/                  LevelController: raiz de composição da fase
    UI/                   telas (UI Toolkit) e o HUD
    Editor/               TDCrown.Editor.asmdef: importers, LevelAuthoring, BalanceTool, WindowsBuild
  Shaders/                SpriteRecolor.shader e efeitos
  Tests/EditMode/         TDCrown.Tests.EditMode.asmdef
  UI/                     UXML/ USS/ Fonts/, PanelSettings e tema
ArtSource/                scripts Python que geram os sprites (fora de Assets)
docs/                     GDD, ARQUITETURA, PLANO, ART_BIBLE
localization/             CSVs com os textos (fonte das tabelas)
```

### Assemblies

- **`TDCrown.Core`** (`Scripts/Core`): toda a regra de combate.
  - Tem `noEngineReferences`: o compilador recusa `using UnityEngine` ali.
  - Não referencia nada.
- **`TDCrown`** (`Scripts/` menos `Core` e `Editor`): o jogo.
  - Referencia `TDCrown.Core`, Input System, Localization e URP 2D.
- **`TDCrown.Editor`** (`Scripts/Editor`): ferramentas, só no Editor.
  - Referencia `TDCrown` e `TDCrown.Core`.
- **`TDCrown.Tests.EditMode`** (`Tests/EditMode`): testes NUnit.
  - Referencia `TDCrown` e `TDCrown.Core`.

### Namespaces e dependências

Namespaces: `TDCrown.Core`, `TDCrown.Game`, `TDCrown.Presentation`, `TDCrown.Audio`, `TDCrown.App`, `TDCrown.UI`, `TDCrown.EditorTools`.

As dependências vão num sentido só: **Core ← Game ← Presentation / Audio ← App ← UI**. O `Game` não conhece views, sons nem telas. Presentation e Audio não se conhecem; o `LevelController` liga cada um à simulação.

## Onde fica cada parte

| Parte do jogo | Unity |
|---|---|
| Regras e números gerais | `CombatConfig` (ScriptableObject) com um `CombatSettings` (C# puro): faixas de defesa, teto de lentidão, imunidade a controle, `waveTimer`, `earlyCallGoldFactor`, `maxBonusGoldPerKill`, venda 60%, `specializationCostFactor` |
| Torres | `TowerDefinition`: id, 3 níveis (custo, dano, cadência, alcance, `attackWindup` e os campos próprios da torre), Dom, especializações, visual por nível (override controller da base e da besta/operador, offset da cintura) |
| Matriz do Dom | `DomMatrix` (ScriptableObject): efeito de cada Dom em cada torre, com "sem efeito" explícito; o hover lê dela |
| Inimigos | `EnemyDefinition`: id, vida, velocidade, defesas, peso, voador, ouro, vidas que tira, habilidade, clips |
| Fases | `LevelDefinition`: id (`r1_f01`), cena, caminhos, pontos de construção e bastiões, ouro inicial, vidas, ondas, item da 1ª vitória, par da Provação, falas da Conselheira |
| Ondas | lista de `WaveDefinition` dentro do `LevelDefinition`: grupos com inimigo, quantidade, espaçamento, atraso e caminho |
| Montagem da fase | cena `Levels/r1_f01.unity` com Tilemap e `LevelAuthoring` (gizmos dos caminhos e dos pontos). **TD Crown → Gravar fase** copia caminhos e pontos para o `LevelDefinition` |
| Itens, poderes e árvore | `ItemDefinition`, `PowerDefinition`, `CrownTreeDefinition` (nós, custo, requisitos, modificadores). Item ou poder mecânico referencia um comportamento do Core por id |
| Estado da fase | `LevelSim` (C# puro): torres, soldados, inimigos, projéteis, zonas, ouro, vidas, ondas, poderes |
| Movimento no caminho | o inimigo guarda o caminho e a distância percorrida; a posição sai da polilinha. "Primeiro" = mais distância percorrida. Inimigo engajado por soldado para de avançar |
| Mira das torres | prioridade por torre (primeiro, maior vida, voador, mais rápido); alcance = círculo em tiles |
| Projéteis | simulados: o virote anda em linha e acerta cada inimigo uma vez; o frasco tem tempo de voo e acerta em área no impacto |
| Dano | `DamageResolver.Resolve`, na ordem da seção 4.3 do GDD |
| Status | `StatusSet` por inimigo, com as regras de acúmulo da seção 4.7 |
| Stats | `StatSheet`: camadas base → árvore → item → Dom → buff, `(valor + fixos) × (1 + %)` |
| Bastiões | `BastionMap`: recalcula os Doms ao construir, vender ou especializar e publica `DomsChanged` |
| Do jogo para a fase | `LevelSetup` (C# puro): fase, modo, nós da árvore, itens e poderes escolhidos. O `Game` monta a partir do save e da Preparação |
| Progresso | `Game/Progression`: estrelas e Selos por fase e modo, nós comprados, itens ganhos, loadout, regiões liberadas |
| Salvamento | `SaveData` + `SaveSystem`: `save.json` com `version` e migração; JSON quebrado começa de novo |
| Animações | Controllers base em `Animation/Controllers`; por asset, clips e override gerados por **TD Crown → Arte → Gerar animações** a partir do `art-manifest.json` |
| Telas | `GameFlow` (UI): título, mapa-múndi, Preparação, fase (HUD), pausa, vitória/derrota, Árvore da Coroa, bestiário, opções |
| Raiz da fase | `LevelController` (App): carrega a cena da fase por cima da `Game.unity`, cria o `LevelSim`, liga views, áudio, HUD e entrada |

## A simulação conversa por eventos

O `LevelSim` não conhece sprites, sons nem UI. Ele emite eventos e o resto reage:

```csharp
public delegate void EnemyKilledHandler(EnemyState enemy, TowerState creditedTower, int gold);
public delegate void HitHandler(in HitResult hit);
public delegate void TowerAttackHandler(TowerState tower, EnemyState target);

public event Action<EnemyState> EnemySpawned;
public event EnemyKilledHandler EnemyKilled;
public event Action<EnemyState, int> EnemyLeaked;        // vidas tiradas
public event HitHandler Hit;
public event TowerAttackHandler TowerAttackStarted;     // a view dispara o trigger Attack do Animator
public event TowerAttackHandler TowerAttackReleased;    // fim do attackWindup: sai o projétil ou o golpe acerta
public event Action<ZoneState> ZoneCreated, ZoneExpired;
public event Action<BastionState> DomsChanged;
public event Action<int> WaveStarted, GoldChanged, LivesChanged;
public event Action<TowerState> SmiteFired;
public event Action<EnemyState, string> BossTelegraph;   // ~1,5 s antes da habilidade
public event Action<LevelResult> LevelEnded;
```

- **Delegates nomeados:** evento novo com números ou com mais de uma entidade ganha um delegate com os parâmetros nomeados, em vez de `Action<float, float, ...>`.
- **Sem cancelar assinatura:** o `LevelSim` é recriado a cada tentativa. Quem assina não cancela; cada `Bind` só zera o próprio estado.
- **Ganho:** isso deixa a simulação testável em EditMode e roda a ferramenta de balanceamento sem tela.

## Visual

- **Torre:** a raiz tem Sorting Group e fica no ponto de construção.
  - **Base:** SpriteRenderer, não espelha.
  - **Besta com operador:** SpriteRenderer filho na altura da cintura (`waist_row` da Art Bible). Vira com flipX conforme o lado do alvo.
  - O `TowerView` troca os sprites e os clips quando o nível muda.
- **Recolor** (`Shaders/SpriteRecolor.shader`, material `M_SpriteRecolor`):
  - **Textura de paleta:** `_PaletteTex`, 8×N, filtro Point, uma linha por preset (`real`, `rubi`, `floresta`, `daltonismo`, patentes da Veterania).
  - **Cor de vértice do SpriteRenderer:** `r` = linha da paleta (`linha / (N − 1)`), `g` = intensidade do hit flash, `a` = alfa. Assim os sprites continuam no mesmo batch.
  - **Pixel recolorido:** só o de cinza neutro (`max − min ≤ 2/255`). O índice é `round(cinza × 7)`, calculado no valor **sRGB**: em espaço Linear, converta com `LinearToSRGB` antes.
  - **Pixel com tom:** pele, madeira, pedra, ferro e os materiais das torres passam direto.
  - **`TeamPalette`:** componente que escreve a cor de vértice.
- **Animação (Animator da Unity):**
  - **Controllers base**, um por categoria, em `Animation/Controllers`:
    - `Unit` (soldados e inimigos): `Idle` padrão; `Walk` enquanto o bool `Moving` estiver ligado; `Attack` pelo trigger `Attack`, a partir do `Idle` ou do `Walk`, e volta ao `Idle` no fim do clip (se ainda estiver andando, o `Idle` passa para o `Walk` no mesmo quadro); `Hit`, `Death`, `Special` e `Spawn` só quando o asset tiver o clip.
    - Todo asset do controller `Unit` precisa de `walk`. Se faltar, o gerador avisa no relatório e põe o clip de `idle` no estado `Walk`, só para nada quebrar até o sheet chegar.
    - O gerador completa controllers que já existem: estados, parâmetros e transições que faltam entram no lugar, sem trocar o GUID.
    - `TowerTurret`: `Idle` e `Attack`.
    - `TowerBase`: só `Idle` (flâmula, fumaça, sino).
  - **Por asset:** um `AnimatorOverrideController` (`{asset_id}.overrideController`) troca os clips do controller base. Subir o nível da torre troca o `runtimeAnimatorController` pelo override do nível novo.
  - **Clips:** um `.anim` por arquivo de animação da Art Bible (`{asset_id}_{animação}.png` → `{asset_id}_{animação}.anim`).
    - Animam **só** `SpriteRenderer.sprite`: nada de transform (é da view, que só posiciona a unidade no caminho) nem de cor (é do recolor).
    - Sample rate 60, com a duração de cada frame vinda da arte, não um fps fixo.
  - **Gerador:** **TD Crown → Arte → Gerar animações** lê o `Assets/_Project/Art/art-manifest.json`, que os scripts de `ArtSource/` escrevem. Para cada sheet, o manifesto tem tamanho do frame, pivô, durações em ms, loop e frame de impacto.
    - Fatia o PNG (Grid By Cell Size, pivô Bottom Center).
    - Cria ou atualiza os clips e o override.
    - Atualizar mantém o GUID, então prefabs e cenas não perdem a referência.
  - **Sincronia com a simulação:** o `attackWindup` de cada torre, nível e inimigo é a soma das durações antes do frame de impacto. O gerador confere o valor contra o manifesto e avisa se divergir.
    - A simulação emite `TowerAttackStarted`; a view dispara o trigger.
    - Depois do windup, a simulação emite `TowerAttackReleased` e só então o projétil sai ou o golpe acerta.
  - **Velocidade do `walk`:** o manifesto traz `groundSpeedTilesPerSecond` (a velocidade em que os pés do ciclo não deslizam). Ela vai para `EnemyDefinition.walkCycleSpeed` (e o equivalente das unidades do jogador); o gerador mostra o valor no relatório. A view liga `Moving` enquanto a simulação move a unidade e, no `Walk`, põe `animator.speed = velocidade atual ÷ walkCycleSpeed` (1 nos outros estados). Lentidão e atordoamento aparecem sozinhos (atordoado = velocidade 0 = `Moving` desligado).
  - **Fase aleatória:** ao nascer, a view começa o estado num ponto aleatório do clip (`animator.Play(estado, 0, Random.value)`), para o enxame não andar em sincronia.
  - **Culling:** inimigos usam `Animator.cullingMode = CullUpdateTransforms`.
- **Morte procedural:** flash, queda e fade.
- **Sombra:** um SpriteRenderer separado, parado no chão (não acompanha o balanço dos frames).
- **Interpolação:** a view desenha entre o passo anterior e o atual.

## UI Toolkit

- Um `UIDocument` na `Game.unity` carrega `UI/UXML/Main.uxml`, com uma UXML por tela. O `GameFlow` mostra uma tela por vez, mais uma sobreposta (pausa, opções).
- **PanelSettings:** 1920×1080, Scale With Screen Size, Expand.
- **Peças de UI em vetor:** exportadas em 2x, com slices em px da textura e `-unity-slice-scale: 0.5px`.
- **Menu radial, tooltips do mundo e botão de chamar onda:** posicionados com `RuntimePanelUtils.CameraTransformWorldToPanel` a cada quadro em que estão abertos.
- **Barras de vida e ícones de status:** são sprites no mundo (camada `Overlay`), não UI. Há dezenas se movendo e elas precisam da ordem por Y.
- **Textos fixos:** ligados às tabelas no UXML (`LocalizedString`).
- **Textos com valores:** escritos pelo código com `Loc.Get` no `Refresh()` da tela.

## Testes e ferramenta de balanceamento

1. **EditMode** (`Tests/EditMode`), contra as tabelas do GDD:
   - ordem de resolução e faixas de defesa;
   - penetração;
   - acúmulo de status e imunidade a controle;
   - pipeline de stats;
   - matriz do Dom (incluindo Dom do próprio tipo e torres gêmeas);
   - ouro por abate com teto;
   - Selos por nota.
2. **Ferramenta de balanceamento** (menu **TD Crown → Balanceamento**, `Editor/BalanceTool.cs` sobre `Core/Balance/BalanceRunner.cs`):
   - **Entrada:** roda uma fase sem tela com uma **build roteirizada**, uma lista de ações por tempo (construir, upgrade, chamar onda).
   - **Saída:** vidas no fim, ouro, duração, vazamentos por inimigo e dano por torre.
   - **Alvos:** marca com `*` o que sai dos alvos da seção 11 do GDD.
3. **Regra:** número de combate só muda depois de passar pela ferramenta.

## Build

`Scripts/Editor/WindowsBuild.cs` cria o menu **TD Crown → Build Windows**:

- Aplica as configurações (nome do produto, 1920×1080, Fullscreen Window, janela redimensionável, Mono).
- Gera `Builds/Windows/TDCrown.exe` com as cenas da Scene List.

A demo pública vira uma variante: símbolo `TDCROWN_DEMO` e um `GameDatabase_Demo` só com as fases 1–3.

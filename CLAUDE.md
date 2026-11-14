# TD Crown (Unity)

Tower defense de campanha em pixel art 2D top-down 3/4 para **Windows**, na Steam: primeiro uma demo pública (fases 1–3), depois a 1.0 com 28 fases (ver `docs/PLANO.md`, Lançamentos). Estúdio: Not Founder Studio.

## Onde está a verdade

- `docs/GDD.md`: regras e todos os números. Ao mudar uma regra ou um número no jogo, atualize o GDD junto. O Notion ([🗼 TD](https://app.notion.com/p/TD-414ae533febb802f9441d8f3cc6e0717)) é o caderno de ideias; o que vale é o GDD.md.
- `docs/ARQUITETURA.md`: decisões técnicas, pastas, assemblies e onde fica cada parte do jogo.
- `docs/PLANO.md`: fases, checklists, o que entra na demo e na 1.0, decisões em aberto e riscos.
- `docs/ART_BIBLE.md` + `docs/art-style.json`: estilo, paletas, tamanhos, animações, materiais das torres e entrega dos sprites. As skills de arte leem o JSON.

## Regras do projeto

1. **Simulação de combate em C# puro**, em `Assets/_Project/Scripts/Core` (assembly `TDCrown.Core`, sem referência à Unity). Não usar Rigidbody2D, Physics2D nem NavMesh para torres, inimigos e projéteis.
2. **Passo fixo de 1/60 s** com acumulador e no máximo 8 passos por quadro; a velocidade 2x roda o dobro de passos. O visual interpola.
3. **Unidades:** 1 tile = 16 px = 1 unidade de mundo (PPU 16). A simulação usa tiles, sem conversão.
4. **Números ficam em ScriptableObjects** (`CombatConfig`, `TowerDefinition`, `EnemyDefinition`, `LevelDefinition`, ...), nunca espalhados no código.
5. **A simulação emite eventos**; views, sons e UI assinam. A simulação não referencia nada visual.
6. **A ordem de resolução de dano é a da seção 4.3 do GDD**, num lugar só (`DamageResolver`). Todo número de torre passa pelo pipeline de stats (base → árvore → item → Dom → buff).
7. **Não mudar número de combate sem rodar a ferramenta de balanceamento** e comparar com a seção 11 do GDD.
8. **Arte:**
   - Segue a Art Bible.
   - Sprites são gerados pelos scripts de `ArtSource/` e exportados para `Assets/_Project/Art`; nunca editar o PNG à mão.
   - Um arquivo por animação: `{asset_id}_{animação}.png`.
   - Assets do jogador usam só os 8 cinzas de índice e as rampas fixas permitidas.
   - O import (PPU 16, Point, sem compressão) é feito pelo `PixelArtImportPostprocessor`.
9. **Assemblies:**
   - `TDCrown.Core` (`Scripts/Core`, `noEngineReferences`): combate.
   - `TDCrown` (o resto de `Scripts/`): o jogo.
   - `TDCrown.Editor` (`Scripts/Editor`): ferramentas.
   - `TDCrown.Tests.EditMode` (`Tests/EditMode`): testes.
   - Pacote novo usado no código entra nas referências do `.asmdef`.
10. **UI em UI Toolkit:**
    - Peças vetoriais em 2x com 9-slice.
    - Barras de vida e ícones de status são sprites no mundo, não UI.
    - Menu radial e tooltips do mundo usam `RuntimePanelUtils.CameraTransformWorldToPanel`.
11. **Texto visível ao jogador só por chave de tabela** (`Loc.Get`, `LocalizedString` ou binding da UI), nunca escrito no código ou no UXML. Textos novos entram nos CSVs de `localization/`.

## Convenções

- Unity 6, URP com Renderer 2D, Pixel Perfect Camera, Input System, UI Toolkit, Localization. Windows x64, Mono.
- Namespaces `TDCrown.Core`, `TDCrown.Game`, `TDCrown.Presentation`, `TDCrown.Audio`, `TDCrown.App`, `TDCrown.UI`, `TDCrown.EditorTools`. Dependências num sentido só: Core ← Game ← Presentation / Audio ← App ← UI.
- Propriedades e métodos públicos em PascalCase; campos (públicos, serializados ou não) em camelCase, como na Unity.
- Código e identificadores em inglês. Comentários em português. Textos do jogo nas tabelas, com o português como origem.
- **Nomes descritivos** para variáveis, parâmetros e lambdas: `enemy`, `tower`, `distanceAlongPath`, `tower => tower.id`.
  - Uma letra só em índices de laço curto (`i`, `j`), coordenadas (`x`, `y`) e `dt`.
  - Sem abreviações que pedem decifração.
- **Comentários só para o porquê:** uma restrição que o código não mostra ou uma escolha que não é a óbvia. Nada de repetir o nome, um número que está no asset ou a história da mudança (isso vai no commit).
- **Ids fixos** (aparecem no save, nas chaves de localização e nos nomes dos sprites):
  - torres: `balista`, `forja`, `campanario`, `alquimista`, `relicario`, `falcoaria`;
  - inimigos: `diabrete`, `cao_infernal`, `brutamontes`, `ninhada`, `gargula`, `cultista`, `xama`, `carrasco`, `senhor_da_brasa`;
  - poderes: `luz_da_coroa`, `estandarte_real`, `decreto_real`, `juramento_antigo`;
  - fases: `r1_f01` … `r4_f07`.

## Como verificar

- **Testes EditMode** em `Assets/_Project/Tests/EditMode`, contra as tabelas do GDD: faixas de defesa, penetração, ordem de resolução, status, pipeline de stats, matriz do Dom, ouro e Selos.
- **Ferramenta de balanceamento** (**TD Crown → Balanceamento**): roda a fase sem tela com uma build roteirizada e compara com os alvos do GDD.
- **Build Windows** (**TD Crown → Build Windows**) e teste do `.exe` fora do Editor ao fim de cada fase do plano.
- **Sprites:** `python ArtSource/validate_sprite.py <png> --style docs/art-style.json --palette <paleta> --size-class <classe>` antes de exportar.

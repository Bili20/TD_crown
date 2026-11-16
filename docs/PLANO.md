# TD Crown: plano do jogo na Unity (Windows), demo e 1.0 na Steam

## Resumo

Regras e números no [GDD](GDD.md); decisões técnicas na [ARQUITETURA](ARQUITETURA.md); estilo e entrega dos sprites na [Art Bible](ART_BIBLE.md).

O alvo é um **jogo para Windows** (64 bits) na Steam. Primeiro sai a demo pública, depois a 1.0. A arte é gerada por código (`ArtSource/`) a partir da Art Bible. Já estão prontos o soldado da Forja nv2, o Diabrete e a Balista nv1–nv3.

Estimativa **até a demo interna** (região 1 completa): **130 a 210 horas**.

- A 10 h por semana: 13 a 21 semanas.
- A 20 h por semana: 7 a 11 semanas.

A 1.0 (mais 3 regiões) soma de **90 a 150 horas**. Programação é uns 45% do total; o resto é conteúdo, arte, efeitos e som, e a faixa larga vem quase toda daí.

## Lançamentos

1. **Demo pública** na Steam, gratuita: fases 1–3 da região 1, com o Bastião aparecendo logo na fase 1.
   - É uma variante da build (símbolo `TDCROWN_DEMO`, `GameDatabase_Demo`). Conteúdo cortado não entra na build.
   - Publicada meses antes de um Steam Next Fest.
2. **1.0 na Steam:** 28 fases (4 regiões × 7), 6 torres + 12 especializações, 4 mini bosses, 4 bosses, 28 itens, 4 poderes.
   - Preço-alvo de US$9,99–12,99.
   - Lançamento perto do Tower Defense Fest de março.

## O que a demo interna entrega (região 1 completa)

Entra:

- As 7 fases da região 1, com mini boss (Carrasco) e boss (Senhor da Brasa).
- As 6 torres em 3 níveis, com Bastiões e Dom.
- Os 5 inimigos da região 1.
- Os 7 itens e os poderes Luz da Coroa e Estandarte Real.
- A Árvore da Coroa e os Selos.
- Os modos Heroico e Provação.
- Telas: título, mapa-múndi, Preparação, HUD, pausa, vitória/derrota, Árvore, bestiário e opções.
- Save, localização (pt-BR, en, es), arte final da região 1, efeitos e som.

Fica para depois:

- Regiões 2–4, com os inimigos camuflados, os escavadores e as torres desativadas.
- Especializações que não couberem (ver "Decisões para tomar").
- Decreto Real e Juramento Antigo, se não couberem.
- Música própria (dá para usar uma faixa CC0 no começo).
- Controle (gamepad) e Steam Deck.
- Mac e Linux.

## Fases

Cada fase termina com algo jogável ou publicável. As horas são estimativas para uma pessoa com Unity 6 e o Claude Code ajudando.

### Fase 0: projeto e pipeline (4 a 6 h)

- [x] Projeto Unity 6 com o template Universal 2D (URP + Renderer 2D) e o Input System.
- [x] Git com o `.gitignore` da Unity e o repositório no GitHub (`Bili20/TD_crown`).
- [x] Pastas iniciais, `docs/` (GDD, ARQUITETURA, PLANO, Art Bible) e `ArtSource/`.
- [x] `PixelArtImportPostprocessor` (PPU 16, Point, sem compressão).
- [x] Primeiros sprites: soldado da Forja nv2, Diabrete, Balista nv1–nv3 e virote.
- [ ] Os quatro `.asmdef` da arquitetura (`TDCrown.Core` com `noEngineReferences`).
- [x] Teste do Animator com um sprite do Diabrete (controller `Triangle`, clip `Idle`).
- [x] Scripts de `ArtSource/` escrevendo o `art-manifest.json` (tamanho do frame, pivô, durações, loop, frame de impacto) e os sheets direto em `Assets/_Project/Art`.
- [x] **TD Crown → Arte → Gerar animações** (`AnimationGenerator`): fatia os sheets, cria clips e overrides; controllers base `Unit`, `TowerTurret` e `TowerBase`.
- [ ] Rodar o gerador no Editor e conferir o relatório no Console.
- [ ] Trocar o teste pelos clips gerados e apagar os sheets antigos `*_sheet.png`.
- [ ] Pacote Pipeline (`unity pipeline install`) para o Claude dirigir o Editor pelo Unity CLI.
- [ ] Pixel Perfect Camera (640×360, PPU 16), Custom Axis `(0, 1, 0)` e as camadas de sorting.
- [ ] Menu **TD Crown → Build Windows** e o `.exe` abrindo em outro PC.

**Pronto quando:** a build vazia abre em outro PC e os quatro assemblies compilam.

### Fase 1: simulação base (18 a 27 h)

- [ ] `CombatConfig`, `TowerDefinition`, `EnemyDefinition` e `LevelDefinition` como ScriptableObjects, preenchidos com os números do GDD.
- [ ] `LevelSim` em C# puro, passo fixo de 1/60 s:
  - inimigos andando no caminho;
  - mira, projéteis e dano na ordem da seção 4.3;
  - faixas de defesa e penetração;
  - lentidão;
  - ouro, vidas e ondas, com a chamada antecipada.
- [ ] Balista, Forja, Campanário e Alquimista completas, incluindo os soldados que bloqueiam, a Veterania, o respawn, a poça e a Corrosão.
- [ ] `BastionMap` e a matriz do Dom para essas quatro torres.
- [ ] Eventos da simulação (seção "A simulação conversa por eventos" da ARQUITETURA).
- [ ] Testes EditMode: dano, defesa, penetração, lentidão, pipeline de stats, Dom (próprio tipo e torres gêmeas), ouro por abate.
- [ ] `BalanceRunner` e o menu **TD Crown → Balanceamento** com builds roteirizadas.

**Pronto quando:** a fase 1 roda sem tela e a ferramenta reproduz os alvos do GDD: 250 de ouro pagam a abertura; com 2 tipos de torre o jogador termina com 18–20 vidas; com uma Balista só, perde.

### Fase 2: vertical slice jogável (18 a 28 h)

- [ ] `Game.unity` + cena da fase carregada por cima.
  - `LevelAuthoring` com gizmos dos caminhos e dos pontos.
  - **TD Crown → Gravar fase**.
- [ ] Views:
  - `TowerView` com base e besta em duas camadas;
  - `EnemyView`, `SoldierView` e `ProjectileView`;
  - interpolação entre passos.
- [ ] Shader `SpriteRecolor` com a textura de paleta e o `TeamPalette`. Conferir os 4 presets contra o lineup da Art Bible.
- [ ] Animator nas views (trigger `Attack` no `TowerAttackStarted`, troca de override ao subir de nível); `ProceduralWalk`; morte procedural e sombra separada.
- [ ] HUD mínimo (vidas, ouro, onda, 1x/2x, chamar onda) e menu radial (construir, upgrade, vender) em UI Toolkit.
- [ ] Linhas do bastião e hover do ponto vazio mostrando o Dom.
- [ ] As fases 1–3 (o slice é o conteúdo da demo pública) com Diabrete, Cão Infernal e Brutamontes.
- [ ] Playtest com 2–3 pessoas.

**Pronto quando:** as 3 fases se jogam de ponta a ponta e o playtest responde às duas perguntas do slice:
- o Dom muda onde e o que o jogador constrói?
- os soldados bloqueando funcionam e se leem?

### Fase 3: arte do slice (14 a 25 h)

Pela Art Bible, um arquivo por animação.

- [ ] Forja: bases nv1–nv3 (tijolo e pedra escura, fornalha em `HOLY`) e soldados nv1 e nv3.
- [ ] Campanário nv1–nv3 (cal, ardósia, sino de bronze) com o sineiro operador.
- [ ] Alquimista nv1–nv3 (tijolo, cobre, vidro) com o operador, o frasco e a poça ácida.
- [ ] Cão Infernal e Brutamontes.
- [ ] Tileset da região 1, ponto de construção vazio e base de bastião.
- [ ] Efeitos básicos: impacto, pulso do Campanário, morte, moedas.
- [ ] Proposta de estilo da UI em vetor (Preparação e HUD) e escolha das fontes.

**Pronto quando:** o slice não tem nenhum placeholder na tela.

### Fase 4: telas e meta (18 a 28 h)

- [ ] `GameFlow` com título, mapa-múndi, Preparação, pausa, vitória/derrota e opções.
  - Opções: resolução, janela, V-Sync, volumes, idioma, acessibilidade.
- [ ] Save em JSON com versão.
- [ ] Estrelas por vidas perdidas e Selos por nota (só a diferença).
- [ ] Árvore da Coroa com reset gratuito; especializações aparecendo no menu radial (com cadeado).
- [ ] Itens por tipo de torre e Capacidade da Coroa.
- [ ] Poderes da Coroa (Luz da Coroa, Estandarte Real) com recarga e atalhos.
- [ ] Modos Heroico e Provação.
- [ ] Pausa ao perder o foco.

**Pronto quando:** dá para jogar do título ao fim do slice, ganhar Selos e itens, comprar uma especialização, fechar o jogo e voltar com tudo salvo.

### Fase 4.5: localização (3 a 5 h)

Antes do conteúdo da região 1, para os textos novos já nascerem em tabela.

- [ ] `com.unity.localization`: pt-BR (origem), en, es.
- [ ] Tabelas `UI`, `Torres`, `Inimigos`, `Itens`, `Historia`, com fonte em `localization/*.csv`.
- [ ] Menu de importação dos CSVs.
- [ ] Smart Strings para "O Rei forjou: {item}".
- [ ] Glossário com tooltip (Dom, Bastião, Fé, Armadura, Selo).

**Pronto quando:** trocar o idioma troca todos os textos, sem texto fixo no código.

### Fase 5: conteúdo da região 1 (20 a 32 h)

- [ ] Relicário (Fé, Raio) e Falcoaria (falcões, marca), na simulação e na arte. A matriz do Dom fica completa.
- [ ] Ninhada (crias com 0 ouro) e Gárgula (voador).
- [ ] Carrasco do Portal e Senhor da Brasa, com as habilidades telegrafadas.
- [ ] As 7 fases da região 1 montadas, balanceadas pela ferramenta e jogadas.
- [ ] Os 7 itens, incluindo os mecânicos (Elmo do Carrasco, Brasa Aprisionada).
- [ ] Onboarding:
  - Conselheira, com uma frase por vez apontando para a tela;
  - cartão de "Nova ameaça";
  - bestiário.
- [ ] Abertura da história (5–6 telas) e apresentação dos bosses.

**Pronto quando:** a região 1 se joga do começo ao fim e a ferramenta não marca nada fora dos alvos.

### Fase 6: especializações (12 a 20 h)

- [ ] As especializações que entram na demo (ver "Decisões para tomar"), com o operador ou os soldados próprios de cada uma.
- [ ] Controle duro com imunidade de 1 s e metade da duração em bosses; peso Leve e Pesado.

**Pronto quando:** cada especialização muda como a torre é usada, conferido em playtest.

### Fase 7: efeitos, áudio e acabamento (10 a 18 h)

- [ ] Efeitos de cada torre e status, hit flash, tremor de tela (com opção de desligar) e "clink" da armadura.
- [ ] Sons de torres, inimigos, UI e poderes, e uma faixa de música por região.
- [ ] Ícone do executável, cursor e telas de carregamento.
- [ ] Passada de acessibilidade: daltonismo (preset), escala de texto, reduzir flashes.

**Pronto quando:** um vídeo de 30 s do jogo serve para a página da Steam.

### Fase 8: demo pública (6 a 10 h)

- [ ] Variante da build com `TDCROWN_DEMO` e `GameDatabase_Demo` (fases 1–3).
- [ ] Página da Steam: cápsulas (vetor), capturas e trailer com duas torres trocando o Dom nos primeiros 5 s.
- [ ] Página separada para a demo; inscrição no próximo Next Fest.

**Pronto quando:** a demo está publicada e a página recebe wishlists.

## Depois da demo: 1.0

| Bloco | Horas | Conteúdo |
|---|---|---|
| Região 2: Floresta Profana | 30 a 50 | Cultista, Xamã, camuflagem, voadores em massa, rotas cruzadas, Inquisidor Caído, Mãe da Ninhada |
| Região 3: Picos de Ferro | 30 a 50 | armadura alta, escavadores, pontos elevados, Capataz Possuído, Golem Profanado |
| Região 4: A Capital | 30 a 50 | portais dentro dos muros, 3 entradas, torres desativadas, Orvan e Vael'Khor, final da história |

Cada região traz 7 fases, 7 itens e a arte do bioma.

## Ordem e paralelismo

- A arte (Fase 3) pode andar junto com as Fases 1 e 2: os scripts de `ArtSource/` não dependem do código.
- A localização (4.5) entra antes do conteúdo (Fase 5), para não reescrever textos.
- Balanceamento é contínuo: toda fase do plano termina rodando a ferramenta.

## Decisões para tomar

1. **Quais especializações entram na demo interna:**
   - todas as 12;
   - ou só as das 3 torres do slice (Balista, Forja, Campanário).
2. **Áudio:** Audio Mixer da Unity, ou FMOD se entrar um sonoplasta.
3. **Velocidades** "muito rápido / lento / médio" dos inimigos: fechar no playtest do slice.
4. **Nome do jogo e do reino.**
5. **Licença comercial** de cada pacote de assets comprado (itens, ícones), antes de entrar na build.
6. **Notion × GDD.md:** manter o Notion como caderno de ideias e o GDD.md como verdade, ou parar de atualizar o Notion.

## Riscos

| Risco | Mitigação |
|---|---|
| Soldados bloqueando (IA, rally point, combate corpo a corpo) é o sistema mais caro | Entra já no vertical slice; se não funcionar, a Forja vira torre de controle sem bloqueio |
| O Dom não mudar a decisão do jogador | Pergunta central do playtest do slice; o level design dos bastiões é a alavanca |
| Torre dominante e picos de dificuldade (a crítica mais comum em reviews do gênero) | Ferramenta de balanceamento com builds roteirizadas desde a Fase 1 |
| Escopo de 28 fases para uma pessoa | A demo vem antes; as regiões 2–4 entram em blocos e a 4ª pode virar atualização |
| Arte por código não dar conta de torres e bosses grandes | Art Bible com exemplos aprovados; se travar, encomendar só os bosses |
| Legibilidade com sprites de 16 px e várias camadas de status | No máximo 2 ícones por inimigo, pips de defesa, teste em 1080p desde o slice |

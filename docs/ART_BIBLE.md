# Art Bible — TD (nome provisório)

> Status: **estilo de personagem aprovado** (teste v2, ver §9). Desde 16/11 inimigos podem ter **andar desenhado** (`walk`, §6). Paletas das regiões 2–4, torres, tiles e UI ainda em aberto (§10).

## 1. Direção

**Tom:** fantasia medieval sombria, mas legível e simpática. Personagens pequenos e expressivos; o perigo vem da quantidade de demônios e do contraste de fogo e sangue com um reino de cores frias e terrosas.

**Referências**
- **Personagens:** estilo da folha KO.DLL — figura baixa e larga (~10 px de altura), chapéu/elmo ocupando quase metade, sem contorno externo, rosto de 4 px com olhos escuros nas laterais, mãos de 1 px, armas grandes em cor clara e sombra em elipse no chão.
- **Perspectiva e montagem de mapa:** "Swamp Tileset" e "Guardian Towers" (top-down 3/4, tiles 16×16, caminho de pedra, pontos de construção marcados no chão). "Simple Winter" só como referência de composição de mapa (é vetor; não usar o estilo).
- Nunca copiar arte das referências: elas definem escala, leitura e composição.

**Modo principal:** pixel art para tudo que está no mundo (terreno, torres, unidades, inimigos, projéteis, VFX).
**Exceções declaradas:** UI, logo e material de loja em **vetor** (perfil no §4.4).

**Evitar**
- Contorno externo em volta da figura: a silhueta vem do contraste com o fundo e da sombra no chão.
- Detalhe de 1 px isolado que some na escala 1×.
- Gradiente, anti-aliasing ou dithering pesado em personagens.
- Inimigos dessaturados que se confundem com o cenário.

## 2. Técnico

| Item | Valor |
|---|---|
| Engine | Unity 6, URP 2D |
| Perspectiva | top-down 3/4, grade quadrada (não isométrico) |
| Tile | 16×16 px |
| PPU | 16 |
| Resolução de referência | 640×360, Pixel Perfect Camera, escala inteira (×3 em 1080p, ×4 em 1440p) |
| Filtro / compressão | Point / None, sem mipmap |
| Orientação das unidades | 3/4 olhando para **baixo-direita**; esquerda via flipX |
| Luz | de cima e da esquerda |
| Sorting | por Y (Transparency Sort Axis = 0,1,0); pivô na base |

## 3. Forma e leitura

- **Silhueta primeiro.** Torres e unidades do jogador são em cinza, então o que diferencia cada uma é a forma: chapéu, arma, escudo, asa, estrutura da torre. Teste a silhueta preenchida de uma cor só antes de sombrear.
- **Proporção (KO.DLL):** figura de 8–11 px de altura e ~10–13 px de largura com arma; chapéu/elmo + rosto ≈ metade da altura; corpo de 3 linhas; pernas de 1 linha no tom mais escuro.
- **Sem contorno externo.** O tom mais escuro (índice 0 no jogador, `OUTLINE` nos inimigos) aparece só em olhos, pernas, boca e riscos internos (centro do escudo).
- **Rosto:** 4 px de pele com os olhos como pixels escuros nas laterais; pele com 1 px de luz no centro.
- **Mãos e armas:** mãos de 1 px de pele segurando a arma; armas grandes, retas (vertical ou horizontal, nunca diagonal) e em cor clara. Espada = lâmina de 1 px + guarda de 3 px + cabo e pomo escuros. Escudo = bloco de metal com risco central escuro.
- **Pluma do time:** toda unidade do jogador tem uma peça na cor primária no topo (pluma, flâmula, capuz) para a cor do time aparecer acima da multidão.
- **Elmo com pluma é só para militares** (soldados da Forja e operador da Balista). Os ofícios evoluem por chapéu, roupa e ferramenta, e cada ofício tem o seu: ferreiro de lenço amarrado, sineiro de chapéu de aba, alquimista de capuz/touca com óculos/chapéu cônico. Duas torres nunca repetem o mesmo boneco no mesmo nível.
- **Demônios:** olhos no acento (`HELLFIRE`), chifres no tom claro da rampa, asas de membrana escura com nervura no tom base. **O olho é sempre o pixel mais claro do inimigo**: brasas do corpo param em `HELLFIRE.base` (no Cão, em `HELLFIRE.dark`), senão o ponto focal pula da cabeça para o corpo e vira um segundo par de olhos. Faíscas de golpe podem passar disso, porque duram um frame.
- **Brutamontes em redesenho (16/11):** o primeiro (de frente, simétrico, cabeça-caixa e clava num palito) ficou duro e com cara de robô. A versão nova parte de massa orgânica e assimétrica; 3 silhuetas aguardam escolha (§10).
- **Inimigos grandes saem do chibi.** De `unit_large` para cima: cabeça pequena afundada entre os ombros, ombros e braços enormes, cintura estreita. Ao lado dos diabretes cabeçudos, a diferença de massa já diz "tanque". Quanto maior o inimigo, mais detalhe (placas, rebites, brasas nas juntas), sempre com 3 materiais + acento no máximo.
- **Quadrúpedes** (Cão Infernal, aprovado em 16/11): de perfil, virados para a direita. Corcunda tipo hiena (ombro alto, quadril baixo, cabeça à frente do cangote), tufos quebrando o dorso e cauda curta caída. O idle é **em pé, respirando**; a corrida é o `walk` desenhado (galope), não mais a pose base. Pernas de perto no tom do pelo, pernas de longe em `OUTLINE`.
- **Materiais por figura:** no máximo 3 rampas mais pele e acento.
- **Sombra no chão:** elipse `SHADOW_BLOB` com 60–70% da largura da figura, 2–3 px de altura, desenhada separada (objeto próprio) para acompanhar o pulo procedural sem subir junto. O topo da elipse fica **na linha dos pés ou abaixo**, nunca sobre as pernas: o `SHADOW_BLOB` é quase o `OUTLINE`, e numa figura escura (Cão) a sombra em cima das pernas apaga as patas.
- **Torres:** cada nível muda a silhueta (altura, telhado, bandeira, estrutura), não só detalhes. Especializações têm uma peça marcante exclusiva.
  - **Cada torre tem um material próprio**, mantido do nv1 ao nv3 (do simples ao nobre dentro desse material). Como todas as torres usam a cor do time, o material é o que diferencia uma torre da outra de longe. Tabela aprovada em 14/11:

    | Torre | Material de identidade | nv1 → nv2 → nv3 | Peça marcante |
    |---|---|---|---|
    | Balista | madeira + ferro (nv3 em pedra, exceção aprovada) | andaime de madeira → torre de troncos com cintas → bastião de pedra com estandarte | besta e virote com pena do time |
    | Forja de Guerra | tijolo + pedra escura, fogo em `HOLY` | barraca de lona com bigorna → oficina de tijolo com chaminé → forja-quartel de pedra escura com fornalha | fornalha acesa e fumaça |
    | Campanário | cal (`WHITEWASH`) + ardósia (`SLATE`) | armação de madeira com sino pequeno → campanário caiado → torre sineira alta | sino de `BRONZE` que balança no pulso |
    | Alquimista | taipa/tijolo + `COPPER` e `GLASS` | bancada com caldeirão → cabana de taipa com alambique → torre com cúpula de cobre e vidro | frascos e fumaça verde |
    | Relicário | `MARBLE` + `HOLY` | altar de pedra com relíquia → capela pequena → santuário de mármore com vitral | brilho dourado que cresce com a Fé |
    | Falcoaria | madeira rústica + `STRAW` | poleiro de galhos → cabana de vime com telhado de palha → viveiro alto com poleiros | ninhos e falcões pousados |

  - **Fogo do jogador é sempre `HOLY`** (amarelo), nunca `HELLFIRE` (laranja dos demônios).
  - **Duas camadas:** a **base** (`tower`, 32×48) é fixa e **não espelha** — a luz continua vindo da esquerda; a **arma + operador** (`tower_turret`, 20×16) fica por cima, alinhada com a linha da cintura (`waist_row`) no topo do parapeito, e vira para a esquerda com flipX.
  - **Cor do time na base:** flâmula no mastro (anima no idle), escudo (nv2) ou estandarte com emblema (nv3), em índice primário; franjas e acabamentos na secundária.
- **Minions e operadores evoluem com a torre.** Toda torre tem gente:
  - Torre que **invoca** unidades (Forja): as unidades mudam de visual a cada nível — equipamento, capacete e pluma crescem do nv1 ao nv3.
  - Torre que **não invoca**: tem um **operador** visível no topo, cortado na cintura pelo parapeito, que também evolui (ex.: Balista — Recruta de gorro de pano → Besteiro de chapéu de ferro com pluma → Mestre-Balisteiro com elmo, guardas de bochecha, ombreiras e tabardo com emblema).
  - O operador anima junto com a arma: respira no idle e participa do disparo (firma o corpo, recarrega).
  - Especializações trocam o operador por uma variação própria (a definir por torre).
  - Decisões por torre (16/11):
    - **Forja:** não tem camada de cima. Um **ferreiro martelando a bigorna** faz parte da base e anima no idle, junto da fornalha em `HOLY` e da fumaça. Ferreiro: aprendiz de gorro → ferreiro de touca e avental de couro → mestre-ferreiro de chapéu com pluma, avental e braçadeiras. Soldados: nv1 recruta (gorro de pano, espada curta, broquel de madeira, sem metal), nv2 chapéu de ferro com pluma, nv3 elmo completo, ombreiras e escudo heráldico com o emblema.
    - **Campanário:** mantém base + camada de cima (sino + sineiro), **sem flipX**, para todas as torres terem a mesma estrutura de view. O sineiro **bate no sino com um malho** de madeira; o sino fica ao lado dele e balança no `attack`. O sino cresce por nível (5, 7 e 9 px de largura). No nv2 e nv3 o telhado de ardósia fica acima da camada de cima, apoiado em pilares caiados.
    - **Alquimista:** o operador arremessa e vira com flipX. Aprendiz de capuz (capuz na primária) → alquimista de avental de couro e luvas → mestre de chapéu cônico (primária) com aba (secundária) e manto. O frasco erguido na mão é de vidro com líquido `ACID`. O nv2 tem o telhado do time atrás do operador, com a janela escura do sótão para o capuz não sumir contra o telhado; o nv3 tem a cúpula de cobre atrás dele.
- **Ponto de construção vazio:** base de entulho/pedra com placa de ícone; deve ler como "aqui dá para construir" a 1×.
- **Legibilidade de time:** jogador = cores do preset (azul/dourado por padrão) e formas retas; demônios = vermelho, roxo e fogo, formas curvas e pontiagudas.
- **Time nunca só por cor** (o dourado do jogador e o laranja dos demônios se confundem em deuteranopia/protanopia): forma e acessório distinguem os times, a barra de vida do jogador tem ponta de escudo e há um preset de recolor para daltonismo (`daltonismo`). Testar sprites novos no Color Oracle.
- **Estandarte Real:** um estandarte do jogador (asset de poder) no preset ativo, cravado no centro do bastião.

## 4. Cor

### 4.1 Unidades e torres do jogador — escala de cinza indexada
Todo asset do jogador é desenhado **só com os 8 cinzas exatos** da paleta `player_index` (mais as rampas fixas permitidas). O shader troca cada cinza pela cor do preset.

| Índice | Cinza | Uso |
|---|---|---|
| 0 | 0 | tom mais escuro: olhos, pernas, riscos internos |
| 1 | 36 | parte primária — sombra |
| 2 | 73 | parte primária — base |
| 3 | 109 | parte primária — luz |
| 4 | 146 | parte secundária — sombra |
| 5 | 182 | parte secundária — base |
| 6 | 219 | parte secundária — luz |
| 7 | 255 | brilho / metal polido |

- **Primária** = roupa, telhado, estandarte (cor do "time"). **Secundária** = metal, madeira, detalhes.
- **Cores fixas** (não recolorem): pele (`SKIN`) e luz sagrada (`HOLY`). O shader deixa passar pixels com saturação acima de 0,15.
- Nunca usar um cinza fora dos 8 valores: um tom errado vira o índice errado no jogo.
- **Regra do shader:** só é recolorido o pixel de **cinza neutro** (R, G e B iguais, tolerância 2). Qualquer cor com tom passa direto — por isso pele, madeira, pedra e ferro ficam com a cor natural mesmo dentro de um asset do jogador.
- **Tom `deep`:** as rampas de material têm um 5º tom, mais fundo e puxado para azul/roxo, usado em juntas, sombras projetadas e oclusão.
- **Rampas fixas permitidas** em assets do jogador: `SKIN`, `HOLY`, `WOOD`, `STONE`, `IRON`, `STRING` (corda/linha) e os materiais de torre `DARK_STONE`, `BRICK`, `WHITEWASH`, `SLATE`, `BRONZE`, `COPPER`, `GLASS`, `MARBLE`, `STRAW`, mais `ACID` (líquido do Alquimista e a poça; proposta de 16/11, aguarda aprovação da prancha). Todas têm leve tom (validado no JSON) e nunca podem ser trocadas por cinza puro.
- **`ACID`** é um verde-limão saturado: contrasta em valor com a terra do caminho e em saturação com a grama, e não se confunde com o `HELLFIRE` dos demônios. Em áreas grandes (a poça) o preenchimento é o tom escuro; base e claro ficam só na borda, nas ondulações e nas bolhas, para a poça não virar o objeto mais claro da cena.
- Presets no JSON (`recolor.presets`): `real` (padrão), `rubi`, `floresta`, `daltonismo` (azul e branco, sem amarelo/laranja), e três patentes da Veterania da Forja (recruta → sargento → capitão; patente máxima 3).

### 4.2 Inimigos — cor direta
Demônios usam cor normal (sem recolor). Rampas da região 1 em `region1_vale`:
- `DEMON` — pele e corpo de diabretes e brutamontes.
- `HOUND_FUR` — pelo preto-violeta do Cão Infernal (aprovado em 16/11). Escuro puxando para o roxo, claro para o quente; o tom mais fundo é o próprio `OUTLINE`. Separa o cão do Diabrete de longe e segue o folclore (cão negro de olhos em brasa). A brasa (olho, uma brasa no dorso, boca) é `HELLFIRE`, com `DEMON.base` como brasa fraca.
- `HELLFIRE` — acento: olhos, chifres incandescentes, fogo.
- `CULT_ROBE` — cultistas (sacerdotes que seguiram Orvan).
- `GARGOYLE` — gárgulas e pedra corrompida. Atenção: hoje tem os mesmos valores do `IRON` e fica perto da pedra do cenário; revisar antes de desenhar a Gárgula (proposta: cinza arroxeado com rachaduras em `HELLFIRE`).
- `BLACK_IRON` — ferro negro das placas cravadas no Brutamontes (proposta de 16/11, aguarda aprovação da prancha). Mais escuro e frio que o `IRON` do jogador, para o metal dos demônios não parecer equipamento do reino.

### 4.3 Cenário — região 1
`GRASS`, `DIRT` (caminho), `STONE`, `WOOD`. O caminho dos inimigos sempre contrasta com a grama em valor (mais claro ou mais escuro), não só em matiz.

Regiões 2–4 ainda sem paleta (§10).

### 4.4 UI em vetor
- **Linguagem:** "chunky" heráldica — formas angulares e robustas, cantos de 2–6 px, contorno `INK` de 6 px (canvas 256), sombra dura deslocada sem blur, sombreamento cel, **sem gradiente**.
- **Motivos:** coroa, estandarte, escudo, pergaminho, selo de cera.
- **Paleta:** só cores derivadas do jogo (`vector.palette_colors`): pergaminho, azul real, dourado, sangue, fogo, tinta.
- **Fontes:** serifada de display para títulos; sans legível para números e tooltips (definir na proposta de UI).
- **Entrega:** PNG em 1× e 2× para 9-slice no UI Toolkit (`-unity-slice-*`); ícones podem ir como VectorImage.

## 5. Tamanhos

| Classe | Frame | Chão (y) | Altura da figura | Exemplos |
|---|---|---|---|---|
| `unit_small` | 16×16 | 15 | 8–11 | Diabrete, Cão Infernal (~10 px de altura, 13 de comprimento), soldado da Forja |
| `unit_medium` | 20×20 | 19 | 11–14 | Gárgula, Cultista e Xamã (região 2) |
| `unit_large` | 24×24 | 23 | 18–22 | Brutamontes, Ninhada |
| `miniboss` | 32×32 | 31 | 24–30 | Carrasco do Portal |
| `boss` | 48×48 | 47 | 36–46 | Senhor da Brasa |
| `tower` | 32×48 | 44 | 28–44 | base das torres, todos os níveis |
| `tower_turret` | 20×16 | — (cintura na linha 12) | — | arma + operador sobre o parapeito |
| `build_spot` | 32×32 | 28 | — | ponto de construção vazio |
| `projectile` | 8×8 | — | — | virote, frasco, pena. O frasco é um sprite só, sem rotação: voa em arco com sombra no chão |
| `zone` | 32×32 | — (pivô Center) | — | zona no chão de 1 tile de raio (poça do Alquimista), camada de sorting `GroundFx`. O contorno é a área do sim (círculo de 30 px), com mossas para não ler como disco |
| `tile` | 16×16 | — | — | terreno |

"Chão (y)" é o limite de baixo da classe. A linha real dos pés vem do `ground_row` de cada script e vira o pivô no manifesto: Diabrete e Cão Infernal usam a linha 13, o soldado da Forja a 14 (a folga de 1 px fica para a sombra separada e para a borda).

Proporção alvo: a unidade pequena tem ~1/3 da altura da torre nível 1.

Altura-alvo das torres por nível (da base ao topo da flâmula): **nv1 ~25–28 px, nv2 ~34–40 px, nv3 até 46 px**. Torre cuja nv2 já ocupa o quadro inteiro não tem para onde crescer no nv3.

Limite de cores por quadro: 16 em geral, 20 em turrets e unidades do jogador e **26 em bases de torre** (`tower`), que juntam vários materiais e às vezes gente embutida (o ferreiro da Forja). O validador lê o limite por classe em `validation.max_colors_per_size_class`.

## 6. Animação

| Tipo | Animações desenhadas | Frames | Duração |
|---|---|---|---|
| Unidades e inimigos | idle, ataque; **andar (`walk`) opcional** | idle 4–6; ataque 4–7; andar 4–8 | idle 130–260 ms; frame do golpe ~70 ms; andar 60–140 ms |
| Torres | idle (bandeira, fumaça, sino) e disparo quando houver peça móvel | 4–6 | 150–250 ms |
| Bosses | idle, ataque, assinatura | 4–8 cada | igual às unidades |

**Andar desenhado (`walk`, desde 16/11).** Inimigos e unidades podem ter o ciclo de andar em frames. É opcional: quem não tem continua tocando o idle enquanto anda, com o andar procedural.
- **Velocidade de referência:** cada ciclo é desenhado para uma velocidade no chão em que os pés não deslizam. O script mede o recuo dos pés apoiados e grava `groundSpeedTilesPerSecond` no manifesto. No jogo, o Animator toca o `walk` a `velocidade atual ÷ referência`, então lentidão e atordoamento aparecem sozinhos. Desenhe para uma velocidade perto da do GDD: acima de ~1,5× o ciclo fica corrido.
- **Com `walk`, o andar procedural fica desligado** (sem pulo, inclinação nem squash): o balanço já está nos frames e somar os dois deixa o sprite tremendo; a inclinação ainda gira pixel e cria mixels.
- **Técnica** (a mesma do Cão Infernal e do Diabrete): o asset é um rig de partes e cada animação é uma lista de poses. Para não sair duro:
  - nada se move junto: ombro antes do quadril, cabeça um frame depois do corpo, ponta da cauda ou da asa atrasada em relação à base (forma muda, não só lugar);
  - pé apoiado recua na velocidade do chão; o pé no ar volta rápido;
  - quadrúpede no passo usa a sequência lateral (traseira-esq, dianteira-esq, traseira-dir, dianteira-dir) com quadril e ombro em fases opostas; corredor usa galope rotativo de 6 frames (extensão, pouso da frente, apoio da frente, recolhido, apoio de trás, impulso);
  - idle com durações variadas e um frame de assentamento abaixo do neutro, para o laço não parar;
  - nenhuma sombra no sprite (a `SHADOW_BLOB` é outro objeto);
  - **enxame fora de sincronia:** cada instância começa o idle e o `walk` num frame aleatório, senão dez Diabretes batem as asas juntos.

**Procedural (código, sem frames):**
- **Andar** (só para quem não tem `walk`): pulo de 1 px, inclinação ±5°, squash de 10% no pouso, 2 passos por tile; a frequência acompanha a velocidade **atual** (lentidão e congelamento aparecem sozinhos).
- **Morte:** flash branco 60 ms → queda/achatamento 180 ms → fade 200 ms + ~6 partículas.
- **Dano:** hit flash de 60 ms no mesmo shader do recolor.

## 7. Processo

**Pipeline em 5 etapas (skill `pixel-art-2d`, desde 16/11):** silhueta → blocagem por material e plano → luz e sombra → material e detalhe → acabamento (sem contorno, ver §1). Construções e props usam o mapa de material de `ArtSource/material_map.py`: cada pixel guarda material, plano e tom, e as receitas (`stone_courses`, `brick_courses`, `planks`, `tile_roof`, `plaster_wear`) aplicam a textura com irregularidade de semente fixa. Personagens de até ~24 px seguem em grade ASCII, no perfil KO.DLL. Cada torre tem `build_base(nível, pose, stage)` para renderizar qualquer etapa.


1. Antes de desenhar: ler a entrada do asset no GDD (Notion), o papel e as habilidades.
2. Assets do jogador: desenhar direto nos 8 cinzas; testar com pelo menos 2 presets de recolor.
3. Mostrar pose base ampliada (6×) sobre o fundo de preview, ao lado dos aprovados.
4. Aprovação → animação → validação (`validate_sprite.py` + lineup) → entrega.
5. Asset aprovado entra em §9.

## 8. Entrega

- **Um arquivo por animação.** Nunca juntar animações diferentes no mesmo PNG. Nome: `{asset_id}_{animação}.png`, com os frames numa única linha, todos do mesmo tamanho, fundo transparente e 1 px de folga dentro de cada frame.
  - `asset_id` inclui o nível quando o visual muda por nível: `forge_soldier_lv2`, `balista_turret_lv3`.
  - Vocabulário fixo de animações (usar só estes nomes; um novo entra aqui antes de ser usado):

    | Nome | Uso |
    |---|---|
    | `idle` | parado / respirando; bases de torre (flâmula, fumaça, sino) |
    | `attack` | ataque e disparo de torre |
    | `walk` | ciclo de locomoção em loop (passo, trote ou galope, conforme o inimigo); registra `groundSpeedTilesPerSecond` |
    | `hit` | reação a dano, quando for desenhada (o padrão é o hit flash do shader) |
    | `death` | morte desenhada (o padrão é a morte procedural) |
    | `special` | habilidade de boss, especialização ou poder; com sufixo quando houver mais de uma (`special_stun`) |
    | `spawn` | entrada em cena (portal, invocação) |
    | `directions` | projéteis: uma direção por frame, na ordem E, SE, S, SW, W, NW, N, NE |

  - Exemplos: `imp_idle.png`, `imp_walk.png`, `imp_attack.png`, `cao_infernal_walk.png`, `balista_base_lv1_idle.png`, `balista_turret_lv1_attack.png`, `balista_bolt_directions.png`.
  - Pasta: `Assets/_Project/Art/{categoria}/{Asset}/`, todos os arquivos de um asset juntos.
- **Na Unity (Animator):**
  - Cada arquivo vira um clip `{asset_id}_{animação}.anim`, com a duração de cada frame igual à do script de arte (não um fps fixo).
  - O script de arte registra no `Assets/_Project/Art/art-manifest.json`: tamanho do frame, pivô, durações em ms, loop e frame de impacto (`impact_frame`, o frame em que o golpe acerta ou o projétil sai).
  - O gerador **TD Crown → Arte → Gerar animações** fatia os sheets e cria os clips e os overrides a partir do manifesto.
- **Pasta:** `Assets/_Project/Art/` + `Enemies/`, `PlayerUnits/`, `Towers/`, `Tiles/`, `Projectiles/`.
- **Import:** Sprite Mode Multiple, PPU 16, Filter Point, Compression None, sem mipmap, slice Grid By Cell Size, pivô Bottom Center.
- Nada de editar `.meta`, `.prefab` ou `.asset` à mão.

## 9. Exemplos aprovados

### Soldado da Forja — v2 (aprovado em 10/11)
- Arquivos: `forge_soldier_index_v2.png` (pose base), `forge_soldier_lv2_idle.png`, `forge_soldier_lv2_attack.png`.
- Nível: este visual é o **soldado nv2** (chapéu de ferro com pluma). Faltam nv1 (recruta, sem metal) e nv3 (elmo completo, ombreiras, tabardo com emblema) — mesma progressão do operador da Balista.
- Funcionou: elmo de metal com **pluma do time** — a v1 sem pluma lia como bandana/cabelo loiro; escudo com risco central escuro (a v1 lia como mancha branca); espada de pé ao lado no idle; recolor validado em 4 presets.
- Refeito: a v1 tinha contorno preto por parte e figura de 15 px; ficou pesada e longe da referência. A v2 tirou o contorno e baixou para ~10 px.

### Balista nv1–nv3 — v1 (aprovada em 14/11)
- Arquivos: `balista_base_lv{1,2,3}_idle.png` (flâmula), `balista_turret_lv{1,2,3}_idle.png`, `balista_turret_lv{1,2,3}_attack.png` (disparo), `balista_bolt_directions.png` (virote em 8 direções).
- Bases: nv1 plataforma de madeira com pernas em X; nv2 torre de vigia de troncos com cintas de ferro, paliçada e escudo do time; nv3 bastião de pedra com ameias, mata-cães e estandarte com emblema.
- Operador: Recruta → Besteiro → Mestre-Balisteiro (ver §3).
- Aprovado como está: no nv1 o arco de madeira fica discreto sobre o parapeito de madeira; o destaque cresce nos níveis seguintes.
- Ajuste feito: o arco precisava descer **abaixo da cintura**, por cima do parapeito; com o quadro cortado na cintura o braço de baixo sumia e a arma lia como besta de mão.
- Virote com a pena na cor do time, ponta em brilho (índice 7).

### Cão Infernal — v2 (aprovado em 16/11)
- Arquivos: `cao_infernal_idle.png` (6 frames), `cao_infernal_walk.png` (galope, 6 × 65 ms, sem deslizar a 1,92 tile/s), `cao_infernal_attack.png` (7 frames, impacto no frame 3, windup de 390 ms). Script: `ArtSource/cao_infernal.py`, pipeline completo em 5 etapas.
- Escolhido entre 3 silhuetas (crina de fogo, corcunda, demônio de chifre): a corcunda tipo hiena foi a escolhida.
- Funcionou: focinho de 2 px e cauda caída (as primeiras silhuetas, de corpo curto e cauda em pé, liam como gato); luz larga no topo da corcunda (massa escura chapada virava mancha); um só ponto de brasa no dorso; olho de 2 px (miolo `HELLFIRE` + órbita em `DEMON.base`); bufada de boca aberta com brasa dentro no idle; colchete de brasa em volta do focinho na mordida.
- Refeito: duas brasas lado a lado no dorso liam como um segundo par de olhos; um pixel vermelho de luz rebatida na barriga parecia ferida; a garra em osso virava ruído a 1×; a cauda comprida pendurada alinhava com a pata de trás e lia como quinta pata.

### Diabrete — animação v3 (16/11)
- Mesma pose base do v2 (conferida pixel a pixel), agora em rig: cabeça, tronco, asas em 3 ângulos em volta do ombro, cauda e pernas. Script: `ArtSource/diabrete.py` (substitui a parte do Diabrete em `animate_v2.py`).
- `imp_idle.png` 6 frames (a cabeça desce antes do tronco e sobe depois, as asas batem fora de fase, uma piscada), `imp_walk.png` 6 × 120 ms (2 passos por tile, referência de 1,39 tile/s), `imp_attack.png` 6 frames com o mesmo windup de 140 ms. O bote é da cabeça: com o corpo indo à frente, as asas encostavam na borda do frame.

### Diabrete — v2 (aprovado em 10/11)
- Arquivos: `imp_v2.png` (pose base), `imp_idle.png`, `imp_attack.png`.
- Funcionou: asas de morcego abertas com nervura (a v1 com asa fechada lia como braço), chifres claros, olhos `HELLFIRE`, presa em `EYE_WHITE`, cauda à direita.
- Escala: ~9 px de altura, menor que o soldado — o enxame tem que parecer fraco sozinho.

## 10. Pendências

- **Paletas das regiões 2–4:** Floresta Profana, Picos de Ferro, A Capital.
- **Tileset:** decidir se o terreno será desenhado ou adaptado de pacote comprado (conferir licença comercial).
- **Ícones de itens:** vêm do pacote comprado — definir se ficam como estão ou passam por ajuste de paleta para casar com o jogo.
- **UI:** proposta de estilo (painel de Preparação + HUD) e escolha das fontes.
- **Bases das 4 torres refeitas no pipeline novo (16/11)** e exportadas (idle); falta aprovação do dono. Camadas de cima do Campanário e do Alquimista, soldados nv1/nv3, Brutamontes, frasco e poça ainda sem animação.
- **Lote da demo pública (16/11), poses base em revisão:** Forja nv1–nv3 com o ferreiro, soldados nv1 e nv3, Campanário nv1–nv3 com o sineiro, Alquimista nv1–nv3 com o operador, frasco e poça. Scripts: `forja.py`, `campanario.py`, `alquimista.py`; prancha em `prancha_demo.py`.
- **Brutamontes refeito do zero (16/11):** 3 silhuetas em 24×24 aguardam escolha — **A** gorila de ferro (anda nos punhos, carapaça de ferro negro com espinhos, cabeça baixa à frente); **B** carcereiro (corcunda, cabeça miúda de um chifre, bola de ferro na corrente arrastando à frente); **C** tronco cravado de pregos no ombro. Todos com `walk` desenhado. O desenho antigo continua em `inimigos_r1.py` só até a escolha.
- **`walk` dos soldados da Forja:** opcional; decidir depois de ver o Diabrete e o cão andando no jogo.
- **Nome do sheet do Diabrete:** o asset é `imp`, mas o id fixo do inimigo é `diabrete`. Renomear muda os GUIDs dos clips e do override; decidir antes de criar o prefab.
- Operadores do Relicário (monge) e da Falcoaria (falcoeiro).
- **`frame0_luminance_range`:** medir nos primeiros aprovados.

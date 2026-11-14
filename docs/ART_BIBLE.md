# Art Bible — TD (nome provisório)

> Status: **estilo de personagem aprovado** (teste v2, ver §9). Paletas das regiões 2–4, torres, tiles e UI ainda em aberto (§10).

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
- **Demônios:** olhos no acento (`HELLFIRE`), chifres no tom claro da rampa, asas de membrana escura com nervura no tom base.
- **Materiais por figura:** no máximo 3 rampas mais pele e acento.
- **Sombra no chão:** elipse `SHADOW_BLOB` com 60–70% da largura da figura, 2–3 px de altura, desenhada separada (objeto próprio) para acompanhar o pulo procedural sem subir junto.
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
- **Rampas fixas permitidas** em assets do jogador: `SKIN`, `HOLY`, `WOOD`, `STONE`, `IRON`, `STRING` (corda/linha) e os materiais de torre `DARK_STONE`, `BRICK`, `WHITEWASH`, `SLATE`, `BRONZE`, `COPPER`, `GLASS`, `MARBLE`, `STRAW`. Todas têm leve tom (validado no JSON) e nunca podem ser trocadas por cinza puro.
- Presets no JSON (`recolor.presets`): `real` (padrão), `rubi`, `floresta`, `daltonismo` (azul e branco, sem amarelo/laranja), e três patentes da Veterania da Forja (recruta → sargento → capitão; patente máxima 3).

### 4.2 Inimigos — cor direta
Demônios usam cor normal (sem recolor). Rampas da região 1 em `region1_vale`:
- `DEMON` — pele e corpo de diabretes, cães e brutamontes.
- `HELLFIRE` — acento: olhos, chifres incandescentes, fogo.
- `CULT_ROBE` — cultistas (sacerdotes que seguiram Orvan).
- `GARGOYLE` — gárgulas e pedra corrompida.

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
| `unit_small` | 16×16 | 15 | 8–11 | Diabrete, soldado da Forja |
| `unit_medium` | 20×20 | 19 | 11–14 | Cão Infernal, Gárgula, Cultista e Xamã (região 2) |
| `unit_large` | 24×24 | 23 | 18–22 | Brutamontes, Ninhada |
| `miniboss` | 32×32 | 31 | 24–30 | Carrasco do Portal |
| `boss` | 48×48 | 47 | 36–46 | Senhor da Brasa |
| `tower` | 32×48 | 44 | 28–44 | base das torres, todos os níveis |
| `tower_turret` | 20×16 | — (cintura na linha 12) | — | arma + operador sobre o parapeito |
| `build_spot` | 32×32 | 28 | — | ponto de construção vazio |
| `projectile` | 8×8 | — | — | virote, frasco, pena |
| `tile` | 16×16 | — | — | terreno |

Proporção alvo: a unidade pequena tem ~1/3 da altura da torre nível 1.

## 6. Animação

| Tipo | Animações desenhadas | Frames | Duração |
|---|---|---|---|
| Unidades e inimigos | idle, ataque | idle 4; ataque 4–6 | idle 180–260 ms; frame do golpe ~70 ms |
| Torres | idle (bandeira, fumaça, sino) e disparo quando houver peça móvel | 4–6 | 150–250 ms |
| Bosses | idle, ataque, assinatura | 4–8 cada | igual às unidades |

**Procedural (código, sem frames):**
- **Andar:** pulo de 1 px, inclinação ±5°, squash de 10% no pouso, 2 passos por tile; a frequência acompanha a velocidade **atual** (lentidão e congelamento aparecem sozinhos).
- **Morte:** flash branco 60 ms → queda/achatamento 180 ms → fade 200 ms + ~6 partículas.
- **Dano:** hit flash de 60 ms no mesmo shader do recolor.

## 7. Processo

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
    | `hit` | reação a dano, quando for desenhada (o padrão é o hit flash do shader) |
    | `death` | morte desenhada (o padrão é a morte procedural) |
    | `special` | habilidade de boss, especialização ou poder; com sufixo quando houver mais de uma (`special_stun`) |
    | `spawn` | entrada em cena (portal, invocação) |
    | `directions` | projéteis: uma direção por frame, na ordem E, SE, S, SW, W, NW, N, NE |

  - Exemplos: `imp_idle.png`, `imp_attack.png`, `balista_base_lv1_idle.png`, `balista_turret_lv1_attack.png`, `balista_bolt_directions.png`.
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

### Diabrete — v2 (aprovado em 10/11)
- Arquivos: `imp_v2.png` (pose base), `imp_idle.png`, `imp_attack.png`.
- Funcionou: asas de morcego abertas com nervura (a v1 com asa fechada lia como braço), chifres claros, olhos `HELLFIRE`, presa em `EYE_WHITE`, cauda à direita.
- Escala: ~9 px de altura, menor que o soldado — o enxame tem que parecer fraco sozinho.

## 10. Pendências

- **Paletas das regiões 2–4:** Floresta Profana, Picos de Ferro, A Capital.
- **Tileset:** decidir se o terreno será desenhado ou adaptado de pacote comprado (conferir licença comercial).
- **Ícones de itens:** vêm do pacote comprado — definir se ficam como estão ou passam por ajuste de paleta para casar com o jogo.
- **UI:** proposta de estilo (painel de Preparação + HUD) e escolha das fontes.
- **Soldado da Forja nv1 e nv3**, e os operadores das outras torres (Campanário: sineiro; Alquimista: alquimista; Relicário: monge; Falcoaria: falcoeiro).
- **`frame0_luminance_range`:** medir nos primeiros aprovados.

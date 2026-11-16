# TD Crown: regras e números

Regras e números do jogo. Os números ficam nos ScriptableObjects (`CombatConfig`, `TowerDefinition`, `EnemyDefinition`, `LevelDefinition`, `ItemDefinition`, `PowerDefinition`, `CrownTreeDefinition`); ao mudar um deles, atualize este documento junto. O Notion ([🗼 TD](https://app.notion.com/p/TD-414ae533febb802f9441d8f3cc6e0717)) é o caderno de ideias; o que vale para o código é este arquivo.

Unidades: distância em **tiles** (1 tile = 16 px = 1 unidade de mundo), tempo em segundos, velocidade em tiles por segundo. Valores marcados como *provisório* saíram de simulação e ainda precisam de playtest.

## 1. Visão geral

- Tower defense de campanha em pixel art 2D top-down 3/4. O jogador é o **Rei**: constrói torres em pontos fixos, faz upgrade e venda, usa os Poderes da Coroa e chama ondas antes da hora.
- Os demônios andam por caminhos fixos até a saída. Cada um que chega tira vidas; com 0 vidas, a fase está perdida.
- **Sem herói.** O rei não aparece no mapa; age pelos Poderes da Coroa e pelos itens.
- **Pontos de construção fixos**, agrupados em **bastiões**. Labirinto descartado.
- Plataforma: PC / Steam, mouse e teclado. Mobile fica para depois.
- **High concept:** o rei, com o poder da coroa, convoca os ofícios do reino para fechar os portais demoníacos abertos por um sacerdote traidor.
- **Fantasia do jogador:** o rei que segura a última linha e retoma o reino região por região.

### Pilares

Toda mecânica, torre, inimigo ou tela nova passa por estes três. O que não serve a nenhum é candidato a corte; o que contraria um deles precisa de um motivo forte.

| Pilar | O que significa | Serve ao pilar | Vai contra |
|---|---|---|---|
| **Onde e o quê construir é a decisão** | Pontos escassos, papéis claros e torres que se fortalecem pelos bastiões. Errar a composição custa vidas | Dom entre vizinhas, bastiões desenhados por fase, counters legíveis | Torre que serve para tudo, ponto de construção sem consequência, uma composição que vence todas as fases |
| **Cada vitória fortalece o rei** | Toda fase devolve poder à coroa (Selos, itens, poderes), e isso muda *como* se joga | Especializações, itens mecânicos, poderes novos | Nó de árvore que só soma %, grind, recompensa aleatória |
| **A horda muda, você se adapta** | Cada região traz ameaças que quebram a formação anterior, com picos no mini boss e no boss | Inimigo novo com counter claro, boss telegrafado | Inimigo que é só mais vida, chefe que não se entende sem guia |

### Controles

Mouse para tudo. Atalhos (remapeáveis nas Opções, menos o Esc): **1–6** escolhem a torre no ponto selecionado, **Q/E** os poderes, **Espaço** chama a próxima onda, **F** alterna 1x/2x, **Esc/P** pausa.

### Core loop

| Camada | Duração | O que o jogador faz |
|---|---|---|
| Ação | segundos | constrói, faz upgrade e vende, usa poderes, chama a onda antes |
| Fase | 6–12 min | sobrevive a 7–10 ondas gerenciando ouro e vidas |
| Sessão | 30–60 min | escolhe a fase no mapa-múndi, monta itens e poderes na Preparação, vence, ganha Selos e itens |
| Meta | campanha | libera regiões, especializações, poderes e modos difíceis |

## 2. Fase

- **Fluxo:** mapa-múndi → **Preparação** (ameaças da fase, itens, 2 poderes) → fase → vitória ou derrota → Árvore da Coroa.
- **Pontos de construção:** 8–10 na região 1, até 14–18 na região 4, agrupados em bastiões (seção 3.1).
- **Caminhos:** 1 entrada nas fases 1–2, 2 a partir da 3; rotas cruzadas a partir da região 2.
- **Vidas:** 20. Inimigo comum tira 1, grande tira 2–3. Mini boss ou boss que chega à saída = derrota.
- **Ondas:** 7 na fase 1, até 10 na fase de boss da região 1. Timer entre ondas: `waveTimer` = 25 s.
- **Chamar a onda antes:** bônus de ouro = `earlyCallGoldFactor` (0,3) × ouro da próxima onda × (tempo restante ÷ `waveTimer`), e −5 s na recarga dos poderes.
- **Velocidade:** 1x/2x. A pausa permite construir.
- **Estrelas** contam **vidas perdidas**: 3★ perdendo até 2, 2★ até 14, 1★ venceu.
- **Derrota:** mostra a onda alcançada e o inimigo que mais vazou, com uma dica de counter; "Tentar de novo" (mantém o loadout) ou "Mapa". Não rende Selos.
- **Save:** progresso salvo ao concluir a fase; sair no meio perde a fase.

### 2.1 Modos (liberados ao vencer a fase no Normal)

| Modo | Onde | Regras |
|---|---|---|
| **Normal** | todas | as regras acima |
| **Heroico** | todas | ondas mais curtas e mais fortes, **1 vida**; Juramento Antigo e nós de vida da árvore bloqueados |
| **Provação** | só fases de mini boss e boss (8 fases) | par de torres fixo por fase (mostrado na Preparação); sem especializações e **sem itens**; poderes permitidos |

## 3. Torres

Custo do nível é **por upgrade** (não acumulado). Especialização = `specializationCostFactor` (1,35) × custo do upgrade nv3. Venda devolve **60%** do investido.

| Torre (`id`) | Papel | Como funciona | Dom (vizinhas) | Custo nv1/2/3 |
|---|---|---|---|---|
| Balista (`balista`) | perfuração em linha | o virote atravessa todos na linha até o alcance; penetração 50%; cadência lenta; acerta terra e ar | +20% de alcance | 90 / 140 / 200 |
| Forja de Guerra (`forja`) | soldados que bloqueiam | 3 soldados com **Veterania**: +1 patente a cada 5 abates (+vida, +dano), máximo 3; voltam a recruta ao morrer; respawn 10 s | +20% de dano em inimigos engajados por soldados | 70 / 110 / 160 |
| Campanário (`campanario`) | controle | pulso em área a cada 3 s: lentidão; revela camuflados; sem dano | +15% de cadência | 80 / 120 / 180 |
| Alquimista (`alquimista`) | zona e debuff | frasco com dano Físico em área de 1 tile deixa poça por 6 s; dentro dela a Armadura cai 1 faixa; só terra | ataques aplicam Corrosão | 100 / 160 / 230 |
| Relicário (`relicario`) | burst e anti-boss | não ataca; ganha Fé (seção 4.8) e, com a Fé cheia, dispara o Raio Sagrado no inimigo de maior vida | **Bênção:** +15% de dano em inimigos com Res. Sagrada 0 | 120 / 180 / 260 |
| Falcoaria (`falcoaria`) | anti-ar e marcação | 2 falcões caçam o voador ou o mais rápido e o marcam | revelam camuflados no próprio alcance e +15% de dano em voadores | 90 / 140 / 200 |

### 3.1 Bastiões e Dom

- Cada ponto de construção pertence a um bastião de 1 a 3 pontos (visualmente uma plataforma ou muralha comum).
- O **Dom vale por tipo**: a torre recebe o Dom de cada **outro** tipo presente no bastião. Nunca recebe o do próprio tipo, e duas torres iguais não dobram o Dom.
- O Dom vale desde o nível 1, é recalculado ao construir, vender ou especializar, continua ativo com a torre atordoada e só cai se ela for desativada (região 4).
- Especializações mantêm o Dom da torre-base e contam como o mesmo tipo.
- Level design: bastião de 3 no gargalo principal, pontos isolados nas bordas.

**Matriz do Dom** (linha = quem dá, coluna = quem recebe; "sem efeito" aparece em cinza no hover):

| Dom de ↓ / recebe → | Balista | Forja | Campanário | Alquimista | Relicário | Falcoaria |
|---|---|---|---|---|---|---|
| Balista: +20% alcance | — | +20% raio de bloqueio | +20% raio do pulso | +20% alcance | +20% alcance do Raio e da coleta de Fé | +20% alcance |
| Forja: +20% dano em engajados | ✓ | — | sem efeito | ✓ | ✓ no Raio | ✓ |
| Campanário: +15% cadência | ✓ | +15% ataque dos soldados | — | ✓ | −15% Fé exigida | ✓ |
| Alquimista: Corrosão | ✓ | golpes aplicam | pulso aplica em área | — | Raio aplica | ✓ |
| Relicário: Bênção | ✓ | ✓ | sem efeito | ✓ | — | ✓ |
| Falcoaria: revela + 15% em voadores | ✓ | só revela | sem efeito | só revela | ✓ | — |

### 3.2 Números por nível (*provisório*)

Dano / cadência / alcance em tiles. Upgrade rende ~20% menos dano por ouro que torre nova no nv3.

| Torre | nv1 | nv2 | nv3 |
|---|---|---|---|
| Balista | 30 / 2,0 s / 4,0 | 58 / 1,7 s / 4,5 | 90 / 1,6 s / 5,0 |
| Forja (por soldado) | 4 / 1,2 s, vida 40 | 7 / 1,1 s, vida 70 | 11 / 1,0 s, vida 110, Armadura 30% |
| Campanário (pulso fixo a cada 3 s) | lentidão 35% por 1,5 s, raio 2,5 | 42% por 2,0 s, raio 2,75 | 50% por 2,5 s, raio 3,0 |
| Alquimista | 20 / 2,4 s / 3,5 | 45 / 2,3 s / 3,75 | 75 / 2,3 s / 4,0 |
| Relicário | Raio 400, Fé 20, alcance 3,5 | 650, Fé 18, 3,75 | 1000, Fé 15, 4,0 |
| Falcoaria (2 falcões) | 6 / 0,9 s / 5,0 | 12 / 0,85 s / 5,5 | 18 / 0,75 s / 6,0 |

### 3.3 Especializações

Liberadas na Árvore da Coroa; aparecem como evolução da torre nv3 (com cadeado no menu radial enquanto bloqueadas).

| Torre | A | B |
|---|---|---|
| Balista | **Corrente**: prende o 1º inimigo atingido por 1,5 s | **Escorpião**: 2 virotes em leque |
| Forja | **Guarda do Portão**: 2 soldados escudados que puxam inimigos Leves a até 2 tiles | **Penitentes**: 4 soldados frágeis que explodem em luz sagrada (dano Sagrado) ao morrer |
| Campanário | **Bronze**: cada 3º pulso atordoa 1 s | **Sino Fúnebre**: o pulso aplica Silenciado por 3 s |
| Alquimista | **Fogo Grego**: poça incendiária, dano Verdadeiro baixo | **Lodo**: lentidão de 50% na poça |
| Relicário | **Ossário**: guarda até 3 cargas | **Santuário**: o raio consagra o chão por 5 s |
| Falcoaria | **Águias**: agarram e erguem inimigos Leves por 2 s | **Corvos**: bando de 5 que marca vários alvos |

## 4. Combate

### 4.1 Ataque

Ataque é qualquer instância que acerta ou aplica efeito: virote, golpe de soldado, pulso, impacto do frasco, Raio, falcão. Tique de poça e de queimadura **não** é ataque.

### 4.2 Tipos de dano e defesa

- **Físico** (Balista, Forja, Falcoaria, frasco do Alquimista), **Sagrado** (Relicário, Penitentes) e **Verdadeiro** (queimadura, Fogo Grego; ignora defesa).
- Defesa em **faixas fixas** de 0 / 30 / 60 / 90%: Armadura contra Físico, Resistência Sagrada contra Sagrado.
- Redução de faixa (poça, Corrosão): no máximo **−1 faixa no total**, mínimo 0.
- **Penetração** é % sobre a defesa que sobra: Balista 50%, Virote de Prata 75%; o nó Virote Pesado soma +10 pontos (teto 90%).

### 4.3 Ordem de resolução de um acerto

1. Valida o alvo: vivo, terra ou ar conforme a torre, camuflado só se revelado.
2. Dano do pipeline de stats (seção 4.9).
3. +20% se o alvo estiver engajado por soldado e a torre tiver o Dom da Forja.
4. Defesa: faixa efetiva (base − redução, mínimo 0), depois penetração: `defesa × (1 − maior penetração)`, depois `dano × (1 − defesa)`.
5. × (1 + marca + consagração), somados.
6. Aplica o dano.
7. Aplica os status do acerto (valem a partir do próximo acerto).
8. Morte (seção 4.4).

### 4.4 Morte

- Crédito de quem deu o último acerto; numa queimadura, de quem a aplicou.
- Ouro = ouro do inimigo + bônus por abate (Anel, etc.) com teto `maxBonusGoldPerKill` = +1. Invocados (crias da Ninhada, portais do boss) dão **0 ouro**.
- Fé: +1 para cada Relicário com a morte no alcance.
- Veterania: +1 abate para cada soldado engajado com o inimigo.
- Efeito de morte (Ninhada) só se o inimigo **não** estiver Silenciado.

### 4.5 Controle duro

Atordoar, prender, erguer e puxar:

- Não acumulam: vale a maior duração restante.
- Ao terminar, o alvo fica **1 s imune** a controle duro.
- Mini boss e boss sofrem **metade** da duração e são imunes a erguer e puxar.

### 4.6 Peso

- **Leve:** Diabrete, Cão Infernal, Gárgula, Cultista, Xamã.
- **Pesado:** Brutamontes, Ninhada, mini bosses e bosses.
- Águias e Guarda do Portão só agem em Leves. Erguido conta como voador e sai do bloqueio e da poça.

### 4.7 Status

| Status | Fonte | Acúmulo | Mini boss / boss |
|---|---|---|---|
| Lentidão | Campanário, Lodo | vale a maior; teto 50% | metade |
| Atordoamento | Bronze, Elmo do Carrasco, Luz da Coroa | regra 4.5 | metade |
| Marca (+20% dano recebido) | Falcoaria, Corvos | renova | sim |
| Corrosão (−1 faixa de Armadura, 3 s) | Dom do Alquimista | renova; não soma com a poça | sim |
| Queimadura (Verdadeiro, −50% cura recebida) | Fogo Grego, Brasa Aprisionada | vale o maior dano por segundo; renova | sim |
| Consagração (+25% dano recebido) | Santuário | zona; soma com a marca | sim |
| Silenciado (sem efeito de morte e sem habilidade) | Sino Fúnebre | renova | sim |
| Camuflagem | inimigos da região 2+ | revelado por 3,5 s após pulso ou falcão; área acerta sem revelar; soldados não bloqueiam camuflado não revelado | — |

### 4.8 Relicário e Fé

- +1 Fé por inimigo morto no alcance; +1 a cada 3 s com inimigo grande ou boss no alcance.
- Com a Fé cheia, o **Raio Sagrado** é instantâneo e mira o maior HP atual no alcance. Sem alvo, segura a carga. A Fé para no limite (o Ossário guarda até 3 cargas).

### 4.9 Pipeline de stats

Um único pipeline para todo número de torre e unidade, nesta ordem: **base → Árvore da Coroa → item → Dom → buff temporário** (Decreto Real, Estandarte Real). Cada camada calcula `(valor + soma dos fixos) × (1 + soma dos %)`. Item nunca define valor absoluto.

## 5. Inimigos

**Apresentação (decidido em 16/11):** todo inimigo e toda unidade que anda (soldados da Forja e qualquer minion invocado) tem `idle`, `walk` e `attack` desenhados. Não existe andar procedural (o pulo e a inclinação por código saíram): o movimento no caminho é só a posição, e o balanço está nos frames do `walk`. O passo do soldado da Forja foi desenhado para **1,5 tile/s**; a velocidade do soldado ainda não tem número aqui e entra no playtest do vertical slice.

### 5.1 Região 1

| Inimigo (`id`) | Papel | Vida | Velocidade | Defesa | Ouro | Estreia |
|---|---|---|---|---|---|---|
| Diabrete (`diabrete`) | enxame, Leve | 20 | 1,4 tile/s | — | 3 | fase 1 |
| Cão Infernal (`cao_infernal`) | corredor, Leve | 35 | muito rápido | — | 5 | fase 2 |
| Brutamontes (`brutamontes`) | tanque, Pesado | 200 | lento | Armadura 60% | 15 | fase 3 |
| Ninhada (`ninhada`) | ao morrer libera 4 Diabretes 1 tile atrás no caminho; Pesado | 120 | lento | Armadura 30% | 12 | fase 5 |
| Gárgula (`gargula`) | voador, Leve | 40 | médio | — | 8 | fase 6 |

Velocidades "muito rápido / lento / médio" ganham número no primeiro playtest do vertical slice. Referência da arte: o galope do Cão Infernal foi desenhado para **1,9 tile/s** e o passo do Diabrete para **1,4 tile/s** (nessas velocidades os pés não deslizam). O passo do Brutamontes foi desenhado para **0,45 tile/s**. O Animator acompanha qualquer valor, mas acima de ~1,5× a referência o ciclo fica corrido: se o número final passar disso, o ciclo é redesenhado.

**Mini boss, fase 4: Carrasco do Portal (`carrasco`)**

- 1600 de vida, sem armadura, 0,5 tile/s.
- A cada 12 s marca por 1,5 s e depois atordoa por 3 s a torre mais próxima. A distância é medida até o ponto de construção; empate vai para a mais cara.
- Torre atordoada não ataca nem reconstrói soldados; o Relicário continua acumulando Fé.
- Atordoar o Carrasco pausa o timer.

**Boss, fase 7: Senhor da Brasa (`senhor_da_brasa`)**

- 4500 de vida, Armadura 30%, 0,45 tile/s.
- Ao cruzar 50% da vida: fica 1,5 s invulnerável, racha o chão da rota alternativa e abre portais menores que soltam Diabretes (0 ouro) até ele morrer.

Toda habilidade de boss é telegrafada ~1,5 s antes.

### 5.2 Região 2 (já definidos)

- **Cultista Corrompido** (`cultista`): Leve, 50 de vida, Res. Sagrada 60%, 6 de ouro.
- **Xamã Infernal** (`xama`): Leve, 80 de vida, Res. Sagrada 30%, cura aliados próximos; não cura bosses.

## 6. Região 1: introdução e economia

| Fase | Torre nova | Inimigo novo | Mecânica nova | Item (1ª vitória) | Ouro inicial | Ondas |
|---|---|---|---|---|---|---|
| 1 | Balista, Forja | Diabrete | construir e upgrade; Bastião (onda 3); chamar onda (onda 5) | Martelo do Mestre-Ferreiro | 250 | 7 |
| 2 | Campanário | Cão Infernal | Luz da Coroa; Preparação só leitura | Virote de Prata | 280 | 7 |
| 3 | Alquimista | Brutamontes | 2 caminhos; 1ª escolha de item | Badalo Abençoado | 320 | 8 |
| 4 ★ | — | Carrasco do Portal | Estandarte Real | Elmo do Carrasco ★ | 360 | 8 + mini boss |
| 5 | Relicário | Ninhada | 2º slot de item | Frasco sem Fundo | 380 | 9 |
| 6 | Falcoaria | Gárgula | — | Rosário dos Mártires | 400 | 10 |
| 7 ★ | — | Senhor da Brasa | — | Brasa Aprisionada ★ | 450 | 10 + boss |

Uma novidade de inimigo por fase. "Nova ameaça" é um cartão que não bloqueia (pausa automática só nas fases 1–3). A Conselheira fala no máximo uma frase por vez, apontando para o elemento na tela.

### 6.1 Ondas da fase 1

Só Diabretes, caminho de ~40 tiles, 25 s entre ondas.

| Onda | Qtd | Grupos × espaçamento | Ouro | Propósito |
|---|---|---|---|---|
| 1 | 10 | 1 × 1,2 s | 30 | construir |
| 2 | 14 | 2 × 1,0 s | 42 | |
| 3 | 18 | 2 × 0,8 s | 54 | Bastião e 1º upgrade |
| 4 | 24 | 3 × 0,7 s | 72 | |
| 5 | 28 | 2 × 0,5 s (densa) | 84 | mostrar a perfuração; chamar onda |
| 6 | 32 | 4 × 0,6 s | 96 | |
| 7 | 40 | 4 × 0,4 s | 120 | final |

## 7. Árvore da Coroa

- **Moeda: Selos.** 1 por estrela, +1 no Heroico, +1 na Provação. Melhorar a nota paga só a diferença. Máximo de 4 por fase (5 nas de boss) e **120 na campanha**. Não dá para farmar.
- **Estrutura:** 6 ramos de torre (~13 Selos cada) + ramo Geral (~22) = ~100. Poucos nós, cada um forte. Fechar a árvore exige jogar os modos difíceis.
- **Reset gratuito.**
- **Ramo Geral:** +ouro inicial, +1 vida, bônus maior por chamar a onda antes, Decreto Real e Juramento Antigo.
- A 1ª especialização custa 7 Selos e sai por volta da fase 3 (jogador bom) ou 4 (casual). Quando o jogador puder comprá-la, a Conselheira avisa no mapa.

Exemplo, ramo Balista:

| Nó | Custo | Efeito | Requer |
|---|---|---|---|
| Precisão | 2 | +15% dano | — |
| Olho de Vigia | 2 | +15% alcance | Precisão |
| Virote Pesado | 3 | +10 pontos de penetração (teto 90%) | Olho de Vigia |
| Especialização: Corrente | 3 | libera a evolução | Olho de Vigia |
| Especialização: Escorpião | 3 | libera a evolução | Olho de Vigia |

## 8. Poderes da Coroa

Leva **2 poderes** por fase, escolhidos na Preparação. Não ocupam a Capacidade da Coroa.

| Poder (`id`) | Efeito | Recarga | Libera |
|---|---|---|---|
| Luz da Coroa (`luz_da_coroa`) | atordoa todos numa área por 2 s | 45 s | fase 2 |
| Estandarte Real (`estandarte_real`) | planta um estandarte num bastião: os Doms dele valem em dobro por 10 s | 50 s | fase 4 |
| Decreto Real (`decreto_real`) | todas as torres +30% de cadência por 8 s | 60 s | Árvore, ramo Geral |
| Juramento Antigo (`juramento_antigo`) | recupera 3 vidas (até o máximo da fase); 1 uso por fase; bloqueado no Heroico | — | Árvore, ramo Geral |

## 9. Itens Reais

- **Origem:** a 1ª vitória em cada fase entrega um item definido ("O Rei forjou: X"). Mini boss e boss entregam lendários. Sem sorteio e sem moeda nova. 28 itens na campanha, 7 na região 1.
- O item vai para um **tipo de torre**: toda torre daquele tipo na fase recebe o bônus, inclusive especializações.
- **Capacidade da Coroa:** começa em 1; +1 no mini boss da região 1 e em cada boss das regiões 1–3 (5 na região 4).
- Máximo de 1 item por tipo de torre. Item "qualquer" ocupa a vaga do tipo onde for colocado. O item não passa pelo Dom.
- A força cresce com a fase. O efeito é sempre relativo (+%, −N).

| Fase | Item (`id`) | Torre | Efeito |
|---|---|---|---|
| 1 | Martelo do Mestre-Ferreiro (`martelo_ferreiro`) | Forja | soldados nascem com patente 1 |
| 2 | Virote de Prata (`virote_prata`) | Balista | penetração 75% (em vez de 50%) |
| 3 | Badalo Abençoado (`badalo_abencoado`) | Campanário | +20% de cadência do pulso |
| 4 | Elmo do Carrasco ★ (`elmo_carrasco`) | Forja | soldados atordoam 0,5 s a cada 3º golpe |
| 5 | Frasco sem Fundo (`frasco_sem_fundo`) | Alquimista | poças +50% de duração |
| 6 | Rosário dos Mártires (`rosario_martires`) | Relicário | −4 de Fé exigida |
| 7 | Brasa Aprisionada ★ (`brasa_aprisionada`) | qualquer | ataques aplicam Queimadura |

## 10. Narrativa e mundo

### 10.1 Premissa

Há séculos, o primeiro rei selou o mundo dos demônios numa coroa, a **Coroa do Juramento**. Cada rei que a usa renova o selo e mantém o reino em paz.

O Sumo Sacerdote **Orvan**, guardião do rito de coroação, avisou que o selo enfraquecia, mas o rei não ouviu. Orvan buscou magia proibida "para salvar o reino", fez um pacto com **Vael'Khor**, um príncipe demônio, e foi consumido por ele. Agora abre portais pelo reino para cercar a capital e tomar a coroa.

O jogador é o Rei: com o poder da coroa, convoca os ofícios do reino (engenheiros, ferreiros, sineiros, alquimistas, monges e falcoeiros) e forja itens para as tropas.

- **A coroa é o selo.** Destruída, abre o mundo demoníaco de vez. Vael'Khor quer a coroa quebrada; Orvan acha que vai reinar, mas é só a chave.
- **Clero dividido:** os Cultistas são sacerdotes que seguiram Orvan (por isso resistem a dano Sagrado); os monges do Relicário ficaram fiéis ao rei.
- **Selos:** cada vitória devolve fragmentos do selo à coroa.

### 10.2 Campanha

4 regiões × 7 fases = **28 fases**. Mini boss na fase 4, boss na fase 7. Contraofensiva e volta para a capital.

| Região | História | Novidade de jogo | Mini boss | Boss |
|---|---|---|---|---|
| 1. Vale do Reino | o rei sai da capital para fechar o primeiro portal | 1–2 caminhos, tutorial | Carrasco do Portal | Senhor da Brasa |
| 2. Floresta Profana | portal no bosque sagrado; a traição veio do clero | voadores em massa, camuflados, rotas cruzadas | Inquisidor Caído | Mãe da Ninhada |
| 3. Picos de Ferro | nas minas da coroa, os diários de Orvan: o demônio quer a coroa quebrada | armadura alta, escavadores que pulam trechos, pontos elevados (+alcance) | Capataz Possuído | Golem Profanado |
| 4. A Capital | Orvan abre o Grande Portal dentro dos muros | distritos da cidade, 3 entradas, inimigos que desativam torres | Orvan, fundindo-se ao demônio | Vael'Khor |

### 10.3 Como a história aparece

- Abertura: 5–6 telas estáticas em pixel art com texto. Final: 3–4 telas.
- **Conselheira do rei:** 1–2 falas no mapa-múndi antes de cada fase; também ensina nas fases tutoriais.
- Tela de apresentação de cada boss.
- Bestiário com 1–2 linhas de lore por inimigo.
- ~60 falas curtas + bestiário, todo texto em tabelas de localização.

## 11. Alvos de balanceamento

| Alvo | Valor |
|---|---|
| Fase 1 | 250 de ouro pagam Balista + Forja + Balista na hora; com 2 tipos de torre termina com 18–20 vidas; com uma Balista só, perde; 4,5–6 min |
| Duração de fase | 6–12 min a partir da fase 3 |
| Mini boss e boss | vida ≈ 65–75% do dano que a build esperada causa nele |
| 1ª especialização | fase 3 (jogador bom) ou 4 (casual) |
| Selos | ~25–30 na região 1 completa; árvore inteira só com modos difíceis |
| Torre dominante | nenhuma composição de um tipo só vence uma fase a partir da 2 no Normal |
| Bônus por chamar onda | 10–20% da renda da fase |

Mudança em número de combate passa pela ferramenta de balanceamento (ver ARQUITETURA) antes de ir para a build.

## 12. UX e feedback

- **HUD:** vidas e ouro (canto superior esquerdo), onda X/Y (centro), 1x/2x e pausa (canto superior direito), 2 poderes com recarga radial e atalho (embaixo). Botão de chamar onda na entrada do caminho, com prévia dos inimigos e do bônus.
- **Menu radial:** custo, diferença de stats no upgrade, venda (60%); no nv3 a especialização aparece com cadeado "Árvore da Coroa" se ainda bloqueada.
- **Dom visível:** linhas finas entre as torres do bastião, ícone do Dom recebido em cada torre e, no hover de ponto vazio, o que o bastião ganharia.
- **Status:** um ícone e uma forma por status, no máximo 2 ícones sobre a barra; zonas no chão com padrão próprio.
- **Defesa:** 0–3 pips por inimigo (escudo = Armadura, auréola = Res. Sagrada); golpe muito reduzido dá um "clink" visual e sonoro.
- **Daltonismo:** time nunca indicado só por cor (barra de vida do jogador com ponta de escudo, preset de recolor para daltonismo).
- **Acessibilidade:** texto em 100/125/150%, remapeamento, reduzir flashes, desligar tremor de tela, velocidade 0,75x, pausar ao perder o foco.
- **Glossário** com tooltip para Dom, Bastião, Fé, Armadura e Selo.

## 13. Escopo

| Marco | Conteúdo |
|---|---|
| Vertical slice | fases 1–3 da região 1: Balista, Forja, Campanário e Alquimista; Diabrete, Cão Infernal e Brutamontes; bastiões de 2 |
| Demo interna | região 1 completa: 7 fases, 6 torres, 5 inimigos, mini boss, boss, 7 itens, 2 poderes |
| Demo pública (Steam) | fases 1–3 (o mesmo conteúdo do vertical slice), com o Bastião logo na fase 1 |
| 1.0 | 28 fases, 6 torres + 12 especializações, ~20 inimigos, 4 mini bosses, 4 bosses, 28 itens, 4 poderes, Provação em 8 fases |

Primeiro corte se apertar: as especializações mais caras (Águias, Guarda do Portão). A Falcoaria fica: a região 2 depende dela contra voadores.

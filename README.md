# TD Crown (nome provisório)

Tower defense medieval em pixel art 2D top-down 3/4: o rei, com o poder da coroa, convoca os ofícios do reino para fechar os portais demoníacos abertos por um sacerdote traidor.

- **Engine:** Unity 6, URP 2D, UI Toolkit
- **Plataforma:** PC / Steam
- **GDD:** [Notion — 🗼 TD](https://app.notion.com/p/TD-414ae533febb802f9441d8f3cc6e0717)
- **Art Bible:** [`docs/ART_BIBLE.md`](docs/ART_BIBLE.md) + [`docs/art-style.json`](docs/art-style.json)

## Documentos

- [`CLAUDE.md`](CLAUDE.md): onde está a verdade, regras do projeto e convenções.
- [`docs/GDD.md`](docs/GDD.md): regras e números.
- [`docs/ARQUITETURA.md`](docs/ARQUITETURA.md): decisões técnicas, pastas, assemblies e onde fica cada parte.
- [`docs/PLANO.md`](docs/PLANO.md): fases, checklists, decisões e riscos.
- [`docs/ART_BIBLE.md`](docs/ART_BIBLE.md): estilo e entrega dos sprites.

## Arte

Torres e unidades do jogador são desenhadas em **cinza indexado** (8 níveis) e recoloridas por shader: só pixels de cinza neutro trocam de cor; madeira, pedra, ferro e pele passam direto. Torre = base fixa (32×48, não espelha) + arma com operador (20×16, vira com flipX).

Para regenerar um asset:

```
cd ArtSource
pip install pillow
python balista.py
```

Os scripts gravam os sheets direto em `Assets/_Project/Art/{categoria}/{Asset}/` e registram cada um no `Assets/_Project/Art/art-manifest.json` (tamanho do frame, pivô, durações, loop, frame de impacto). Previews (GIFs, lineups) ficam em `ArtSource/`, ignorados pelo git.

**Um arquivo por animação:** `{asset_id}_{animação}.png` com os frames numa linha (`imp_idle.png`, `balista_turret_lv1_attack.png`). Nomes de animação permitidos e regras completas na Art Bible §8.

### Animações na Unity

Depois de rodar um script de arte, use **TD Crown → Arte → Gerar animações**. O menu:

- fatia cada sheet do manifesto (pivô no chão do personagem ou na cintura da besta);
- cria um clip por arquivo (`Assets/_Project/Animation/{categoria}/{asset_id}/{asset_id}_{animação}.anim`) com a duração de cada frame;
- cria um override por asset (`{asset_id}.overrideController`) sobre os controllers base `Unit`, `TowerTurret` e `TowerBase`.

Rodar de novo atualiza tudo no lugar, sem perder referências. O relatório no Console mostra o `attackWindup` de cada ataque e a âncora da besta em cada base de torre.

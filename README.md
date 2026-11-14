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

Os spritesheets gerados saem em `ArtSource/` (ignorados pelo git); copie o final para `Assets/_Project/Art/`.

**Um arquivo por animação:** `{asset_id}_{animação}.png` com os frames numa linha (`imp_idle.png`, `balista_turret_lv1_attack.png`). Nomes de animação permitidos e regras completas na Art Bible §8.

### Fatiamento na Unity

O `PixelArtImportPostprocessor` aplica as configurações de import na primeira importação. O slice é feito no Sprite Editor → **Grid By Cell Size**, pivô **Bottom Center**:

| Sheet | Célula |
|---|---|
| unidades e inimigos pequenos | 16×16 |
| base de torre | 32×48 |
| arma + operador da torre | 20×16 |
| projétil | 8×8 |

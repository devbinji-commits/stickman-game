# Stickman Arena — Ursina

Un jeu de combat local en 2.5D avec deux personnages stickman articulés, des coups, un saut, un blocage, une IA adverse et des barres de vie. Le jeu est construit en 3D avec Ursina, sans Pygame et sans images externes.

![Aperçu des stickmen bleu et rouge dans l'arène](https://raw.githubusercontent.com/devbinji-commits/stickman-game/main/assets/stickmen-preview.svg)

## Installation et lancement

Prérequis : Python 3.9 ou plus récent.

```bash
python -m pip install -r requirements.txt
python main.py
```

## Commandes

- **A / D** ou **← / →** : se déplacer
- **Espace** : sauter
- **J** ou **F** : frapper
- **K** ou **Maj** : bloquer (maintenir)
- **Échap** : quitter

Les personnages ont une tête expressive, un bandeau, un haut coloré, des gants, des articulations et des bottes. Après une victoire ou une défaite, le round suivant démarre automatiquement.

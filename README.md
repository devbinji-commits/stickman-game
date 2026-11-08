# Stickman Arena — Ursina

Un petit jeu de combat local en 2.5D fait avec **Ursina**. Deux personnages stickman articulés (tête, bras, jambes, vêtements et visage) se battent dans une arène. L'adversaire est contrôlé par une IA simple. Le projet n'utilise **pas Pygame** et ne nécessite aucune image externe.

## Installation

Prérequis : Python 3.9 ou plus récent.

```bash
python -m pip install -r requirements.txt
python main.py
```

## Commandes

- **A / D** ou **← / →** : se déplacer
- **Espace** : sauter
- **J** ou **F** : frapper
- **K** ou **Maj** : bloquer
- **Échap** : quitter

Les barres de vie indiquent l'état des combattants. Après une victoire ou une défaite, le round suivant démarre automatiquement.

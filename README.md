# Stickman Run — Ursina

Petit jeu de course 3D où le stickman doit éviter les obstacles en changeant de voie ou en sautant. Le projet utilise **Ursina uniquement** pour le jeu : aucune dépendance à Pygame.

## Prérequis

- Python 3.9 ou plus récent
- Une machine compatible avec Ursina/Panda3D

## Installation et lancement

```bash
python -m pip install -r requirements.txt
python main.py
```

## Commandes

- **← / →** ou **A / D** : changer de voie
- **Espace**, **↑** ou **W** : sauter
- **Échap** : quitter

Le score augmente avec le temps, la vitesse augmente progressivement et le meilleur score est enregistré dans `save.json`.

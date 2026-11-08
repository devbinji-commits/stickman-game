# Stickman Arena — Ursina

Jeu de combat local en 2.5D, avec des combattants cartoon originaux aux formes rondes et aux couleurs vives. Le parcours de jeu comprend un écran d'accueil, le choix **Solo contre l'ordinateur** ou **Duo local**, la sélection des couleurs, puis le combat avec points et barres de vie. Le style est inspiré des jeux de party cartoon, sans reprendre leurs personnages ou leurs images.

![Aperçu du menu et des combattants](https://raw.githubusercontent.com/devbinji-commits/stickman-game/main/assets/stickmen-preview.svg)

## Installation et lancement

Python 3.9 ou plus récent :

```bash
python -m pip install -r requirements.txt
python main.py
```

## Parcours et commandes

1. Clique sur **Jouer**.
2. Choisis **Solo** contre l'ordinateur ou **Duo** sur le même clavier.
3. Choisis la couleur de chaque personnage avec les flèches, puis clique sur **Combattre !**.
4. Gagne des points en mettant l'adversaire K.-O. ; le round suivant redémarre automatiquement.

### Joueur 1
- **A / D** : bouger
- **W** : sauter
- **F** : frapper
- **G** : bloquer (maintenir)

### Joueur 2 en mode Duo
- **← / →** : bouger
- **↑** : sauter
- **/** : frapper
- **Maj droite** : bloquer (maintenir)

**Échap** revient au menu pendant un combat et quitte le jeu depuis les menus.

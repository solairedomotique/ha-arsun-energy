# ARSUN Energy v0.4.2

## Modifications
- `-` et `---` ont désormais exactement le même traitement : chauffe-eau à l'arrêt, 0 W comptabilisé.
- `OFF` correspond également à une sortie non alimentée : 0 W.
- En `H` ou `P`, l'importation EDF est comparée à la puissance totale des sorties forcées.
- La part EDF est répartie proportionnellement entre les sorties forcées. Le reste de leur puissance est attribué au solaire.
- Les quatre compteurs kWh continuent d'être alimentés séparément : sortie 1 solaire/réseau et sortie 2 solaire/réseau.
- `ON` reste 100 % solaire.
- Aucun changement des identifiants uniques des capteurs existants.

## Exemple
Sortie 1 = 1 000 W, sortie 2 = 500 W, import EDF = 600 W :
- Sortie 1 : 400 W réseau + 600 W solaire.
- Sortie 2 : 200 W réseau + 300 W solaire.

## Publication
Remplacer les fichiers du dépôt par ceux de cette archive, publier le tag `v042`, puis installer la mise à jour depuis Home Assistant Marketplace et redémarrer Home Assistant.

**Validation :** la syntaxe Python et les fichiers JSON doivent être vérifiés avant publication. Le fonctionnement doit ensuite être confirmé sur une instance Home Assistant réelle.

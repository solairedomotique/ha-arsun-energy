# ARSUN Energy v0.4.0

## Nouveautés

- Détection automatique des entités ARSUN à partir de leur identifiant et de leur nom convivial.
- Affichage des entités proposées et de leurs valeurs actuelles avant validation.
- Possibilité de modifier chaque proposition ou de configurer toutes les sources manuellement.
- Sortie 2 et état LED du canal 2 facultatifs.
- Calculs et capteurs basés sur les entités sources choisies, quel que soit leur préfixe.
- Conservation de la logique de répartition solaire / réseau et des modes forcés `H` et `P`.
- Compatibilité conservée avec les anciennes configurations utilisant les entités historiques par défaut.

## Installation / mise à jour

Installer ARSUN Energy depuis Home Assistant Marketplace, puis redémarrer Home Assistant. Lors de la première configuration en 0.4.0, vérifier les entités proposées et leurs valeurs avant de valider.

## À savoir

La détection automatique repose sur les identifiants et noms conviviaux. Elle fournit des suggestions qui doivent être vérifiées. En mode forcé, la répartition entre solaire et réseau reste une estimation basée sur le bilan réseau global.

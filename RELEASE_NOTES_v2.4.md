# ARSUN Energy 2.4

## Compteurs énergétiques persistants
- Les deux compteurs EDF et les quatre compteurs cumulus enregistrent désormais leur total dans le stockage persistant de Home Assistant.
- La clé de stockage repose sur les entités sources configurées et le compteur, pas sur l'ID aléatoire de l'entrée.
- Une désinstallation/réinstallation avec les mêmes entités sources retrouve les totaux précédents.
- La valeur restaurée en kWh n'est plus écrasée par la méthode de mise à jour de puissance instantanée en W.
- Les valeurs continuent à être cumulées par intégration trapézoïdale de la puissance.

## Important
Le stockage persistant est conservé dans le dossier `.storage` de Home Assistant. Ne pas supprimer les fichiers de stockage ARSUN ni restaurer un backup antérieur si l'objectif est de conserver les compteurs.

## Correctif complémentaire
- Ajout de l'entité batterie ARSUN dans les entités par défaut. Cela évite une erreur `KeyError` au démarrage lors de la mise à jour d'anciennes configurations qui ne contiennent pas encore la clé `battery_sensor`.
- Version du micrologiciel affichée dans Home Assistant harmonisée sur `2.4`.

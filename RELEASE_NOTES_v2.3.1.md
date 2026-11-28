# ARSUN Energy v2.3.1

## Correction
Le journal Home Assistant a révélé une erreur bloquante dans `__init__.py` :
`NameError: name 'async_reload_entry' is not defined`.

La fonction de rechargement manquante a été ajoutée. Elle permet à Home Assistant de recharger l'intégration lorsque ses options sont modifiées.

## Version
- Version affichée dans la fiche appareil : 2.3.1
- Version du manifest : 2.3.1
- URL « Visiter » conservée : https://solaire-domotique.fr/ha/github/arsun/

Aucun calcul énergétique ni nom de capteur n'a été volontairement modifié.

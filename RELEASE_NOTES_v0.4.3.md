# ARSUN Energy v0.4.3

## Amélioration de la détection automatique
- Analyse combinée de l'Entity ID et du nom convivial (`friendly_name`).
- Pour les capteurs de puissance, vérification de l'unité W/kW et priorité à `device_class: power`.
- Reconnaissance des sorties 1 et 2 ainsi que des LED S1/S2 par leur nom de canal, sans dépendre du préfixe d'entité.
- Les valeurs LED inconnues, notamment `N`, ne sont pas interprétées et ne font pas échouer la détection par nom.
- L'aperçu affiche maintenant la valeur, l'unité, la classe d'appareil et un score de correspondance.
- La puissance batterie devient une source facultative configurable ; elle reste affichée simplement, sans calcul énergétique.

## Préservation
- Configuration manuelle toujours disponible.
- Sortie 2, LED 2 et batterie facultatives.
- Les calculs énergétiques de la V0.4.2 sont conservés.
- Les noms et identifiants uniques des capteurs existants sont conservés.

## Publication
Remplacer les fichiers du dépôt par ceux de cette archive, publier le tag `v043`, puis installer la mise à jour depuis Home Assistant Marketplace et redémarrer Home Assistant.

**Validation :** syntaxe Python et JSON vérifiés. À tester sur une instance Home Assistant réelle avant publication.

# ARSUN Energy – Home Assistant

Intégration personnalisée Home Assistant pour exploiter le capteur de puissance instantanée du routeur ARSUN et distinguer le soutirage réseau de l'injection.

> Projet communautaire indépendant réalisé par **Solaire Domotique**. Il ne s'agit pas d'une intégration officielle ARSUN.

## Fonctionnalités

- Configuration depuis l'interface Home Assistant, sans modifier `configuration.yaml`.
- Sélection du capteur source, avec `sensor.arsun_routeur_injection_soutirage` proposé par défaut.
- Exposition de la valeur ARSUN originale, avec son signe conservé.
- Exposition d’un capteur dédié à la jauge, conservant le signe ARSUN pour afficher les valeurs négatives et positives.
- Séparation de la puissance instantanée de soutirage et d'injection.
- Deux compteurs d'énergie cumulée en kWh : soutirage et injection.
- Restauration des compteurs après redémarrage de Home Assistant.

## Convention de signe ARSUN

Cette intégration applique la convention confirmée pour le capteur ARSUN utilisé :

| Valeur source | Signification | Capteur séparé |
|---|---|---|
| Positive | Soutirage / consommation depuis EDF | Puissance soutirée |
| Négative | Injection vers le réseau | Puissance injectée |
| Zéro | Équilibre | 0 W des deux côtés |

La valeur originale reste disponible sans inversion. Le capteur « Puissance jauge » conserve lui aussi le signe ARSUN : négatif pour l’injection, positif pour le soutirage.

## Entités créées

- **Puissance réseau (origine)** : valeur signée originale en W.
- **Puissance jauge** : valeur signée en W, négative en injection et positive en soutirage.
- **Puissance soutirée** : puissance positive uniquement lorsque le réseau alimente l'installation.
- **Puissance injectée** : puissance positive uniquement lorsque l'installation injecte vers le réseau.
- **Énergie soutirée** : compteur cumulatif en kWh, restauré après redémarrage.
- **Énergie injectée** : compteur cumulatif en kWh, restauré après redémarrage.

Les identifiants d'entités définitifs sont attribués par Home Assistant et peuvent dépendre du nom choisi lors de l'installation.

## Installation via HACS

Après publication du dépôt sur GitHub :

1. Ouvrir **HACS → Marketplace**.
2. Ouvrir le menu ⋮ puis **Ajouter depuis un lien**.
3. Ajouter `https://github.com/solairedomotique/ha-arsun-energy` et choisir **Intégration** si demandé.
4. Rechercher **ARSUN Energy**, puis installer l'intégration.
5. Redémarrer Home Assistant.
6. Aller dans **Paramètres → Appareils et services → Ajouter une intégration**.
7. Rechercher **ARSUN Energy** et sélectionner le capteur source.

## Installation manuelle

1. Copier `custom_components/arsun_energy` dans `/config/custom_components/arsun_energy`.
2. Redémarrer Home Assistant.
3. Ajouter l'intégration depuis **Paramètres → Appareils et services**.

## Compteurs d'énergie : méthode et limites

Les compteurs sont calculés à partir des changements d'état du capteur source, par intégration trapézoïdale de la puissance instantanée. Leur valeur est restaurée après un redémarrage de Home Assistant.

L'énergie consommée pendant une période où Home Assistant est arrêté ou où le capteur ne fournit pas de mesure n'est pas reconstituée. La précision dépend donc de la fréquence de mise à jour du capteur ARSUN.

## Carte jauge Lovelace

Exemple à adapter à l'identifiant attribué au capteur :

```yaml
type: gauge
entity: sensor.arsun_energy_puissance_jauge
name: ARSUN Injection / Soutirage
min: -6000
max: 6000
needle: true
unit: W
severity:
  green: -6000
  yellow: 0
  red: 2500
```

Le capteur conserve le signe ARSUN : injection à gauche (négatif, vert) et soutirage à droite (positif, rouge). Dans l'éditeur visuel de la carte Jauge, sélectionne cette entité et règle les limites minimale et maximale selon la puissance de l'installation. Aucun capteur Template ni modification de `configuration.yaml` n'est nécessaire.

## Informations techniques

- Domaine : `arsun_energy`
- Version : `0.1.3`
- Plateforme : Home Assistant – Sensor
- Configuration : UI (Config Flow)
- Dépendances Python externes : aucune

## Support et contributions

Les retours, demandes d'évolution et rapports de bugs sont les bienvenus via les Issues GitHub du dépôt.

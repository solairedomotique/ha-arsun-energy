# ARSUN Energy

Intégration personnalisée **Home Assistant** pour le routeur ARSUN, développée par **Solaire Domotique**.

- Dépôt : https://github.com/solairedomotique/ha-arsun-energy
- Installation : Home Assistant Marketplace (HACS)
- Version : **0.4.0**

## Fonctionnalités

- Suivi de la puissance réseau ARSUN avec conservation du signe d'origine.
- Séparation de la puissance importée depuis EDF et de la puissance injectée vers EDF.
- Mesure instantanée des sorties cumulus 1 et 2.
- États de fonctionnement lisibles des canaux ARSUN.
- Détection des modes forcés `H` et `P`.
- Estimation de la part solaire et de la part réseau des cumulus.
- Compteurs d'énergie cumulatifs restaurés après redémarrage et compatibles avec le tableau de bord Énergie de Home Assistant.
- Détection automatique des entités avec propositions modifiables, ou configuration entièrement manuelle.
- Sortie 2 et LED 2 facultatives.

## Installation via Home Assistant Marketplace

1. Ouvrir **Marketplace** dans Home Assistant.
2. Ouvrir le menu `⋮` puis choisir l'ajout d'un dépôt personnalisé.
3. Ajouter : `https://github.com/solairedomotique/ha-arsun-energy`
4. Rechercher **ARSUN Energy**, puis installer l'intégration.
5. Redémarrer Home Assistant.
6. Ajouter l'intégration **ARSUN Energy** depuis Paramètres → Appareils et services.
7. Choisir la détection automatique ou la configuration manuelle.
8. Vérifier les entités proposées et leurs valeurs avant de valider.

La détection automatique s'appuie sur les identifiants et noms conviviaux des entités. Elle propose des correspondances : elle ne peut pas garantir seule qu'une entité est la bonne. Vérifier les valeurs avant validation. Si nécessaire, sélectionner manuellement les capteurs exacts.

## Configuration des sources

Les sources configurables sont :

| Source | Obligatoire | Unité / état attendu |
|---|---:|---|
| Puissance réseau injection/soutirage | Oui | W ou kW, négatif = import EDF, positif = injection |
| Puissance sortie 1 | Oui | W ou kW |
| État LED canal 1 | Oui | `H`, `P`, `---`, `ON` ou `OFF` |
| Puissance sortie 2 | Non | W ou kW |
| État LED canal 2 | Non | `H`, `P`, `---`, `ON` ou `OFF` |

Les noms et préfixes des entités peuvent varier d'une installation à l'autre. C'est pour cela que la version 0.4.0 permet de choisir les entités sources au lieu de dépendre d'un préfixe fixe.

## Convention de signe du réseau

Le capteur réseau ARSUN conserve sa convention d'origine :

- Valeur **négative** : consommation / soutirage depuis EDF.
- Valeur **positive** : injection / énergie renvoyée vers EDF.

Le capteur « Puissance jauge » conserve également ce signe : positif = injection EDF, négatif = consommation EDF.

## États des canaux ARSUN

| État ARSUN | Libellé affiché | Traitement |
|---|---|---|
| `H` | Forcé H1H2 | Mode forcé |
| `P` | Programme Horaire | Mode forcé |
| `---` | Automatique en attente de surplus | Mode automatique |
| `ON` | Surplus alimentant le chauffe-eau | Mode automatique |
| `OFF` | Sortie non alimentée | Mode automatique |

Les états `H` et `P` activent tous les deux les indicateurs binaires « Marche forcée » et la logique de répartition estimative entre solaire et réseau.

## Répartition énergétique des cumulus

En fonctionnement automatique (aucun canal en `H` ou `P`), la puissance mesurée sur les sorties est comptabilisée comme solaire, conformément à la convention retenue pour cette intégration.

Dès qu'au moins un canal est en mode `H` ou `P` :

1. L'import EDF est calculé à partir de la valeur négative du capteur réseau.
2. Cet import est plafonné à la puissance totale mesurée sur les sorties cumulus.
3. La part réseau est répartie proportionnellement entre les sorties selon leurs puissances instantanées.
4. Le complément de chaque sortie est comptabilisé comme solaire.

Exemple : sortie 1 à 1 500 W, sortie 2 à 1 000 W et import EDF mesuré à 800 W : 480 W sont attribués au réseau pour la sortie 1 et 320 W pour la sortie 2. Le reste est attribué au solaire.

### Limite de précision

Le capteur injection/soutirage mesure le bilan réseau global de l'installation, et non l'alimentation dédiée des cumulus. En mode forcé, la répartition proportionnelle constitue donc une **estimation** : les autres consommations de la maison peuvent influencer le résultat. Une mesure dédiée à chaque cumulus serait nécessaire pour obtenir une attribution exacte.

## Capteurs créés

L'intégration expose notamment :

- Puissance réseau d'origine (W).
- Puissance consommée EDF et puissance redonnée à EDF (W).
- Puissance jauge bidirectionnelle (W).
- Puissance cumulus sortie 1 et sortie 2 (W).
- Mode canal 1 et mode canal 2.
- Marche forcée canal 1 et canal 2.
- Énergie consommée EDF et énergie redonnée à EDF (kWh).
- Cumulus sortie 1 solaire / réseau (kWh).
- Cumulus sortie 2 solaire / réseau (kWh).

Les compteurs d'énergie utilisent `device_class: energy`, `state_class: total_increasing` et l'unité `kWh`. Ils restaurent leur valeur après redémarrage.

## Mise à jour

Pour mettre à jour l'intégration depuis Marketplace, installer la nouvelle version proposée puis redémarrer Home Assistant.

Les installations antérieures à la 0.4.0 conservent leurs entités sources historiques par défaut. La nouvelle configuration des sources peut être utilisée pour sélectionner des entités différentes.

## Dépannage

- **Une mauvaise entité est proposée :** modifier la sélection dans le formulaire avant validation ou utiliser le mode manuel.
- **Aucune entité n'est détectée :** sélectionner les entités manuellement.
- **Une puissance reste à zéro :** vérifier l'entité source, son état et son unité (`W` ou `kW`).
- **Les compteurs ne correspondent pas à une mesure dédiée :** consulter la limite de précision décrite plus haut.

## Historique des versions

Voir [CHANGELOG.md](CHANGELOG.md) et les [versions publiées](https://github.com/solairedomotique/ha-arsun-energy/releases).

## Licence

Projet distribué sous licence MIT. Voir [LICENSE](LICENSE).

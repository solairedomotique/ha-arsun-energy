# ARSUN Energy

Intégration personnalisée **Home Assistant** pour le routeur ARSUN.

## 🤝 Les partenaires du projet

ARSUN Energy est développé dans le cadre d'un partenariat réunissant **Solaire Domotique**, le concepteur du routeur **ARSUN** et la société **SOSUNELEC**.

Les logos ci-dessous sont chargés directement depuis le site Solaire Domotique. Ils sont affichés dans des emplacements à hauteur limitée : si un logo est remplacé sur le FTP en conservant la même URL, le README utilisera automatiquement la nouvelle image sans modification du dépôt.

<table>
  <tr>
    <td align="center" valign="middle">
      <a href="https://arsun-concept.com/">
        <img src="https://solaire-domotique.fr/ha/github/logo/arsun.png" alt="ARSUN" height="80" />
      </a>
      <br />
      <strong>ARSUN</strong>
      <br />
      <sub>Concepteur du routeur</sub>
    </td>
    <td align="center" valign="middle">
      <a href="https://sosunelec.com/">
        <img src="https://solaire-domotique.fr/ha/github/logo/logo-sosunelec.png" alt="SOSUNELEC" height="80" />
      </a>
      <br />
      <strong>SOSUNELEC</strong>
      <br />
      <sub>Partenaire du projet</sub>
    </td>
    <td align="center" valign="middle">
      <a href="https://solaire-domotique.fr/">
        <img src="https://solaire-domotique.fr/ha/github/logo/solaire-domotique.png" alt="Solaire Domotique" height="80" />
      </a>
      <br />
      <strong>Solaire Domotique</strong>
      <br />
      <sub>Site web et développement de l'intégration</sub>
      <br />
      <a href="https://www.youtube.com/@solairedomotique">Chaîne YouTube</a>
    </td>
  </tr>
</table>

Ce partenariat associe la conception du routeur ARSUN, l'expertise de SOSUNELEC et le développement ainsi que le partage communautaire assurés par Solaire Domotique.


- Dépôt : https://github.com/solairedomotique/ha-arsun-energy
- Installation : Home Assistant Marketplace (HACS)
- Version : **2.4**

## Fonctionnalités

- Suivi de la puissance réseau ARSUN avec conservation du signe d'origine.
- Séparation de la puissance importée depuis EDF et de la puissance injectée vers EDF.
- Mesure instantanée des sorties cumulus 1 et 2.
- Affichage de la puissance instantanée de la batterie ARSUN (lecture seule, sans traitement énergétique), avec source configurable.
- États de fonctionnement lisibles des canaux ARSUN.
- Détection des modes forcés `H` et `P`.
- Estimation de la part solaire et de la part réseau des cumulus.
- Compteurs d'énergie cumulatifs restaurés après redémarrage et compatibles avec le tableau de bord Énergie de Home Assistant.
- Détection automatique améliorée : analyse des noms, friendly_name, unités et device_class, avec propositions modifiables et configuration manuelle.
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

La détection automatique classe les capteurs en analysant l'Entity ID, le nom convivial (`friendly_name`), l'unité et la classe d'appareil (`device_class`). Pour les puissances, elle privilégie les capteurs en W/kW et de classe `power`. Pour les LED, elle privilégie les noms propres à chaque canal. Une valeur LED inconnue (par exemple `N`) n'est ni interprétée ni rejetée : la correspondance est proposée sur la base du nom, et l'état reste visible pour vérification. Vérifier les valeurs avant validation. Si nécessaire, sélectionner manuellement les capteurs exacts.

## Configuration des sources

Les sources configurables sont :

| Source | Obligatoire | Unité / état attendu |
|---|---:|---|
| Puissance réseau injection/soutirage | Oui | W ou kW, négatif = import EDF, positif = injection |
| Puissance sortie 1 | Oui | W ou kW |
| État LED canal 1 | Oui | `H`, `P`, `---`, `ON`, `-` ou `OFF` |
| Puissance sortie 2 | Non | W ou kW |
| État LED canal 2 | Non | États LED affichés sans interpréter les valeurs inconnues |
| Puissance batterie | Non | W ou kW |

Les noms et préfixes des entités peuvent varier d'une installation à l'autre. C'est pour cela que la version 0.4.0 permet de choisir les entités sources au lieu de dépendre d'un préfixe fixe.

## Convention de signe du réseau

Le capteur réseau ARSUN conserve sa convention d'origine :

- Valeur **négative** : consommation / soutirage depuis EDF.
- Valeur **positive** : injection / énergie renvoyée vers EDF.

Le capteur « Puissance jauge » conserve également ce signe : positif = injection EDF, négatif = consommation EDF.

## États des canaux ARSUN

| État ARSUN | Libellé affiché | Traitement énergétique |
|---|---|---|
| `H` | Forcé H1H2 | Répartition estimative entre solaire et EDF |
| `P` | Programme Horaire | Même calcul que H |
| `ON` | Surplus alimentant le chauffe-eau | 100 % solaire |
| `-` | Arrêt du chauffe-eau | 0 W comptabilisé |
| `---` | Arrêt / attente de surplus | Même traitement que `-` : 0 W |
| `OFF` | Sortie non alimentée | 0 W comptabilisé |

Les états `H` et `P` activent tous les deux les indicateurs binaires « Marche forcée ». Les états `-`, `---` et `OFF` sont considérés comme un arrêt de la sortie. Un canal en `ON` est considéré comme alimenté à 100 % par le surplus solaire.

## Répartition énergétique des cumulus

Lorsque les deux canaux sont en fonctionnement forcé (`H` ou `P`), la puissance mesurée sur les sorties forcées est comparée à la puissance importée depuis EDF.

1. L'import EDF est calculé à partir de la valeur négative du capteur réseau.
2. La part EDF attribuée aux cumulus est plafonnée à la puissance totale mesurée des sorties en `H` ou `P`.
3. Cette part EDF est répartie proportionnellement à la puissance mesurée de chaque sortie forcée.
4. Pour chaque sortie forcée, la différence entre sa puissance mesurée et sa part EDF est comptabilisée comme solaire.
5. Les sorties en `ON` restent 100 % solaires ; les sorties en `-`, `---` ou `OFF` sont comptabilisées à 0 W.

Exemple avec deux sorties forcées :
- Sortie 1 : 1 000 W
- Sortie 2 : 500 W
- Puissance totale des cumulus : 1 500 W
- Import EDF : 600 W

Répartition :
- Sortie 1 : 400 W réseau et 600 W solaire.
- Sortie 2 : 200 W réseau et 300 W solaire.

Les quatre compteurs correspondants sont incrémentés en kWh : sortie 1 solaire, sortie 1 réseau, sortie 2 solaire et sortie 2 réseau. Si l'import EDF dépasse la puissance totale des sorties forcées, toute leur puissance est attribuée au réseau et leur part solaire est nulle.

### Limite de précision

Le capteur injection/soutirage mesure le bilan réseau global de l'installation, et non l'alimentation dédiée des cumulus. En mode forcé, la répartition proportionnelle constitue donc une **estimation** : les autres consommations de la maison peuvent influencer le résultat. Une mesure dédiée à chaque cumulus serait nécessaire pour obtenir une attribution exacte.

## Capteurs créés

L'intégration expose notamment :

- Puissance réseau d'origine (W).
- Puissance batterie (W), affichage simple du capteur `sensor.arsun_routeur_batterie`.
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

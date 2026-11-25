# ARSUN Energy

Intégration personnalisée Home Assistant pour le routeur ARSUN, par Solaire Domotique.

## Installation via Home Assistant Marketplace

1. Ouvrir **Marketplace**.
2. Menu ⋮ → Ajouter un dépôt depuis un lien.
3. Ajouter `https://github.com/solairedomotique/ha-arsun-energy`.
4. Rechercher **ARSUN Energy**, installer puis redémarrer Home Assistant.
5. Ajouter l'intégration et sélectionner le capteur réseau. Par défaut : `sensor.arsun_routeur_injection_soutirage`.

## Convention de signe

- `sensor.arsun_routeur_injection_soutirage` négatif : consommation depuis EDF.
- Le même capteur positif : énergie renvoyée vers EDF.
- `sensor.arsun_routeur_sortie_1` et `_sortie_2` : puissances instantanées positives des récepteurs, en W.

Le capteur **Puissance jauge** conserve le signe ARSUN : positif = injection EDF, négatif = consommation EDF.

## Capteurs créés

- Puissance réseau d'origine.
- Puissance cumulus sortie 1 et puissance cumulus sortie 2 (W, mesures instantanées).
- Puissance consommée EDF et puissance redonnée à EDF.
- Énergie consommée EDF et énergie redonnée à EDF (compteurs cumulatifs).
- Puissance jauge bidirectionnelle.
- Cumulus sortie 1 solaire / réseau (kWh).
- Cumulus sortie 2 solaire / réseau (kWh).

Tous les compteurs d'énergie sont exprimés en kWh avec `device_class: energy` et `state_class: total_increasing`, pour être utilisables dans le tableau de bord Energy de Home Assistant.
- Marche forcée canal 1 et marche forcée canal 2 (ON lorsque l’état LED correspondant vaut `H`).

## Répartition énergétique des cumulus

Entités lues automatiquement :
- `sensor.arsun_routeur_sortie_1`
- `sensor.arsun_routeur_sortie_2`
- `sensor.arsun_routeur_etat_led_s1`
- `sensor.arsun_routeur_etat_led_s2`
- `sensor.arsun_routeur_injection_soutirage`

Le mode forcé global est actif si **LED S1 = H OU LED S2 = H**.

- Si aucune LED n'est `H`, les puissances mesurées des sorties sont affectées au solaire.
- Si au moins une LED est `H`, la puissance soutirée depuis EDF (valeur négative du capteur réseau) est répartie proportionnellement entre les deux sorties, selon leurs puissances instantanées. La part restante de chaque sortie est affectée au solaire.
- Une sortie à 0 W ne reçoit aucune énergie.
- Les quatre compteurs sont cumulatifs et restaurés après redémarrage.

### Limite importante de la méthode

La mesure `injection_soutirage` représente le bilan réseau global de l'installation, pas une mesure dédiée aux cumulus. En mode forcé, la répartition proportionnelle suppose donc que l'import EDF mesuré peut être attribué aux deux cumulus. Les autres consommations de la maison peuvent influencer cette estimation. Pour une mesure parfaitement exacte, il faudrait une mesure dédiée à l'alimentation des cumulus.

## Développement

Version actuelle : 0.3.3.


### États des sorties ARSUN
Les états des canaux sont également exposés sous forme de capteurs de mode :
- `H` : Forcé H1H2
- `P` : Programme Horaire
- `---` : Automatique en attente de surplus
- `ON` : Surplus alimentant le chauffe-eau
- `OFF` : Sortie non alimentée

Les états `H` et `P` déclenchent la même répartition estimative de la puissance réseau entre les deux cumulus.

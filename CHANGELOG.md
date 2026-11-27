## 0.4.2
- Traite les états LED `-` et `---` de manière identique : sortie arrêtée, 0 W comptabilisé.
- Traite également `OFF` comme une sortie non alimentée (0 W).
- En mode forcé `H` ou `P`, plafonne l'import EDF à la puissance totale des sorties forcées.
- Répartit la part EDF proportionnellement entre les sorties forcées ; le complément de chaque sortie forcée est comptabilisé comme solaire.
- Conserve `ON` à 100 % solaire et incrémente séparément les quatre compteurs énergétiques sortie 1/2 solaire/réseau.

## 0.4.1
- Ajout du capteur de puissance batterie ARSUN `sensor.arsun_routeur_batterie` en W, en affichage simple uniquement.
- Ajustement du calcul énergétique par canal : `H` et `P` sont forcés et partagent l'estimation EDF, `ON` est 100 % solaire, `-` signifie que le chauffe-eau est à l'arrêt (0 W).
- La répartition EDF est désormais limitée aux canaux réellement en `H` ou `P`, sans attribuer de réseau à un canal en `ON`.
- Ajout dans le README de la présentation du partenariat entre Solaire Domotique, ARSUN et SOSUNELEC avec liens directs.

## 0.4.0
- Ajout de la détection automatique des entités sources avec propositions modifiables.
- Ajout d'une configuration entièrement manuelle des capteurs réseau, sorties cumulus et états LED.
- Sortie 2 et LED canal 2 facultatives.
- Adaptation des capteurs de puissance, des modes, des indicateurs de marche forcée et des compteurs aux entités sélectionnées.
- Conservation de la logique de répartition énergétique existante et des états forcés H/P.
- Correction de compatibilité pour les anciennes entrées de configuration : les entités historiques par défaut restent utilisées lorsque les nouveaux champs de configuration sont absents.

## 0.3.3
- Treat ARSUN LED states `H` (Forcé H1H2) and `P` (Programme Horaire) as equivalent forced modes for the heater solar/grid allocation.
- Keep the binary forced-mode indicators active for both `H` and `P`.
- Add readable operating-mode sensors for channels 1 and 2, mapping `H`, `P`, `---`, `ON`, and `OFF` to their French descriptions.
- Preserve the existing power sensors, energy counters, entity names, and Home Assistant Energy metadata.

## 0.3.2
- Added instantaneous power sensors for ARSUN outputs 1 and 2 (W).
- Preserved all existing sensor names and entity unique IDs.
- Kept cumulative energy sensors in kWh with `device_class: energy` and `state_class: total_increasing` for Home Assistant Energy compatibility.
- Kept the forced-mode binary sensors and the existing heater energy allocation.

## 0.3.1
- Added binary sensors for forced mode on ARSUN channels 1 and 2 (ON when the corresponding LED state is `H`).
- Kept the existing energy and power sensors and the heater energy split calculation.

# Changelog

## 0.3.0
- Corrected the gauge sign: positive means export to EDF; negative means consumption from EDF.
- Renamed grid energy sensors to clarify energy consumed from EDF and energy returned to EDF.
- Added four restored cumulative energy counters for heater outputs 1 and 2: solar and EDF shares.
- Heater split uses the global forced state: LED S1 is `H` OR LED S2 is `H`.
- During forced mode, EDF import is allocated proportionally to the instantaneous wattage measured on outputs 1 and 2. Remaining heater power is attributed to solar.
- When neither LED is `H`, measured heater output power is attributed to solar, as specified.

## 0.2.1
- Previous gauge sign correction release.

## 0.2.0
- Bidirectional signed gauge and default source selection.

## 0.1.3
- Initial public release with original power, split grid power, and cumulative energy counters.

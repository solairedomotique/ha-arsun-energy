## 2.5.0
- Mise à jour du numéro de version de l’intégration dans `manifest.json`.
- Harmonisation de la version logicielle affichée dans Home Assistant (`sw_version`) sur `2.5.0`.
- Aucun changement fonctionnel par rapport à la version 2.4.

## 2.4 (correctif)
- Ajout du capteur batterie dans la table des entités par défaut pour assurer la compatibilité des anciennes configurations.
- Harmonisation de la version affichée dans les informations de l'appareil sur 2.4.

## 2.4
- Correction de la restauration des compteurs énergétiques EDF et cumulus : la valeur restaurée n'est plus écrasée par une puissance instantanée en W.
- Ajout d'une sauvegarde persistante Home Assistant indépendante de l'ID temporaire de l'entrée, afin de conserver les totaux lors d'une réinstallation avec les mêmes entités sources.
- Sauvegarde périodique différée et sauvegarde immédiate au retrait des entités.

## 2.3.1\n- Correction du démarrage : ajout de `async_reload_entry`, appelée lors de l'enregistrement du listener de mise à jour des options.\n- Le lien « Visiter » et les fonctionnalités existantes sont conservés.\n\n## 2.3
- Mise à jour du numéro de version affiché dans les informations de l'appareil Home Assistant.

## 0.4.6
- Modification du seul lien « Visiter » de la fiche appareil : https://solaire-domotique.fr/ha/github/arsun/.

## 0.4.5
- Présentation graphique des trois partenaires dans le README avec leurs logos hébergés sur solaire-domotique.fr.
- Logos cliquables vers les sites officiels ; le logo Solaire Domotique donne également accès à la chaîne YouTube.
- Images chargées par URL avec une hauteur d'affichage limitée afin de pouvoir remplacer les fichiers sur le FTP sans modifier le dépôt.

## 0.4.4
- Mise en valeur du partenariat dans le README avec liens directs vers le site Solaire Domotique, sa chaîne YouTube, ARSUN et SOSUNELEC.
- Enrichissement des informations de l'appareil Home Assistant : nom ARSUN Energy, fabricants/partenaires, modèle descriptif, version logicielle et lien vers le site Solaire Domotique.

## 0.4.3
- Amélioration de la détection automatique par analyse combinée de l'Entity ID, du friendly_name, de l'unité et du device_class.
- Priorité aux capteurs de puissance en W/kW et de classe `power`.
- Recherche des sorties et des LED par nom de canal, sans dépendance au préfixe de l'installation.
- Les états LED inconnus (dont `N`) ne sont pas interprétés et ne bloquent pas la détection basée sur le nom.
- Ajout de la puissance batterie comme source facultative configurable ; affichage simple en W, sans traitement énergétique.
- Ajout des informations de classe, unité et score dans l'aperçu des correspondances.

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

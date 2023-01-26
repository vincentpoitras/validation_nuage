# Contenu
  1. Résumé
  2. Structure générale
  3. Description détaillée des scripts

# Résumé
Ce répertoire contient les scripts qui servent à "formater" les trois jeux de données.  

**GEM5** 
 - Conversion: fst --> NetCDF

**CALIPSO** 
 - Conversion: hdf --> NetCDF
 - Sélection des traces qui passent dans le domaine d'intérêt (liste de fichiers).

**MODIS**
 - Conversion: hdf --> NetCDF
 - Interpolation vers le domaine d'intérêt + fusion des fichiers de 5 min --> fichiers horaires
 - Fusion MYD06_L2 et MOD06_L2 --> MCD06_L2.


&nbsp;
# Structure générale

&nbsp;
**Scripts principaux et scripts de lancement**
À chacun des scripts principaux (debutant par le préfixe main) correspond un script de lancement (débutant par le préfixe submit). Par exemple:
> Pour lancer `main_GEM5_01_format.bash`, on utilise `submit_GEM5_01_format.bash`
  
&nbsp;
**Ordre de lancement**
Les scripts de lancements sont numérotés pour chaque jeux de données (GEM5, CALIPSO, MODIS) et ils doivent être lancés dans l'ordre correspondant. Par exemple:
> `main_CALIPSO_02_makefilelist.bash` doit être lancé après `main_CALIPSO_01_format.bash`

Il est à noter qu'il existe des tests sanitaires dans les scripts de lancements pour vérifier si l'étape à été complétée. Ces tests vérfient par exemples l'existence de répertoires ou de fichiers, mais ne sont pas exhaustifs. Il est préférable que l'usager s'assure lui-même que l'étape précédente a été complétée avant de passer à la suivante.

Par ailleur, à partir de l'étape 02 pour les jeux de données CALIPSO et MODIS, il est nécessaire d'avoir d'avoir au moins un fichier de GEM5 converti en format NetCDF (pour faire l'interpolation, identifier les traces de satellites passant au-dessus du domaine). Donc,
> `main_CALIPSO_02_makefilelist.bash` et `main_MODIS_02_interpolate_and_merge.bash` doivent être lancés après avoir produit au moins un fichier avec `main_GEM5_01_format.bash` (le chemin de ce fichier sera trouvé automatiquement).


&nbsp;
# Description détaillée des scripts

#### [A1] main_GEM5_01_format.bash

##### Soumission
>`./submit_GEM5_01_format.bash YYYYMMi YYYYMMf overwrite submission_type`
> - **YYYYMMi**: Date de début de l'intervalle des données à traiter (année + mois).
> - **YYYYMMf**: Date de fin de l'intervalle des données à traiter (année + mois).
> - **overwrite** [true/false]:  
&nbsp;&nbsp;&nbsp;&nbsp; 'true': lors d'une resoumission, écrase les données déjà existantes. 
&nbsp;&nbsp;&nbsp;&nbsp; 'false': ne traite que les fichiers manquants ou corrompus. 
> - **submission_type** [interactive/scheduler]: Soumettre la tâche interactivement ou en passant par l'ordonannceur.

Une tâche consiste à tariter tous les fichiers d'un répertoire mensuel.

**[IMPORTANT]** Cas spécial: Pour convertir le répertoire step0, il faut utiliser YYYYMMi=0 YYYYMMf=0. Les fichiers de ce répertoire contiennent des champs géophysiques dont on va se servir, il est donc important de ne pas oublié de le convertir lui aussi.

##### Scripts auxillaires
  - yamlmanip.py (lien vers ../yamlmanip.py)

##### Description
Effectue la converstion des fichiers fst (dm et pm contenues) vers le format fst en utilisant le module python **fstd2nc**.  

Note:  Le module python **fstd2nc** est utilisé au lieu du plus conventionnel **cdf2rpn** car ce dernier ne garde pas les coefficients de pression a et b (p=a+bLOG(ps/pref)). Ceux-ci vont éventuellemnt être nécessaires pour calculer les niveaux de pression (momentum + thermodynamic).
  
##### Références
  - Module python fstd2nc : https://pypi.org/project/fstd2nc


&nbsp;
#### [B1] main_CALIPSO_01_format.bash
##### Soumission
>`./submit_CALIPSO_01_format.bash YYYYi YYYYf overwrite submission_type`
> - **YYYYi**: Date de début de l'intervalle des données à traiter (année seule).
> - **YYYYf**: Date de fin de l'intervalle des données à traiter (année seule).
> - **overwrite** [true/false]:  
&nbsp;&nbsp;&nbsp;&nbsp; 'true': lors d'une resoumission, écrase les données déjà existantes.  
&nbsp;&nbsp;&nbsp;&nbsp; 'false': ne traite que les fichiers manquants ou corrompus.  
> - **submission_type** [interactive/scheduler]: Soumettre la tâche interactivement ou en passant par l'ordonannceur.

Une tâche correspond à traiter toutes les données d'une année.

##### Scripts auxillaires
  - yamlmanip.py (lien vers ../yamlmanip.py)
  - h4tonccf_nc4
  - auxCALIPSO_format_attributes.py

##### Description
Effectue la conversion des fichiers hdf en NetCDF en utilisant **h4tonccf_nc4**. 

Dans le fichier original, l'attribut _valid_range_ est une chaine de caractère formé de 2 nombres séparés par trois points (...). Ce format non-standard peut créer certains bogues lors de la manipulation subséquente des fichiers NetCDF. Cet attribut est donc modifié en utilisant **aux_CALIPSO_format_attributes.py**. Exemple:
> Latitude:valid_range = "-90.0...90.0" ; (original)
> Latitude:valid_range = -90., 90. ;  (modifié)

##### Références
  - h4tonccf_nc4: http://hdfeos.org/software/h4cflib.php


&nbsp;
#### [B2] main_CALIPSO_02_makefilelist.bash
##### Soumission
>`./submit_CALIPSO_02_makefilelist.bash YYYYi YYYYf submission_type`
> - **YYYYi**: Date de début de l'intervalle des données à traiter (année seule).
> - **YYYYf**: Date de fin de l'intervalle des données à traiter (année seule).
> - **submission_type** [interactive/scheduler]: Soumettre la tâche interactivement ou en passant par l'ordonannceur.

Une tâche correspond à traiter toutes les données d'une année. 
Si la liste à créé existe déjà, il sera demandé lors de la soumission si on doit l'écraser.

##### Scripts auxillaires
  - yamlmanip.py (lien vers ../yamlmanip.py)
  - aux_CALIPSO_check_if_track_is_inside.py

##### Description
Identifie les fichiers contenant des portions de trajectoire passant au-dessus du domain (de la simulation GEM5) et crée un liste de ceux-ci. La liste comporte 8 colonnes:
> fichier &nbsp; nray &nbsp; datei &nbsp; datef &nbsp; date_calispo &nbsp; MM &nbsp; date_gem  &nbsp; npas_gem 
  - **fichier**: Chemin complet vers le fichier
  - **nray**: nombre de profils verticaux mesurées
  - **datei**: date [YYYYMMDDhhmmss] à laquelle la trajectoire du satellite entre dans le domaine
  - **datef**: date [YYYYMMDDhhmmss] à laquelle la trajectoire du satellite sort du le domaine
  - **date_calipso**:  date [YYYYMMDDhh00] associé à l'intervalle [datei,datef], arrondie à l'heure la plus près.
  - **MM**: mois extrait de date_calipso
  - **date_gem** : date [YYYYMMDD] apparaissant dans le fichier GEM5 contenant la date date_calipso
  - **npas_gem**: pas de temps (0 à 23) du fichier GEM5 correspondant à date_calipso 
 
 Note: les valeurs reliées à GEM5 ne sont évidemment pas nécessaire en soi pour traiter les données de CALIPSO, par contre elles vont être utiles pour trouver le fichier et le pas de temps correspondant lorsqu'on voudra comparé GEM5 et CALIPSO.
 
 Exemple 
 > chemin/fichier.nc  &nbsp; 166  &nbsp; 20140101032117 &nbsp; 20140101032320 &nbsp;  201401010300 &nbsp; 01 &nbsp; 20140101  &nbsp; 2
 

- Le satellite arrive au-dessus du domaine le 2014-01-01 à 03h21'17" et il sort le 2014-01-01 à 03h23'20".
- Durant cet intervalle, 166 profils verticaux ont été mesurés
- La date arrondie à l'heure près associé à cet intervalle est 2014-01-01 03h00' (car entierement située entre 02h30'00" et 03h29'59"). Lorsque datei et datef sont situés de par et d'autre d'une demi-heure (??h30), l'heure associée au "demi-inetrvalle" le plus grand est choisie.
- Le mois de la date arrondie est janvier (01). 
 &nbsp;
- Les fichiers quotidiens gem sont étiquettés par la date du jour (YYYYMMDD), mais contiennent en fait une plage horaire qui commence à 01H et se termine à 00H le jour suivant. Les parties année+mois+quantième de date_gem et date_calispo seront identiques si l'heure se situe entre 01h00' et 23h00' (comme dans cette exemple, ce qui donne date_gem=20140101). Si on avait eu date_calipso=201401010000, alors dans ce cas cela aurait donné date_gem=20131231. En résumé, pour trouver la date 2014-01-01 03h00' dans un fichier gem, il faut donc choisir le fichier ...20140101d.nc  et le pas de temps 2 (en python on commence à compter à 0: 0-->01h00', 1-->02h00', 03-->03h00')
 
À noter: chaque profil vertical est identifié par une latitude, une longitude et une date. Puisque le satellite se déplace pendant une mesure, chacune de ses trois quantités comportent 3 valeurs (au début de la mesure, au milieu de la mesure, ;a la fin de la mesure). Tous les calculs sont basés sur la valeur du milieu de meeure.



&nbsp;
#### [C1] main_MODIS_01_format.bash
##### Soumission
> `./submit_MODIS_01_format.bash YYYYMMi YYYYMMf dataset overwrite submission_type`  
> - **YYYYMMi**: Date de début de l'intervalle des données à traiter (année + mois).
> - **YYYYMMf**: Date de fin de l'intervalle des données à traiter (année + mois).
> - **dataset**: [MYD06_L2/MOD06_L2]
> - **overwrite** [true/false]:  
&nbsp;&nbsp;&nbsp;&nbsp; 'true': lors d'une resoumission, écrase les données déjà existantes. 
&nbsp;&nbsp;&nbsp;&nbsp; 'false': ne traite que les fichiers manquants ou corrompus. 
>- **submission_type** [interactive/scheduler]: Soumettre la tâche interactivement ou en passant par l'ordonannceur.


##### Scripts auxillaires
  - yamlmanip.py (lien vers ../yamlmanip.py)
  - h4tonccf_nc4
  - aux_MODIS_MMDD2JJJ.py
  - aux_MODIS_format.py

##### Description
Effectue la conversion des fichiers hdf en NetCDF en utilisant **h4tonccf_nc4**.

Le script **aux_MODIS_MMDD2JJJ.py** est utilisé pour chnager le format YYYYJJJ --> YYYYMMDD dans le nom de fichiers de sortie. Exemples
> MYD06_L2.A**2014001**.0000.061.2018051042231.hdf --> MYD06_L2_**20140101**\_0000.nc
> MYD06_L2.A**2015365**.2355.061.2018055105135.hdf --> MYD06_L2_**20141231**\_2355.nc

Le script **aux_MODIS_format.py** élimine les champs créés en double lors de la conversion faite avec **h4tonccf_nc4**. Les données originales sont définies sur deux grilles de résolution différente. Les données qui nous intéressent sont définies sur la grille la plus fine, mais lors de la conversion, la grille la plus grossière est utilisée comme grille de référence. Les champs définis sur la grille la plus grossière sortent correctement, ceux définis sur la grille la plus fine sortent en double _nomvar_ (interpolé sur la grille la plus grossière) et _nomvar\_reduced_ (sur la grille originale). Le script élimine simplement le champs _nomvar_ et renomme ensuite _nomvar\_reduced_ en _nomvar_. 

Note: la présence des doublets résulte peut-être d'une utilisation naive de **h4tonccf_nc4** (que je ne maîtrise pas en détail). Si c'était possible de créer uniquement la version non-interpolée du champs, ça serait évidemment préférable.

##### Références
  - h4tonccf_nc4: http://hdfeos.org/software/h4cflib.php

&nbsp;
#### [C2] main_MODIS_02_interpolate_and_merge.bash

##### Soumission
> `./submit_MODIS_02_interpolate_and_merge.bash YYYYMMi YYYYMMf dataset overwrite submission_type`  
> - **YYYYMMi**: Date de début de l'intervalle des données à traiter (année + mois).
> - **YYYYMMf**: Date de fin de l'intervalle des données à traiter (année + mois).
> - **dataset**: [MYD06_L2/MOD06_L2]
> - **overwrite** [true/false]:  
&nbsp;&nbsp;&nbsp;&nbsp; 'true': lors d'une resoumission, écrase les données déjà existantes. 
&nbsp;&nbsp;&nbsp;&nbsp; 'false': ne traite que les fichiers manquants ou corrompus. 
>- **submission_type** [interactive/scheduler]: Soumettre la tâche interactivement ou en passant par l'ordonannceur.

##### Scripts auxillaires
  - yamlmanip.py (lien vers ../yamlmanip.py)
  - aux_MODIS_merge_subhour_files.py
 
##### Description
Les fichiers sont diponibles aux 5 minutes sur une grille propre à chaque fichier (qui dépend de la positions des satellites). Les 12 fichiers associés à une heure sont combinés. Par exemple: 13h30, 13h35, ..., 14h20, 14h25 &nbsp;&nbsp; --> &nbsp;&nbsp; 13h00. Cela se fait en deux étapes:
  - Interpolation bilinéaire (faite avec cdo) des fichiers de 5-min vers la grille utilisée par GEM5
  - Combinaison des 12 fichiers par le script **aux_MODIS_merge_subhour_files.py**

Note 1: Si pour une heure donnée, aucune données ne se trouve dans le domaine, le fichier sera éliminé.
Note 2: Les fichiers créer dépendent du domaine considéré. Pour un autre domaine (par exemple à plus fine résolution), il faudra exécuter de nouveau ce scripts (en modifiant le chemin de GEM5 et le nom du domaine dans le fichier de configuration).

&nbsp;
#### [C3] main_MODIS_03_merge_MOD06_and_MYD06.bash

##### Soumission
> `./submit_MODIS_03_merge_MOD06_and_MYD06.bas YYYYMMi YYYYMMf overwrite submission_type`  
> - **YYYYMMi**: Date de début de l'intervalle des données à traiter (année + mois).
> - **YYYYMMf**: Date de fin de l'intervalle des données à traiter (année + mois).
> - **dataset**: [MYD06_L2/MOD06_L2]
> - **overwrite** [true/false]:  
&nbsp;&nbsp;&nbsp;&nbsp; 'true': lors d'une resoumission, écrase les données déjà existantes. 
&nbsp;&nbsp;&nbsp;&nbsp; 'false': ne traite que les fichiers manquants, corrompus et les liens symboliques. 
>- **submission_type** [interactive/scheduler]: Soumettre la tâche interactivement ou en passant par l'ordonannceur.

##### Scripts auxillaires
  - yamlmanip.py (lien vers ../yamlmanip.py)
  - aux_MODIS_average_two_files.py

##### Description
Ce script ssert à combiner les deux jeux de donnée (MYD06_L2 et MOD06_L2) en un seul produit (MCD06_L2). Pour une heure données, 3 situations peuvent se produire
  - MYD06_L2_YYYYMMDD\_hhmm.nc et MOD06_L2_YYYYMMDD\_hhmm.nc n'existent pas (pas de données dans le donmaine). Dans ce cas, MCD06_L2_YYYYMMDD\_hhmm.nc n'est pas créé.
  - Un seul des deux fichiers existe. Dans ce cas, MCD06_L2_YYYYMMDD\_hhmm.nc est crée comme lien symbolique vers le fichiers existant.
  - Les deux fichiers existent. Dans ce cas, MCD06_L2_YYYYMMDD\_hhmm.nc est créé par le scripts **aux_MODIS_average_two_files.py** qui combine les valeurs des deux fichiers. Pour chaque point de grille, s'il y a
    + 1 valeur diponible (dans un seul fichier)
         - On prend la valeur dispobible
    + 2 valeur disponibles (une dans chaque fichiers)
         - On prend la valeur moyenne si la variable se moyenne.
         - On prend la valeur associée au couvert nuageux le plus important si la variable ne se moyenne pas (par exemple Cloud_Phase_Infrared qui est représentée par un code)


# Contenu
  - submit_COSPIN_01.bash
  - wrapper_COSPIN_01.bash
  - main_COSPIN_01.py
  - aux_COSPIN_01.py

# Tâche à réaliser
Produire les fichiers nécessaires pour faire rouler le simulateur de produits satellitaires **COSP2**.

# Soumission
Le script principal `main_COSPIN_01.py` étant en python, il a été plus simple de l'insérer dans un *wrapper* en bash pour le soumettre à l'ordonnaceur. Le script `submit_COSPIN_01.bash` soumet donc indirectement `main_COSPIN_01.py` à travers `wrapper_COSPIN_01.bash`.

>`./submit_COSPIN_01.bash YYYYMMi YYYYMMf dataset  overwrite submission_type`
- **YYYYMMi**: Date de début de l'intervalle des données à traiter (année + mois).
- **YYYYMMf**: Date de fin de l'intervalle des données à traiter (année + mois).
- **dataset** [CALIPSO/MYD06_L2/MOD06_L2/MCD06_L2/ALL_STEPS]: Liste contenant les pas de temps où les observations sont disponibles.
- **overwrite** [true/false]:  
&nbsp;&nbsp;&nbsp;&nbsp; 'true': lors d'une resoumission, écrase les données déjà existantes.    
&nbsp;&nbsp;&nbsp;&nbsp; 'false': ne traite que les fichiers manquants ou corrompus.    
- **submission_type** [interactive/scheduler]: Soumettre la tâche interactivement ou en passant par l'ordonannceur.

**Note 1**: Une tâche consiste à traiter tous les fichiers d'un répertoire mensuel.    
**Note 2**: L'idée derrière la productions de données avec **COSP2** est de pouvoir comparer les observations à la simulation. Il n'est donc pas nécessaire de traiter tous les pas de temps, seuelement ceux pour lesquelles des données observationelles sont disponibles. On spécifie le jeu de donnée désiré lors de la soumission (*dataset*) et le script ira lire les pas de temps à traiter dans le fichier correspondant (produit lors de l'étape de formatage des données). Des pas de temps peuvent évidemment être communs à différents jeux de données et ils ne sont traités qu'une seule fois (si *overwrite*=*false*). Si *dataset*=*ALL_STEPS*, tous les pas de temps seront traités (l'implémentation de cette option n'est pas encore complètement terminée)

# Descriptions
Une description plus détaillée des scripts `main_COSPIN_01.py` et `aux_COSPIN_01.py` est à venir. 

# Crédits
Les scripts `main_COSPIN_01.py` et `aux_COSPIN_01.py` ont été partielleemnt adaptés à partir des scripts développés par Zhipeng Qu. Les discussions du groupe ECCC/UQAM sur COSP2 Faisal Boudala, Mélissa Cholette, Jason Milbrant, Vincent Poitras, Zhipeng Qu) ont aussi beaucoup aidé.

# Contenu  
  - Répertoire COSPv2.0  

# Répertoire COSPv2.0  

### Description
Le contenu du répertoire COSPv2.0 est une version simplifiée du répertoire original qu'on peut télécharger ici:   
https://github.com/CFMIP/COSPv2.0   



### Compilation  

Avant de lancer la compilation, il faut ajouter les bonnes librairies au fichier de configuration de compilation (` .../COSPv2.0/build/Makefile.conf`), par exemple:  
![](images/makefiles.png)  

Il faut aussi s'assurer que les chemins vers les librairies sont correctement définis dans les variables d'environnement  
> export PATH LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/sca/compilers_and_tools/netcdf-f/gfortran/lib  
> export LIBRARY_PATH=$LIBRARY_PATH:/usr/lib/x86_64-linux-gnu  

La compilation peut maintenant être lancée:  
> ./Makefile  

test

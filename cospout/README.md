# Contenu  
  - Répertoire COSPv2.0  

# Répertoire COSPv2.0  

### Description
Le répertoire COSPv2.0 contient le code de COSP2 ainsi que des exemples. Il a été téléchargé à aprtir de la source offcielle: 
https://github.com/CFMIP/COSPv2.0   



### Compilation  

Avant de lancer la compilation, il faut ajouter les bonnes librairies au fichier de configuration de compilation:
`COSPv2.0/build/Makefile.conf`  

Par exemple 
![](https://github.com/vincentpoitras/validation_nuage/blob/master/cospout/images/Makefile.conf.png)


Il faut aussi s'assurer que les chemins vers les librairies sont correctement définis dans les variables d'environnement  
> `export PATH LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/sca/compilers_and_tools/netcdf-f/gfortran/lib`  
> `export LIBRARY_PATH=$LIBRARY_PATH:/usr/lib/x86_64-linux-gnu`  

La compilation peut maintenant être lancée:  
> `./Makefile`  


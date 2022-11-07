#!/bin/bash


# DATASET : CAL_LID_L2_05kmCPro-Standard-V4 
# INFO    : https://www-calipso.larc.nasa.gov/resources/calipso_users_guide/data_summaries/profile_data_v420.php
# DOWNLOAD: https://search.earthdata.nasa.gov/search?q=CAL_LID_L2_05kmCPro-Standard-V4-20 (to gerenate the files_list)
#
# How to launch this script
# 	Scheduler  : YYYY=2014; soumet CALIPSO_download.bash -args $YYYY -jn CALIPSO_download_${YYYY} -t 864000
#	Intercative: ./CALIPSO_download.bash 2014
# Notes:
#	[1] This script it adapted from https://search.earthdata.nasa.gov
#           It downloads the files in the $files_list file (go on the website)
#           To download the files, an username and a password must be provided (go on the website)
#       [2] Since this file contain a clear password, it may be preferable to grant reading right only to the user 
#           chmod u+r  CALIPSO_download.bash 
#           chmod go-r CALIPSO_download.bash
#       [3] Download estimate time (for a whole year): ~3 days


# Input parameters
YYYY=$1


# Hardcoded parameters
username=vincentpoitras
password=PASSWORD_TO_BE_EDITED
output_directory=/pampa/poitras/DATA/CALIPSO/CAL_LID_L2_05kmCPro-Standard-V4/hdf/$YYYY
files_list=/home/poitras/validation_des_nuages/download/CAL_LID_L2_${YYYY}.txt


# Check wheter the output_directory and the file_list are existing
[ -d $output_directory ] || { echo $output_directory does not exist. It will be created; mkdir -p $output_directory }
[ -f $files_list       ] || { echo $files_list does not exist. EXIT; exit; }

# Moveing into the output_directory (this cannot be specified when we are dowloading files witrh curl)
cd $output_directory



    ###########################################################################################
    # The script below was taken from https://search.earthdata.nasa.gov with minor adaptation #
    ###########################################################################################
    GREP_OPTIONS=''

    cookiejar=$(mktemp cookies.XXXXXXXXXX)
    netrc=$(mktemp netrc.XXXXXXXXXX)
    chmod 0600 "$cookiejar" "$netrc"
    function finish {
      rm -rf "$cookiejar" "$netrc"
    }

    trap finish EXIT
    WGETRC="$wgetrc"

    prompt_credentials() {
        #echo "Enter your Earthdata Login or other provider supplied credentials"
        #read -p "Username (vincentpoitras): " username
        #username=${username:-vincentpoitras}
        #read -s -p "Password: " password
        echo "machine urs.earthdata.nasa.gov login $username password $password" >> $netrc
        echo
	cat $netrc
    }

    exit_with_error() {
        echo
        echo "Unable to Retrieve Data"
        echo
        echo $1
        echo
        echo "https://asdc.larc.nasa.gov/data/CALIPSO/LID_L2_05kmCPro-Standard-V4-20/2014/12/CAL_LID_L2_05kmCPro-Standard-V4-20.2014-12-30T23-25-04ZD.hdf"
        echo
        exit 1
    }

    prompt_credentials
      detect_app_approval() {
        approved=`curl -s -b "$cookiejar" -c "$cookiejar" -L --max-redirs 5 --netrc-file "$netrc" https://asdc.larc.nasa.gov/data/CALIPSO/LID_L2_05kmCPro-Standard-V4-20/2014/12/CAL_LID_L2_05kmCPro-Standard-V4-20.2014-12-30T23-25-04ZD.hdf -w %{http_code} | tail  -1`
        if [ "$approved" -ne "302" ]; then
            # User didn't approve the app. Direct users to approve the app in URS
            exit_with_error "Please ensure that you have authorized the remote application by visiting the link below "
        fi
    }

    setup_auth_curl() {
        # Firstly, check if it require URS authentication
        status=$(curl -s -z "$(date)" -w %{http_code} https://asdc.larc.nasa.gov/data/CALIPSO/LID_L2_05kmCPro-Standard-V4-20/2014/12/CAL_LID_L2_05kmCPro-Standard-V4-20.2014-12-30T23-25-04ZD.hdf | tail -1)
        if [[ "$status" -ne "200" && "$status" -ne "304" ]]; then
            # URS authentication is required. Now further check if the application/remote service is approved.
            detect_app_approval
        fi
    }

    setup_auth_wget() {
        # The safest way to auth via curl is netrc. Note: there's no checking or feedback
        # if login is unsuccessful
        touch ~/.netrc
        chmod 0600 ~/.netrc
        credentials=$(grep 'machine urs.earthdata.nasa.gov' ~/.netrc)
        if [ -z "$credentials" ]; then
            cat "$netrc" >> ~/.netrc
        fi
    }

    fetch_urls() {
      if command -v curl >/dev/null 2>&1; then
          setup_auth_curl
          while read -r line; do
            # Get everything after the last '/'
            filename="${line##*/}"

            # Strip everything after '?'
            stripped_query_params="${filename%%\?*}"

            curl -f -b "$cookiejar" -c "$cookiejar" -L --netrc-file "$netrc" -g -o $stripped_query_params -- $line && echo || exit_with_error "Command failed with error. Please retrieve the data manually."
          done;
      elif command -v wget >/dev/null 2>&1; then
          # We can't use wget to poke provider server to get info whether or not URS was integrated without download at least one of the files.
          echo
          echo "WARNING: Can't find curl, use wget instead."
          echo "WARNING: Script may not correctly identify Earthdata Login integrations."
          echo
          setup_auth_wget
          while read -r line; do
            # Get everything after the last '/'
            filename="${line##*/}"

            # Strip everything after '?'
            stripped_query_params="${filename%%\?*}"

            wget --load-cookies "$cookiejar" --save-cookies "$cookiejar" --output-document $stripped_query_params --keep-session-cookies -- $line && echo || exit_with_error "Command failed with error. Please retrieve the data manually."
          done;
      else
          exit_with_error "Error: Could not find a command-line downloader.  Please install curl or wget"
      fi
    }

    fetch_urls < $files_list

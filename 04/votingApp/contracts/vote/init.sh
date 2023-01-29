#!/usr/bin/env bash

# helpful tutorial
#https://dappradar.com/blog/introduction-to-algorand-pyteal-smart-signature-development

./sandbox goal account new alice
./sandbox goal account new bob
#./sandbox goal account new charlie

./sandbox goal account list



# Compile voting contact
python voting.py
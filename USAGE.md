
# Using the CLDF data

In the following sections, we give some hints how to use the [CLDF data](cldf/) in
this repository to answer common questions. To access the CSV data, we use the tools
provided with [csvkit](https://csvkit.readthedocs.io/en/1.0.3/), which you should
install to follow along.


## Listing the phoneme inventories for a language

Inspecting [`cldf/parameters.csv`](cldf/parameters.csv) we see that the phoneme inventory
of a language is spread over 4 different parameters:
```
Consonant_inventory,Consonant inventory,,Sound inventory,categorical,yes
Vowel_inventory,Vowel inventory,,Sound inventory,categorical,yes
Geminate_inventory,Geminate inventory,,Sound inventory,categorical,yes
Diphtong_inventory,Diphtong inventory,,Sound inventory,categorical,yes
Vowel_sequence_inventory,Vowel sequence inventory,,Sound inventory,categorical,yes
```

All four parameters have 
- an `ID` ending in `inventory`,
- are specified as `categorical`, thus their allowed values can be looked up in [`cldf/codes.csv`](cldf/codes.csv),
- are specified as `multichoice` parameters, i.e. a language may have more than one value for each of these parameters.

This information is the input for the following sequence of `csvkit` commands:

```shell script
$ csvjoin -c Code_ID,ID cldf/values.csv cldf/codes.csv | \
csvgrep -c Language_ID -m yue | \
csvgrep -c Parameter_ID -r"inventory$" | \
csvcut -c Parameter_ID,Name
Parameter_ID,Name
Consonant_inventory,/p
Consonant_inventory,t
Consonant_inventory,k
Consonant_inventory,kʷ
Consonant_inventory,pʰ
Consonant_inventory,tʰ
Consonant_inventory,kʰ
Consonant_inventory,kʷʰ
Consonant_inventory,t͡s
Consonant_inventory,t͡sʰ
Consonant_inventory,f
Consonant_inventory,s
Consonant_inventory,h
Consonant_inventory,m
Consonant_inventory,n
Consonant_inventory,ŋ
Consonant_inventory,l
Consonant_inventory,j
Consonant_inventory,w/
Vowel_inventory,/i
Vowel_inventory,y
Vowel_inventory,e
Vowel_inventory,ø
Vowel_inventory,a
Vowel_inventory,ɑ
Vowel_inventory,ɔ
Vowel_inventory,u/
Diphtong_inventory,/ai
Diphtong_inventory,ɑi
Diphtong_inventory,au
Diphtong_inventory,ɑu
Diphtong_inventory,ei
Diphtong_inventory,øi
Diphtong_inventory,iu
Diphtong_inventory,ui
Diphtong_inventory,oi
Diphtong_inventory,ou/
```


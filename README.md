# hrdfreader [![Current Version](https://img.shields.io/badge/version-2.2.0-green.svg)](https://github.com/BERNMOBIL/hrdfreader)

> parse hafas rohdaten format files into a postgres db

## Description

hrdfreader is used to import timetable data in HAFAS Rohdaten Format and is optimized for swiss public transport data as provided by [opentransportdata.ch](https://www.opentransportdata.ch)

The focus is set on analytics and fast access to departures of a given day.

It can manage multiple publications of timetable data and has features for automatic data import and time table generation.
Since version 2.1.1 there's also a VDV454 AUSRef server integrated to convert HRDF data into 'Linienfahrplan' data as used for public transport in Switzerland.

## Installation

clone repository

prepare database using ./db/create/create-hrdf.sh

customize settings in hrdfconfig.config
customize settings in vdvconfig.conf, if VDV server is needed

## How to use

```bash
# import data from .zip file
hrdfimport.py <importFile>

# generate daily timetables
hrdfgenerate.py  <eckdatenId> [<generateFrom> <generateTo>]
```

## Automation

You can set up cronjobs for

hrdfimportSVC.py - to regularly check for new data and import it

hrdfgenerateSVC.py - to generate daily timetables for the configured range of days

Configuration is done in hrdfconfig.config


## Version History

* 2.2.0
    * FIX: Lookuptable for Haltepositionstexte gets too big to be stored in memory 
* 2.1.2
    * ADD: View for stop point identification
* 2.1.1
    * ADD: VDV454 AUSRef Server
    * ADD: tables for conversion from HRDF formats to PT CH specific VDV formats 
* 2.0.2
    * ADD: Automation of import and generation (cronjob needed)
    * ADD: config file for individual settings
* 2.0.1
    * ADD: Debug Mode for Logging
    * Change: Based on Swiss HRDF 5.40.41
* 1.0
    * Support for Swiss HRDF 5.20.xx 


## Meta

Distributed under the LGPL-3.0 license. See ``LICENSE`` for more information.

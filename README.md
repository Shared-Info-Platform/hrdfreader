# hrdfreader

> parse hafas rohdaten format files into a postgres db

[![Current Version](https://img.shields.io/badge/version-2.0.2-green.svg)](https://github.com/BERNMOBIL/hrdfreader)

## Description

hrdfreader is used to import timetable data in HAFAS Rohdaten Format and is optimized for swiss public transport data as provided by [opentransportdata.ch](https://www.opentransportdata.ch)

The focus is set on analytics and fast access to departures of a given day. hrdfreader is not meant to be a backend for a passenger information system.

It can manage multiple publications of timetable data and has features for automatic data import and time table generation.

## Installation

clone repository

prepare database using ./db/create/create-hrdf.sh

customize settings in hrdfconfig.config

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

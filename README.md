## Summary

**OPGG Scraper** is a web scraper written in Python to quickly look up [op.gg](https://www.op.gg) builds for League of Legends from the terminal.

It uses [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) to scrape the website, and [anytree](https://github.com/c0fec0de/anytree) + [colorama](https://github.com/tartley/colorama) for the result visualization. 

Example:

<img src="/assets/images/image-1.png" style="zoom:50%;" />

## Role Flags

A role can also be specified by using a flag. This is useful in cases where a champion can be played in many roles but we are interested in one of its non-main roles. 

> For example, Akshan is mostly played mid but if we want to see his builds for top, we  can use the '-t' flag. 

<img src="/assets/images/image-2.png" style="zoom:50%;" />

The role-specifying flags are as follows:

* '-t' for top
* '-j' for jungle
* '-m' for mid
* '-b' for adc
* '-s' for support

## Mode Flags

Finally, similar to the roles flags a mode can be specified alongside the champion. By default, ranked data will be requested, but ARAM and URF are also available by writing "aram" or "urf" respectively after the champion name. 

Example:

<img src="/assets/images/image-3.png" style="zoom:50%;" />


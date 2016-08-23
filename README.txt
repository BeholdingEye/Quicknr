
            =======
            QUICKNR
            =======

Fast and powerful Python application for the making and updating of 
websites from plain text sources.

Quicknr is Copyright 2016 Karl Dolenc, beholdingeye.com. 
All rights reserved.

Licensed under the GPL License as open source, free software.

Documentation and a growing collection of extras for Quicknr can be 
found here:

http://www.beholdingeye.com/quicknr


SYSTEM REQUIREMENTS

Python 3.4 or greater is required.

Quicknr should work on all platforms that Python runs on, including 
Windows, Mac and Linux.


CHANGELOG

Version 2.0.0 - 23 August 2016

* FTP can now be configured for active or passive connection with the 
    new FTP_PASSIVE configuration setting.
* The "lib.js" file that is copied to new websites has been fixed; it 
    previously contained code compatible only with Firefox and Chrome.

Version 1.9.0 - 27 June 2016

* Quicknr now includes a "templates" folder, containing the "base" set 
    of 3 CSS files that are copied to new websites. This serves as a 
    starting point for customisation, exposing all generated classes.
* Default Head and Tail snippets in configuration now include empty 
    page header and footer, ready for content.
* The sample custom Python directive "page_style_link" is now actually 
    used in support of new CSS files and is in the Head snippet.
* News item thumbnails on news listing page now load as background 
    images of their container, making them easier to style with CSS.
* Default "More..." link on news listing page changed to "More>" in 
    the configuration to avoid repetition of any preceding "...".
* Improved handling of import and Python directives in source files.
* A few other minor improvements and fixes.

Version 1.8.0 - 19 June 2016

* News listing page now features a "Load More" Javascript button for 
    displaying more news items than shown, if more are available.
* A "javascript" folder now ships with Quicknr, containing "lib.js" with
    routine functions and "news.js" for news listing functionality. The 
    related configuration option for copying of Javascript files has 
    been removed, being redundant.
* News listing page title and its link text on news post pages have been
    split into two configuration preferences, enabling "Blog" title, but
    "Latest News" link.
* News item thumbnails on the news listing page can now be generated 
    rectangular or square, controlled by a new preference.
* Open Graph and Twitter Card, as well as the canonical <link> tag and 
    optionally <meta> description tag can now be edited by Quicknr from 
    page content, filling out their title, description, image and URL. 
    Of most use for news posts that may be shared on social media.
* Numerous smaller fixes and improvements.

Version 1.7.0 - 14 May 2016

* HTML <title> is now set not only for ".txt" source files, but also 
    ".html". In the latter case, the title is obtained from the 
    filename. If the file is "index.html", the title will be "Home".
* Head and Tail snippets in the "config.txt" file are now in HTML 5 
    format.

Version 1.6.0 - 8 April 2016

Whereas previously Quicknr used the XHTML style of HTML tags (with 
    "empty" tags having " />" endings) regardless of the DOCTYPE, now
    HTML style (with ">" endings) is used if <!DOCTYPE html> is found.
    A new configuration setting allows old behaviour to be retained.  

Version 1.5.0 - 4 April 2016

Indenting of the HTML tree is now done natively by Quicknr, Python's
    XML module is no longer used. The feature is now safe, the 
    configuration option for turning it off has been removed.

Version 1.4.0 - 3 April 2016

* New Tools mode, accessed as a commandline '-t' toggle, with two
    commands:
        - Delete a news post:
            Delete all files, links and records of a news post, locally
            and from the server.
        - Upgrade 'config.txt' file to latest version
            Use this after upgrading to a new Quicknr release, to copy
            latest 'config.txt' contents to a website, while keeping
            existing preferences
* The date of a news post can now be obtained from the first word of a
    news post filename, if it is in numerical YYYYMMDD format.
* Javascript links can be made with <span> rather than <a> tags.
* Custom Javascript files can now be set for import into every website.
* Fix: news listing page now takes account of file extension preference,
    is not limited to ".html".
* A number of other small improvements and fixes.

Version 1.3.0 - 22 March 2016

* New optional feature: image thumbnails with news post items on the news 
    listing page. Quicknr creates the thumbs if PIL is available.
* HTML tree indenting improved, the feature is now turned on by default.
* Randomness of "odd"/"even" classes on floated image blocks removed.
    This should be handled with CSS, if required.
* News.js file now always offered for upload to server when news are 
    updated, across restarts.
* Several other fixes and small improvements.

Version 1.2.3 - 9 March 2016

Correction for two unescaped line breaks in the news.js file.

Version 1.2.2 - 8 March 2016

Fix for an uploading bug introduced in previous release, and another typo.

Version 1.2.1 - 8 March 2016

Fixing typos missed in previous release.

Version 1.2.0 - 8 March 2016

News posts now feature Previous and Next links, created dynamically by 
    Javascript.

Version 1.1.3 - 3 March 2016

Basic Open Graph and Twitter Card meta tags with mostly empty content 
    attributes now part of the head snippet in "config.txt" file.

Version 1.1.2 - 2 March 2016

Version number updated in the "Quicknr_App.py" file.

Version 1.1.1 - 2 March 2016

Correction for a typo in a "config.txt" meta tag that resulted in badly 
    formed XHTML.

Version 1.1.0 - 1 March 2016

* News list link on news postings can now be positioned at start or end 
    of page, not just the end.
* News list link prefix now a configurable option.
* More fine-grained commandline options for uploading of specific 
    resource folders have been added.
* Naming convention for import files has been improved.
* More robust prevention of styling markup being left in "alt" attributes.
* Bug fix for ID generator, regex used was too greedy.
* Some whitespace fixes when HTML tree indentation is on.
* Miscellaneous small improvements.

Version 1.0.0 - 15 February 2016

First public release.

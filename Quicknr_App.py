#!/usr/bin/env python3
# -*- coding: utf-8 -*-

########################################################################
#                                                                      #
#                               QUICKNR                                #
#                                                                      #
#              Fast and powerful Python application for                #
#                 the making and updating of websites                  #
#                       from plain text sources                        #
#                                                                      #
#                                                                      #
#                            Version 1.8.0                             #
#                                                                      #
#            Copyright 2016 Karl Dolenc, beholdingeye.com.             #
#                         All rights reserved.                         #
#                                                                      #
#                  Python 3.4 or greater is required.                  #
#                                                                      #
########################################################################

#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  


import sys
# Check for version, must be 3.4 or greater
if sys.version_info[0] < 3:
    eval(   "print 'Error: Python "+str(sys.version_info[0])+" is too old for Quicknr.\n"+\
            "       Please upgrade to version 3.4 or greater.\n       Quit.'")
    sys.exit()
if sys.version_info[0] == 3 and sys.version_info[1] < 4:
    print(  "Error: Python 3."+str(sys.version_info[1])+" is too old for Quicknr.\n"+\
            "       Please upgrade to version 3.4 or greater.\n       Quit.")
    sys.exit()

import os, re, hashlib, shutil, html, getpass, random, readline, argparse
import xml.dom.minidom as xml
import ftplib as ftp
import datetime as dt
from urllib.parse import urljoin
from urllib.request import pathname2url
from contextlib import suppress
try: import markdown
except ImportError: markdownModule = False
else: markdownModule = True
try:
    from PIL import Image as img
    from PIL import ImageOps
except ImportError: imgModule = False
else: imgModule = True


def markdown_to_html(text):
    """
    Process text from Markdown markup to HTML, return the result
    
    This is the only function that is outside the main Quicknr() function,
    for easy adaptation or override by the user. Incorporate your pre- and 
    post-processors and extensions as you like here
    
    """
    if markdownModule: return markdown.markdown(text)
    else:
        print("Error: Markdown module not available. Text returned in original state.")
        return text

class QuicknrError(Exception):
    """
    Custom exception, used to provide traceback on handled errors, if pref set so
    
    """
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return str(self.message)

def Quicknr():
    """
    Quicknr - Fast and powerful Python application for the making and updating of 
    websites from plain text sources
    
    """
    
    print("\n===================== QUICKNR 1.8.0 =====================\n")
    
    # --------------------- App defaults
    
    # All values in CAPS are settable in "config.txt" file, except FILE_SIZE_LIMIT,
    # which is only settable here (True or False) and sets a 1MB limit on the size of 
    # files being worked on. camelCase values at the end are set by code
    
    CD = dict(
                    HTML_HEAD = "",
                    HTML_TAIL = "",
                    HTML_TITLE = "WEBSITE-PAGE",
                    HTML_TITLE_SEPARATOR = " - ",
                    HTML_WEBSITE_NAME = "Quicknr",
                    HTML_PAGE_TITLE = "Test Page",
                    PAGE_FILE_EXTENSION = ".html",
                    QLM_OR_MARKDOWN = "QLM",
                    MARKDOWN_TITLING = "YES",
                    HTML_TAG_ID = "NO",
                    NEWS_LIST_ITEMS = "50",
                    NEWS_LIST_TITLE = "Latest News",
                    NEWS_BLURB_LENGTH = "300",
                    NEWS_MORE_PHRASE = "More...",
                    NEWS_LIST_LINK = "Latest News",
                    NEWS_LIST_LINK_POSITION = "END",
                    NEWS_LIST_LINK_PREFIX = "",
                    NEWS_DATE_FORMAT = "%A, %d %B %Y",
                    NEWS_DATE_FROM_FILENAME = "NO",
                    NEWS_PREV_LINK = "&lt; Older",
                    NEWS_NEXT_LINK = "Newer &gt;",
                    NEWS_LIST_THUMBS = "YES",
                    NEWS_LIST_THUMB_SIZE = "100",
                    NEWS_LIST_THUMB_SQUARE = "YES",
                    JAVASCRIPT_LINK_SPAN = "YES",
                    JAVASCRIPT_LINK_PRE = "",
                    JAVASCRIPT_LINK_POST = "",
                    META_EDIT = "YES",
                    META_DESCRIPTION = "YES",
                    META_BASE_URL = "",
                    DEBUG_ERRORS = "NO",
                    FTP_SERVER = "",
                    FTP_PATH = "",
                    FTP_USERNAME = "",
                    FTP_PASSWORD = "",
                    FTP_ACCT = "",
                    FTP_DEBUG = "0",
                    ALWAYS_XHTML_TAGS = "NO",
                    FILE_SIZE_LIMIT = True,
                    siteDir = "", # Path
                    siteFolder = "", # Name
                    sourceFilePath = "",
                    htmlFilePath = ""
                )
    
    # --------------------- App current working directory
    qnrDir = os.path.dirname(sys.argv[0])
    # If CWD is the Quicknr folder, sys.argv[0] may be only the script name, no dir path
    if not qnrDir: qnrDir = os.getcwd()
    else: os.chdir(qnrDir) # Set CWD to the app
    print("Application working directory:\n  %s\n\n" % qnrDir)
    # Paranoid, but you never know...
    if "Quicknr_App.py" not in os.listdir("."):
        print(  "Error: Quicknr has not started up in its own directory.\n"
                "       Contact your webmaster for help.\n"
                "       Quit.")
        sys.exit()
    
    # Prepare list for <pre> handling
    preContentL = []
    
    # Prepare list for Javascript link function argument handling
    #jsLinkContentL = []
    
    # Boolean toggle for 'page_sources/news.txt' updating conversion
    updateNewsList = False
    
    # Boolean toggle for 'page_sources/news.txt' to be rebuilt
    rebuildNewsList = False
    
    # News list item block to be filled with data and inserted into news posts
    newsListItemBlock = """
<!-- Quicknr-news-list-item-block
<div class="headed_section">
  <h2 class="heading"><span>DATE_TEXT</span> <a href="POST_URL">HEADING_TEXT</a></h2>
  <div class="section">
    <div class="imgfloat link_img">
      <a href="POST_URL"><img src="THUMB_URL" alt=""></a>
    </div>
    <p class="p_1 img_p">BLURB_TEXT <a href="POST_URL">MORE_TEXT</a></p>
  </div>
</div>
-->
    """
    
    # News list item block, no thumbnail
    newsListItemBlockNoThumb = """
<!-- Quicknr-news-list-item-block
<div class="headed_section">
  <h2 class="heading"><span>DATE_TEXT</span> <a href="POST_URL">HEADING_TEXT</a></h2>
  <div class="section">
    <p class="p_1">BLURB_TEXT <a href="POST_URL">MORE_TEXT</a></p>
  </div>
</div>
-->
    """
    
    # --------------------- INTERFACE/UTILITY FUNCTIONS ---------------------

    def _parse_cli_args():
        """
        Return commandline arguments parsed and type-validated by the argparse module
        
        """
        argparseDesc = "Commandline arguments accepted by this Quicknr_App script. "
        argparseDesc += "All arguments are optional."
        argParser = argparse.ArgumentParser(description=argparseDesc, 
                                            prefix_chars="-") # Prefix can be customised
        # Mark all sources as changed and to be converted to HTML again
        argParser.add_argument("-c","--convertall", # Bool optional argument
                            action="store_true", # Avoid None
                            help="Mark all sources as changed and to be converted to HTML again")
        # Enter Tools mode, for various admin tasks
        argParser.add_argument("-t","--tools", # Bool optional argument
                            action="store_true", # Avoid None
                            help="Enter Tools mode, to perform various admin tasks")
        # Upload resources as well
        argParser.add_argument("-r","--resupload", # Bool optional argument
                            action="store_true", # Avoid None
                            help="Upload resources folder 'res'")
        # Upload css files as well
        argParser.add_argument("-s","--stylesupload", # Bool optional argument
                            action="store_true", # Avoid None
                            help="Upload css stylesheet folder 'res/css'")
        # Upload js files as well
        argParser.add_argument("-j","--jsupload", # Bool optional argument
                            action="store_true", # Avoid None
                            help="Upload javascript folder 'res/js'")
        # Upload font files as well
        argParser.add_argument("-f","--fontsupload", # Bool optional argument
                            action="store_true", # Avoid None
                            help="Upload fonts folder 'res/font'")
        # Upload img files as well
        argParser.add_argument("-i","--imgupload", # Bool optional argument
                            action="store_true", # Avoid None
                            help="Upload images folder 'res/img'")
        # Upload all contents of "public_html", including those not by Quicknr
        argParser.add_argument("-a","--allupload", # Bool optional argument
                            action="store_true", # Avoid None
                            help="Upload all contents of 'public_html'")
        return argParser.parse_args() # Namespace object
    
    def _say_quit():
        """
        Simple quit
        
        """
        print("Quit.")
        sys.exit()
    
    def _say_error(message):
        """
        Error message and exit, or raise exception to provide traceback
        
        """
        if CD["DEBUG_ERRORS"] == "NO":
            print("\n" + message)
            sys.exit()
        else:
            raise QuicknrError("\n"+message)
        
    def _file_size_and_hash(fPath):
        """
        Return file size and hash as a tuple
        
        """
        filePath = os.path.join(CD["siteDir"], fPath)
        fS = os.path.getsize(filePath) # Bytes
        if CD["FILE_SIZE_LIMIT"] and fS > 1100000: # Let's stay sane
            _say_error( "Error: File '"+fPath+"' is over 1MB in size,\n" + \
                        "         too large for publication.\n" + \
                        "       Reduce the size to under 1MB and try again.\n" + \
                        "       Quit.")
        with open(filePath, mode="r") as f:
            fT = f.read()
        fH = hashlib.md5(fT.encode()).hexdigest()
        return (str(fS), fH)

    def _html_escape_noamp(tT, quote=True):
        """
        Returns text with <>'" characters escaped, but not & to protect existing
        character entities. Quotes conversion can be turned off
        
        """
        tT = tT.replace(">", "&gt;").replace("<", "&lt;")
        if quote:
            tT = tT.replace("'", "&#27;").replace('"', "&quot;")
        return tT

    def _ui_list_menu(inputList, inputTitle, userPrompt, customOption="", customKey=""):
        """
        Presents a list of up to 99 numbered options to choose from, returns chosen
        
        """
        if not inputList: return None
        inputList = inputList[:99]
        menu = "     " + inputTitle + ":\n"
        menu += "     " + "-"*(len(inputTitle)+1) + "\n\n     " # Underline title
        menu += "\n     ".join(["{: >2} {}".format(i+1,x) for i,x in enumerate(inputList)])
        if customOption and customKey:
            menu += "\n\n     " + "{: >2} {}".format(customKey, customOption)
        menu += "\n\n"
        print(menu)
        while True:
            wI = input(userPrompt)
            if not wI and len(inputList) > 1:
                return None
            if not wI and len(inputList) == 1:
                wI = "1" # Must be string
            if wI in "qQ": return None
            if customKey and wI.upper() == customKey:
                break
            try:
                wI = int(wI)
            except:
                continue
            else:
                if wI <= 0:
                    continue
                elif wI <= len(inputList):
                    break
        if isinstance(wI, int): return inputList[wI-1]
        elif wI.upper() == customKey: return customOption
    
    def _ui_get_full_website_name(prompt):
        """
        Prompt for full website name and return it
        
        """
        while True:
            wn = input(prompt)
            if not wn or wn in "qQ": _say_quit()
            if len(wn) > 100: # Keep it real
                print("  Error: Website name cannot exceed 100 characters.")
                continue
            break
        return re.sub(r"\s", " ", wn.strip()) # HTML escaping to be done on read
    
    def _data_file_corrupted_quit(workSite):
        """
        Exits with error message. Cannot happen, unless the data file
        is tampered with in some way
        
        """
        _say_error( "Error: The 'quicknr_private/quicknr_data.txt' file of '"+workSite+"' is\n"
                    "       corrupted and therefore untrusted. If you do not have\n"
                    "       a backup, remove the file and run Quicknr again.\n"
                    "       Further instructions will then appear.\n"
                    "       Quit.")
    
    def _ui_get_site_dir():
        """
        Prompts the user with list of websites, offers the option of 
        creating a new one, and returns the website folder name
        
        """        
        def _create_new_website():
            """
            Prompts user to create new website name and directory tree
            Updates website 'config.txt' file with full website name
            Records folder name in data file and returns the name
            
            """
            prompt = "\nEnter the FULL NAME of the website (or Q to quit): "
            r = _ui_get_full_website_name(prompt) # User may quit
            r = html.escape(r)
            while True:
                r1 = input( "\nEnter the website FOLDER name, using alphanumerical characters and\n"
                            "  the underscore (A-Za-z0-9_) only and no spaces (or Q to quit).\n"
                            "  Choose the name well, website folder names cannot be changed later: ")
                if not r1 or r1 in "qQ": _say_quit()
                if len(r1) > 50:
                    print("  Error: Website folder name cannot exceed 50 characters.")
                    continue
                if re.search("[^A-Za-z0-9_]", r1): continue
                if os.path.exists(os.path.join(qnrDir, "websites/" + r1)):
                    print("  Error: Website folder '%s' already exists." % r1)
                    continue
                break
            # --------------------- Make website folder tree
            wDirs = [   "websites/" + r1 + "/page_sources/news",
                        "websites/" + r1 + "/public_html/news/images",
                        "websites/" + r1 + "/public_html/res/css",
                        "websites/" + r1 + "/public_html/res/font",
                        "websites/" + r1 + "/public_html/res/img",
                        "websites/" + r1 + "/public_html/res/js",
                        "websites/" + r1 + "/quicknr_private"
                        ]
            for x in wDirs:
                os.makedirs(os.path.join(qnrDir, x))
            # --------------------- Copy Quicknr config folder to website
            cPath = os.path.join(qnrDir, "websites/" + r1 + "/config")
            shutil.copytree(os.path.join(qnrDir, "config"), cPath)
            # --------------------- Copy Quicknr Javascript files to website
            for x in ["javascript", "Javascript"]:
                if os.path.exists(os.path.join(qnrDir, x)):
                    jsPath = os.path.join(qnrDir, 
                                "websites/" + r1 + "/public_html/res/js")
                    # Copying function requires that dir not exist yet
                    os.rmdir(jsPath) # Expects empty dir, good
                    shutil.copytree(os.path.join(qnrDir, x), jsPath)
                    break
            # --------------------- Record website folder name in data file
            with open(os.path.join(qnrDir, 
                                    "websites/" + r1 + "/quicknr_private/quicknr_data.txt"), 
                                    mode="w") as f:
                f.write(r1 + "\n")
            # --------------------- Update config file with full website name
            with open(os.path.join(cPath, "config.txt"), mode="r") as f: fT = f.read()
            fT = re.sub(r"(?m)^(HTML_WEBSITE_NAME:).*?\n", 
                                            r'\1 "' + r + r'"\n', fT)
            with open(os.path.join(cPath, "config.txt"), mode="w") as f: f.write(fT)
            
            # --------------------- Detail the created directory tree
            report = "\n  New website folder '%s' has been created\n" % r1
            report += "  with the following sub-folders:\n"
            report += """
              /config/             - Website configuration files copied
                                     from the Quicknr config folder:
                                       * config.txt - website 
                                         preferences file
                                       * user_functions.py - Python
                                         script containing custom 
                                         functions used in this website
                                       
              /config/import/      - Files to be imported with import
                                     directives from head or tail
                                     snippets
                                       
              /page_sources/       - Location of your source files
                                     that will be combined with HTML
                                     head and tail snippets to form 
                                     HTML pages in the 'public_html'
                                     folder. Sources can be of two 
                                     types:
                                       * ".txt"/".mdml" files, that will
                                         be converted to HTML as Quicknr 
                                         Light Markup or Markdown
                                       * ".html", ".php" or ".htm"
                                         files, to be combined with
                                         snippets without conversion
                                         
              /page_sources/news/  - Location of source files that will
                                     be converted as detailed above, but
                                     are to be published as news, blog
                                     posts, latest updates.
                                     Converted HTML files will reside 
                                     in 'public_html/news'.
                                     
              /public_html/        - HTML pages fully created by you
                                     or converted from source files by
                                     Quicknr
                                     
              /public_html/news/   - News sources converted to HTML
                                     
              /public_html/news/images - Images used in news postings
                                         must be placed here
                                         
              /public-html/res/    - Resources folder, location of UI
                                     files in four sub-folders:
                                     
              /public-html/res/css - CSS stylesheet files
              /public-html/res/font - Custom fonts
              /public-html/res/img - Website interface images and icons
              /public_html/res/js  - Javascript files, including lib.js
                                     containing routine functions, and 
                                     news.js, continually updated by 
                                     Quicknr for dynamic Prev/Next news
                                     links
              
              /quicknr_private/    - Location of the 'quicknr_data.txt'
                                     file, used by Quicknr to perform its
                                     work. Must not be edited by user
            """
            print(report)
            return r1
        
        dL = os.listdir(qnrDir)
        if "websites" in dL:
            wL = os.listdir(os.path.join(qnrDir, "websites"))
            if wL:
                # No spaces allowed in website folder names
                if [x for x in wL if " " in x]:
                    _say_error( "Error: Website folder names must not contain spaces.\n"
                                "       Remove the spaces and try again.\n"
                                "       Quit.")
                # Choose or create website
                if len(wL) > 1: prompt = "Enter the number of website to work on,\n"
                else: prompt = "Press Return to work on your website,\n"
                prompt += "or N to create a new website (or Q to quit): "
                customOption = "Create a new website"
                wL.sort()
                # Prompt user with menu of choices
                wL.sort()
                workSite = _ui_list_menu(wL, "Websites", prompt, customOption, "N")
                if workSite == customOption:
                    workSite = _create_new_website()
                elif not workSite:
                    _say_quit()
                else:
                    # Check that it is a Quicknr website (config folder and data file)
                    # --------------------- Config check
                    if not os.path.exists(os.path.join(qnrDir, 
                                    "websites/"+workSite+"/config/config.txt")):
                        _say_error("ERROR: Configuration files for '"+workSite+"' are missing.\n" + \
                        "       A Quicknr website must contain a 'config' folder with files\n" + \
                        "       used for its setup and operation. Copy the folder from the\n" + \
                        "       Quicknr global folder into the website folder and try again.\n" + \
                        "       Quit.")
                    # --------------------- Data file check
                    wdf = os.path.join(qnrDir, 
                                    "websites/"+workSite+"/quicknr_private/quicknr_data.txt")
                    if os.path.exists(wdf):
                        with open(wdf, mode="r") as f: fT = f.read()
                        if not re.match(workSite, fT):
                            _data_file_corrupted_quit(workSite)
                    else:
                        with open(wdf, mode="w") as f: f.write(workSite+"\n")
                        _say_error("ERROR: Data file for '"+workSite+"' is missing.\n" + \
                        "       New data file has now been created, without records.\n" + \
                        "       When Quicknr runs next, all sources will be converted again and uploaded.\n" + \
                        "       If this is not a Quicknr website, it may not work.\n\n" + \
                        "NOTE:  All news pages converted to HTML again will be stamped with today's date\n" + \
                        "       as the date of publication. To prevent this, remove old source news\n" + \
                        "       files from the 'page_sources/news' directory of your website folder.\n" + \
                        "       Then Quicknr will not overwrite old HTML news files.\n" + \
                        "       Quit.")
            else: # No websites in folder
                print("  There are no websites to work on.\n  Let's create one.")
                workSite = _create_new_website()
        else: # No 'websites' folder, create it and try again
            os.mkdir(os.path.join(qnrDir, "websites"))
            return _ui_get_site_dir()
        return workSite
    
    # --------------------- CONTENT OBTAINING FUNCTIONS ---------------------
    # Obtain settings, snippets and content for later HTML file building
    
    def _import_files(pT):
        """
        Imports files from the "config/import" directory into html page text if it
        contains '@import: "file-to-import"' directives (placed there from HTML 
        head and tail snippets, or even from the source)
        
        See the "config.txt" for details of the naming convention used by the 
        import system
        
        """
        sys.setrecursionlimit(500) # Limit to stay safe
        while True:
            if "@import: " not in pT: return pT
            mo = re.search(r"@import:\s+['\"](.*?)['\"]\n*", pT)
            if not mo: return pT # Syntax error, give up silently
            fT = "" # !Needed if empty/non-matching file name (then drop directive)
            if mo.group(1): # We have a file name
                imFname = mo.group(1)
                # Drop extensions on import and target to compare base names only
                if "__" in imFname: imFname = imFname.split("__", maxsplit=1)[1]
                imFname = os.path.splitext(imFname)[0]
                sbName = os.path.splitext(os.path.basename(CD["sourceFilePath"]))[0]
                if imFname == sbName or imFname == "all" or (imFname == "newspost" and \
                    os.path.split(os.path.dirname(CD["sourceFilePath"]))[1] == "news"):
                        importPath = os.path.join(CD["siteDir"],"config/import/"+mo.group(1))
                        if not os.access(importPath, os.F_OK):
                            _say_error( "Error: File '{}' not found for import.\n"
                                        "       Quit.".format(mo.group(1)))
                        with open(importPath) as f: fT = f.read()
                        mc = re.match(r"(?m)(^#.*?$\n*)+", fT) # Ignore comments at top
                        if mc: fT = fT[mc.end():]
                        if "@import:" in fT:
                            fT = _import_files(fT) # Recurse
            pT = pT[:mo.start()]+fT+pT[mo.end():] # Insert, dropping directive
        return pT
    
    def _validate_correct_CD():
        """
        Validates CD values, and corrects some
        
        """
        nonlocal CD
        
        def _ve(s):
            """ Error call on the error """
            _say_error("Error: Invalid value in config: %s\n       Quit." % s)

        if CD["HTML_TITLE"] not in ["WEBSITE-PAGE", "WEBSITE", "PAGE"]:
            _ve("HTML_TITLE")
        if len(CD["HTML_TITLE_SEPARATOR"].strip()) > 3: _ve("HTML_TITLE_SEPARATOR")
        if CD["PAGE_FILE_EXTENSION"] not in [".html",".php",".htm"]:
            _ve("PAGE_FILE_EXTENSION")
        if CD["QLM_OR_MARKDOWN"] not in ["MARKDOWN","QLM"]: _ve("QLM_OR_MARKDOWN")
        if CD["MARKDOWN_TITLING"] not in ["YES","NO"]: _ve("MARKDOWN_TITLING")
        if CD["HTML_TAG_ID"] not in ["YES","NO"]: _ve("HTML_TAG_ID")
        try:
            if not CD["NEWS_LIST_ITEMS"].strip() or int(CD["NEWS_LIST_ITEMS"]) < 1:
                _ve("NEWS_LIST_ITEMS")
        except:
            _ve("NEWS_LIST_ITEMS")
        if not CD["NEWS_LIST_TITLE"].strip(): _ve("NEWS_LIST_TITLE")
        try:
            if not CD["NEWS_BLURB_LENGTH"].strip() or int(CD["NEWS_BLURB_LENGTH"]) < 1:
                _ve("NEWS_BLURB_LENGTH")
        except:
            _ve("NEWS_BLURB_LENGTH")
        if not CD["NEWS_MORE_PHRASE"].strip(): _ve("NEWS_MORE_PHRASE")
        # Escape <> in NEWS_MORE_PHRASE
        CD["NEWS_MORE_PHRASE"] = _html_escape_noamp(CD["NEWS_MORE_PHRASE"], quote=False)
        if not CD["NEWS_LIST_LINK"].strip(): _ve("NEWS_LIST_LINK") # Will be html.escaped
        if CD["NEWS_LIST_LINK_POSITION"].strip() not in ["START", "END"]:
            _ve("NEWS_LIST_LINK_POSITION")
        # News list link prefix can be empty, no validation, will be html.escaped
        if not CD["NEWS_DATE_FORMAT"].strip(): _ve("NEWS_DATE_FORMAT")
        if CD["NEWS_DATE_FROM_FILENAME"] not in ["YES","NO"]: _ve("NEWS_DATE_FROM_FILENAME")
        if not CD["NEWS_PREV_LINK"].strip(): _ve("NEWS_PREV_LINK")
        if not CD["NEWS_NEXT_LINK"].strip(): _ve("NEWS_NEXT_LINK")
        if CD["NEWS_LIST_THUMBS"] not in ["YES","NO"]: _ve("NEWS_LIST_THUMBS")
        if not re.match(r"\d+\Z", CD["NEWS_LIST_THUMB_SIZE"]): _ve("NEWS_LIST_THUMB_SIZE")
        if CD["NEWS_LIST_THUMB_SQUARE"] not in ["YES","NO"]: _ve("NEWS_LIST_THUMB_SQUARE")
        if CD["JAVASCRIPT_LINK_SPAN"] not in ["YES","NO"]: _ve("JAVASCRIPT_LINK_SPAN")
        if re.search(r"[^ A-Za-z0-9_\-'\.;:()]", CD["JAVASCRIPT_LINK_PRE"]): _ve("JAVASCRIPT_LINK_PRE")
        if re.search(r"[^ A-Za-z0-9_\-'\.;:()]", CD["JAVASCRIPT_LINK_POST"]): _ve("JAVASCRIPT_LINK_POST")
        if re.search(r'[ "<>]', CD["META_BASE_URL"]): _ve("META_BASE_URL")
        if CD["META_EDIT"] not in ["YES","NO"]: _ve("META_EDIT")
        if CD["META_DESCRIPTION"] not in ["YES","NO"]: _ve("META_DESCRIPTION")
        if CD["DEBUG_ERRORS"] not in ["YES","NO"]: _ve("DEBUG_ERRORS")
        # Leave out server values
        if CD["FTP_DEBUG"] not in ["0","1","2"]: _ve("FTP_DEBUG")
        if CD["ALWAYS_XHTML_TAGS"] not in ["YES","NO"]: _ve("ALWAYS_XHTML_TAGS")
        if CD["FILE_SIZE_LIMIT"] not in [True, False]: _ve("FILE_SIZE_LIMIT")
    
    def _get_site_config(CD):
        """
        Reads config.txt file from the website config folder, updating settings dict
        
        """
        
        prevCWD = os.getcwd()
        os.chdir(CD["siteDir"]) # Change CWD to website
        
        with open("config/config.txt", "r") as f: cT = f.read()
        rS = r"(?:\s|['\"])*$\n(^(?:.|\n)*?)['\"]{3}"
        rP = r"\s*['\"]?(.*?)['\"]?\s*?\n"
        if re.search(r"(?m)^HTML_HEAD:",cT):
            CD["HTML_HEAD"] = re.search(r"(?m)^HTML_HEAD:"+rS,cT).group(1)
        if re.search(r"(?m)^HTML_TAIL:",cT):
            CD["HTML_TAIL"] = re.search(r"(?m)^HTML_TAIL:"+rS,cT).group(1)
        if re.search(r"(?m)^HTML_TITLE:",cT):
            CD["HTML_TITLE"] = re.search(r"(?m)^HTML_TITLE:"+rP,cT).group(1)
        if re.search(r"(?m)^HTML_TITLE_SEPARATOR:",cT):
            CD["HTML_TITLE_SEPARATOR"] = re.search(r"(?m)^HTML_TITLE_SEPARATOR:"+rP,cT).group(1)
            CD["HTML_TITLE_SEPARATOR"] = _html_escape_noamp(CD["HTML_TITLE_SEPARATOR"])
        if re.search(r"(?m)^HTML_WEBSITE_NAME:",cT):
            CD["HTML_WEBSITE_NAME"] = re.search(r"(?m)^HTML_WEBSITE_NAME:"+rP,cT).group(1)
            CD["HTML_WEBSITE_NAME"] = _html_escape_noamp(CD["HTML_WEBSITE_NAME"], quote=False)
        if re.search(r"(?m)^HTML_PAGE_TITLE:",cT): # Will be escaped
            CD["HTML_PAGE_TITLE"] = re.search(r"(?m)^HTML_PAGE_TITLE:"+rP,cT).group(1)
        if re.search(r"(?m)^PAGE_FILE_EXTENSION:",cT):
            CD["PAGE_FILE_EXTENSION"] = re.search(r"(?m)^PAGE_FILE_EXTENSION:"+rP,cT).group(1)
        if re.search(r"(?m)^QLM_OR_MARKDOWN:",cT):
            CD["QLM_OR_MARKDOWN"] = re.search(r"(?m)^QLM_OR_MARKDOWN:"+rP,cT).group(1)
        if re.search(r"(?m)^MARKDOWN_TITLING:",cT):
            CD["MARKDOWN_TITLING"] = re.search(r"(?m)^MARKDOWN_TITLING:"+rP,cT).group(1)
        if re.search(r"(?m)^HTML_TAG_ID:",cT):
            CD["HTML_TAG_ID"] = re.search(r"(?m)^HTML_TAG_ID:"+rP,cT).group(1)
        if re.search(r"(?m)^NEWS_LIST_ITEMS:",cT):
            CD["NEWS_LIST_ITEMS"] = re.search(r"(?m)^NEWS_LIST_ITEMS:"+rP,cT).group(1)
        if re.search(r"(?m)^NEWS_LIST_TITLE:",cT):
            CD["NEWS_LIST_TITLE"] = re.search(r"(?m)^NEWS_LIST_TITLE:"+rP,cT).group(1)
        if re.search(r"(?m)^NEWS_BLURB_LENGTH:",cT):
            CD["NEWS_BLURB_LENGTH"] = re.search(r"(?m)^NEWS_BLURB_LENGTH:"+rP,cT).group(1)
        if re.search(r"(?m)^NEWS_MORE_PHRASE:",cT):
            CD["NEWS_MORE_PHRASE"] = re.search(r"(?m)^NEWS_MORE_PHRASE:"+rP,cT).group(1)
        if re.search(r"(?m)^NEWS_LIST_LINK:",cT):
            CD["NEWS_LIST_LINK"] = re.search(r"(?m)^NEWS_LIST_LINK:"+rP,cT).group(1)
        if re.search(r"(?m)^NEWS_LIST_LINK_POSITION:",cT):
            CD["NEWS_LIST_LINK_POSITION"] = re.search(r"(?m)^NEWS_LIST_LINK_POSITION:"+rP,cT).group(1)
        if re.search(r"(?m)^NEWS_LIST_LINK_PREFIX:",cT):
            CD["NEWS_LIST_LINK_PREFIX"] = re.search(r"(?m)^NEWS_LIST_LINK_PREFIX:"+rP,cT).group(1)
        if re.search(r"(?m)^NEWS_DATE_FORMAT:",cT):
            CD["NEWS_DATE_FORMAT"] = re.search(r"(?m)^NEWS_DATE_FORMAT:"+rP,cT).group(1)
        if re.search(r"(?m)^NEWS_DATE_FROM_FILENAME:",cT):
            CD["NEWS_DATE_FROM_FILENAME"] = re.search(r"(?m)^NEWS_DATE_FROM_FILENAME:"+rP,cT).group(1)
        if re.search(r"(?m)^NEWS_PREV_LINK:",cT):
            CD["NEWS_PREV_LINK"] = re.search(r"(?m)^NEWS_PREV_LINK:"+rP,cT).group(1)
        if re.search(r"(?m)^NEWS_NEXT_LINK:",cT):
            CD["NEWS_NEXT_LINK"] = re.search(r"(?m)^NEWS_NEXT_LINK:"+rP,cT).group(1)
        if re.search(r"(?m)^NEWS_LIST_THUMBS:",cT):
            CD["NEWS_LIST_THUMBS"] = re.search(r"(?m)^NEWS_LIST_THUMBS:"+rP,cT).group(1)
        if re.search(r"(?m)^NEWS_LIST_THUMB_SIZE:",cT):
            CD["NEWS_LIST_THUMB_SIZE"] = re.search(r"(?m)^NEWS_LIST_THUMB_SIZE:"+rP,cT).group(1)
        if re.search(r"(?m)^NEWS_LIST_THUMB_SQUARE:",cT):
            CD["NEWS_LIST_THUMB_SQUARE"] = re.search(r"(?m)^NEWS_LIST_THUMB_SQUARE:"+rP,cT).group(1)
        if re.search(r"(?m)^JAVASCRIPT_LINK_SPAN:",cT):
            CD["JAVASCRIPT_LINK_SPAN"] = re.search(r"(?m)^JAVASCRIPT_LINK_SPAN:"+rP,cT).group(1)
        if re.search(r"(?m)^JAVASCRIPT_LINK_PRE:",cT):
            CD["JAVASCRIPT_LINK_PRE"] = re.search(r"(?m)^JAVASCRIPT_LINK_PRE:"+rP,cT).group(1)
        if re.search(r"(?m)^JAVASCRIPT_LINK_POST:",cT):
            CD["JAVASCRIPT_LINK_POST"] = re.search(r"(?m)^JAVASCRIPT_LINK_POST:"+rP,cT).group(1)
        if re.search(r"(?m)^META_EDIT:",cT):
            CD["META_EDIT"] = re.search(r"(?m)^META_EDIT:"+rP,cT).group(1)
        if re.search(r"(?m)^META_DESCRIPTION:",cT):
            CD["META_DESCRIPTION"] = re.search(r"(?m)^META_DESCRIPTION:"+rP,cT).group(1)
        if re.search(r"(?m)^META_BASE_URL:",cT):
            CD["META_BASE_URL"] = re.search(r"(?m)^META_BASE_URL:"+rP,cT).group(1)
        if re.search(r"(?m)^DEBUG_ERRORS:",cT):
            CD["DEBUG_ERRORS"] = re.search(r"(?m)^DEBUG_ERRORS:"+rP,cT).group(1)
        if re.search(r"(?m)^FTP_SERVER:",cT):
            CD["FTP_SERVER"] = re.search(r"(?m)^FTP_SERVER:"+rP,cT).group(1)
        if re.search(r"(?m)^FTP_PATH:",cT):
            CD["FTP_PATH"] = re.search(r"(?m)^FTP_PATH:"+rP,cT).group(1)
        if re.search(r"(?m)^FTP_USERNAME:",cT):
            CD["FTP_USERNAME"] = re.search(r"(?m)^FTP_USERNAME:"+rP,cT).group(1)
        if re.search(r"(?m)^FTP_PASSWORD:",cT):
            CD["FTP_PASSWORD"] = re.search(r"(?m)^FTP_PASSWORD:"+rP,cT).group(1)
        if re.search(r"(?m)^FTP_ACCT:",cT):
            CD["FTP_ACCT"] = re.search(r"(?m)^FTP_ACCT:"+rP,cT).group(1)
        if re.search(r"(?m)^FTP_DEBUG:",cT):
            CD["FTP_DEBUG"] = re.search(r"(?m)^FTP_DEBUG:"+rP,cT).group(1)
        if re.search(r"(?m)^ALWAYS_XHTML_TAGS:",cT):
            CD["ALWAYS_XHTML_TAGS"] = re.search(r"(?m)^ALWAYS_XHTML_TAGS:"+rP,cT).group(1)
        os.chdir(prevCWD)
        _validate_correct_CD()
        return CD
    
    def _get_pages_folders(siteDir):
        """
        Checks whether 'page_sources' and 'public_html' folders exist
        in website folder. Quits if they don't
        
        If sources folder contains 'news' folder, any missing 'news' in 
        html folder is created, and both returned with main two folders
        in a list of lists
        
        """
        sourcesDirs = [os.path.join(siteDir, "page_sources")]
        htmlDirs = [os.path.join(siteDir, "public_html")]
        errorPrompt = ""
        if not os.path.exists(sourcesDirs[0]):
            errorPrompt = "Error: 'page_sources' folder not found.\n"
        if not os.path.exists(htmlDirs[0]):
            errorPrompt += "Error: 'public_html' folder not found.\n"
        if errorPrompt: _say_error(errorPrompt + "Quit.")
        if os.path.exists(os.path.join(sourcesDirs[0], "news")):
            sourcesDirs.append(os.path.join(sourcesDirs[0], "news"))
            # We have sources news folder, make html too if not there
            with suppress(OSError):
                os.makedirs(os.path.join(htmlDirs[0], "news/images")) # Creates missing dirs
            htmlDirs.append(os.path.join(htmlDirs[0], "news"))
        return [sourcesDirs, htmlDirs]
        
    def _get_pages_files(sourcesDirs, htmlDirs, qnrDT):
        """
        Returns a list of lists:
            sL - List of source files, relative to sources dir, no file extension
            sLx - Full source paths with file extensions
            sLxN - Full source paths that have no matching html counterpart
            sLxC - Full source paths that have a counterpart and differ from record
            hL - List of HTML files, relative to html dir, no file extension
        
        """
        def _source_changed(sourcePath, qnrDT, qnrDTL):
            """
            Returns true if the source doc does not match record in data file
            
            """
            # Need the relative path, with extension
            rfP = os.path.relpath(sourcePath, CD["siteDir"])
            if rfP not in qnrDT:
                # Source not in record, but has HTML counterpart, report as changed
                return True
            sF, hF = _file_size_and_hash(rfP)
            for x in qnrDTL:
                xL = x.split("\t")
                if xL[0] == rfP and (xL[2] != sF or xL[3] != hF):
                    return True
            return False
            
        sL = []; sLx = []; sLxN = []; sLxC = []; hL = []
        qnrDTL = qnrDT.splitlines()[1:] # Prepare for _source_changed()
        for sDir in sourcesDirs:
            for f in os.listdir(sDir):
                if os.path.splitext(f)[1] in [".txt", ".mdml", ".html", ".php", ".htm"]:
                    fP = os.path.join(sDir, f)
                    if CD["FILE_SIZE_LIMIT"] and os.path.getsize(fP) > 1100000:
                        _say_error( "Error: Source file '"+f+"' is over 1MB in size," + \
                                    " too large for publication.\n" + \
                                    "       Reduce the size to under 1MB and try again.\n"+\
                                    "       Quit.")
                    sLx.append(fP)
                    sL.append(os.path.splitext(os.path.relpath(fP, sourcesDirs[0]))[0])
        for hDir in htmlDirs:
            for f in os.listdir(hDir):
                if os.path.splitext(f)[1] in [".html", ".php", ".htm"]:
                    fP = os.path.join(hDir, f)
                    if CD["FILE_SIZE_LIMIT"] and os.path.getsize(fP) > 1100000:
                        _say_error( "Error: HTML file '"+f+"' is over 1MB in size," + \
                                    " too large for publication.\n" + \
                                    "       Reduce the size to under 1MB and try again.\n"+\
                                    "       Quit.")
                    hL.append(os.path.splitext(os.path.relpath(fP, htmlDirs[0]))[0])
        if not hL and sLx:
            sLxN = sLx[:]
        elif sL:
            for i, x in enumerate(sL):
                if x not in hL:
                    sLxN.append(sLx[i])
                elif _source_changed(sLx[i], qnrDT, qnrDTL):
                    sLxC.append(sLx[i])
        sL.sort(); sLx.sort(); sLxN.sort(); sLxC.sort(); hL.sort()
        return [sL, sLx, sLxN, sLxC, hL]
    
    def _save_image_thumbnail(filePath):
        """
        Resizes the image file to thumbnail, assumes img module available
        Returns thumb file path
        
        """
        size = int(CD["NEWS_LIST_THUMB_SIZE"]), int(CD["NEWS_LIST_THUMB_SIZE"])
        if not os.path.exists(filePath):
            _say_error( "Error: File '{}' not found.\n"
                        "       Thumbnail could not be created. Check your image links.\n"
                        "       Quit.".format(filePath))
        im = img.open(filePath)
        if CD["NEWS_LIST_THUMB_SQUARE"] == "YES":
            im = ImageOps.fit(im, size, img.ANTIALIAS, 0, (0.5,0.5))
        else:
            im.thumbnail(size, img.ANTIALIAS) # Size will control longest side
        fpThumb = os.path.splitext(filePath)[0] + "-thumb.jpg"
        im.save(fpThumb, "JPEG", optimize=True, quality=45)
        print("\n  Thumbnail generated for '%s'" % os.path.basename(filePath))
        return fpThumb


    # --------------------- HTML FILE BUILDING FUNCTIONS ---------------------
    
    def _enter_html_title():
        """
        Enters the HTML title from the settings dict in to the empty 
        <title></title> tag of HTML_HEAD snippet in the dict
        
        """
        nonlocal CD
        
        if "<title>" in CD["HTML_HEAD"]:
            # Clear any pre-existing title
            CD["HTML_HEAD"] = re.sub(r"(<title>)[^<]+(</title>)", r"\1\2", CD["HTML_HEAD"])
            # Process title to be acceptable for the <title> tag
            cleanTitle = _html_escape_noamp(_delete_inline_styling(CD["HTML_PAGE_TITLE"]), quote=False)
            if CD["HTML_TITLE"] == "WEBSITE-PAGE":
                if CD["HTML_PAGE_TITLE"]:
                    htmlTitle = CD["HTML_WEBSITE_NAME"] + CD["HTML_TITLE_SEPARATOR"] + \
                                                                cleanTitle
                else: htmlTitle = CD["HTML_WEBSITE_NAME"]
            elif CD["HTML_TITLE"] == "WEBSITE": htmlTitle = CD["HTML_WEBSITE_NAME"]
            elif CD["HTML_TITLE"] == "PAGE": htmlTitle = cleanTitle
            CD["HTML_HEAD"] = CD["HTML_HEAD"].replace( "<title></title>", 
                                                "<title>{}</title>".format(htmlTitle))

    def _bold_italic_mono(tT):
        """
        Converts inline text styling, bold, italic, monospaced (<code>)
        
        We use <span> for a sense of CSS 'neutrality', and easier 
        processing with regex
        
        """
        tT = re.sub(r"(?<!\w)[*_`]{3}([^ ].*?)[*_`]{3}(?!\w)", 
            r'<span style="font-weight:bold;font-style:italic"><code>\1</code></span>', tT)
        # Order matters here, catch double ** and __ as bold & italic, `` as italic
        tT = re.sub(r"(?<!\w)[*_]{2}([^ ].*?)[*_]{2}(?!\w)", 
            r'<span style="font-weight:bold;font-style:italic">\1</span>', tT)
        tT = re.sub(r"(?<!\w)[_`]{2}([^ ].*?)[_`]{2}(?!\w)", 
            r'<span style="font-style:italic"><code>\1</code></span>', tT)
        tT = re.sub(r"(?<!\w)[*`]{2}([^ ].*?)[*`]{2}(?!\w)", 
            r'<span style="font-weight:bold"><code>\1</code></span>', tT)
        tT = re.sub(r"(?<!\w)\*([^ ].*?)\*(?!\w)", r'<span style="font-weight:bold">\1</span>', tT)
        tT = re.sub(r"(?<!\w)_([^ ].*?)_(?!\w)", r'<span style="font-style:italic">\1</span>', tT)
        tT = re.sub(r"(?<!\w)`([^ ].*?)`(?!\w)", r"<code>\1</code>", tT)
        return tT
        
    def _delete_inline_styling(tT):
        """
        Deletes styling markup from text
        
        """
        tT = re.sub(r"(?<!\w)[*_`]+([^ ].*?)[*_`]+(?!\w)", r"\1", tT)
        return tT
    
    def _process_inline_markup(rT):
        """
        Converts inline markup to HTML and returns the text
        
        """
        # --------------------- Links
        if re.search(r"\[.+?\]", rT):
            
            # Javascript links as <span>
            if CD["JAVASCRIPT_LINK_SPAN"] == "YES":                
                x = '<span class="js_call" onclick="'+CD["JAVASCRIPT_LINK_PRE"]
                x += '\\2'+CD["JAVASCRIPT_LINK_POST"]+'">\\1</span>'
                rT = re.sub(r"\[(.+?)[ ]+([A-Za-z0-9_\-'\.;]+\([A-Za-z0-9_\-'\.;]*\))\]", x, rT)
                
                x = '<span class="js_call" onclick="'+CD["JAVASCRIPT_LINK_PRE"]
                x += '\\1'+CD["JAVASCRIPT_LINK_POST"]+'"></span>'
                rT = re.sub(r"\[([A-Za-z0-9_\-'\.;]+\([A-Za-z0-9_\-'\.;]*\))\]", x, rT)
                
            # Regular links as <a>
            rT = re.sub(r"\[(.+?)[ ]+(\S+?)\]", r'<a href="\2">\1</a>', rT)
            rT = re.sub(r"\[(\S+?)\]", r'<a href="\1">\1</a>', rT)
        
        # --------------------- Bold, italic and monospace in linked text
        def _inline_style_links(mo):
            """ Returns inline styled matches """
            return mo.group(1) + _bold_italic_mono(mo.group(2)) + mo.group(3)
        rT = re.sub(r"(>)([^<]+?)(</a>)", _inline_style_links, rT)

        # Delete styling in alt attributes, styling not valid here
        def _delete_inline_styling_call(mo):
            """ Deletes styling markup from matches """
            tT = _delete_inline_styling(mo.group(2))
            return mo.group(1) + tT + mo.group(3)
        rT = re.sub(r"( alt=\")([^\"]+)(\")", _delete_inline_styling_call, rT)
        
        # Correct http/www.
        rT = re.sub(r"(href|src)=\"www\.", r'\1="http://www.', rT)
        
        # --------------------- Styling outside links
        rT = _bold_italic_mono(rT)
        return rT
        

    def _plaintext_to_html(text, fX, relfPath):
        """
        Converts QLM (or Markdown if configured) plain text to HTML and returns it
        
        """
        nonlocal CD
        nonlocal preContentL
        #nonlocal jsLinkContentL
        
        if markdownModule and (fX == ".mdml" or CD["QLM_OR_MARKDOWN"] == "MARKDOWN"):
            # A compromise attempt at titling a Markdown page: first para up to 80 chars
            if CD["MARKDOWN_TITLING"] == "YES":
                mo = re.match(r"\S[^\n]{0,80}", text) # !No starting whitespace
                if mo: CD["HTML_PAGE_TITLE"] = mo.group().strip()
            return markdown_to_html(text)
        elif not markdownModule and fX == ".mdml":
            print("     File '%s' not converted, Markdown module not available." % relfPath)
            return None
        
        # --------------------- Convert text with Quicknr Light Markup
        
        title = ""
        titleAppear = True
        blocks = [] # List of 2-item lists of block & type ("title", "heading", "section")
        
        def _delete_leading_spaces(mo):
            """
            Deletes leading spaces in match object
            
            """
            return re.sub(r"\n[ ]+", r"\n", mo.group())
        
        def _link_type(sT):
            """
            Return link type of text: link, image, YTvideo
            
            """
            if "youtube" in sT.lower() or "youtu.be" in sT.lower(): return "YTvideo"
            for x in [".jpg",".png",".gif",".svg"]:
                if sT.lower().endswith(x) or sT.split("Quicknr?=IL=?Quicknr")[0].lower().endswith(x):
                    return "image"
            return "link"
        
        # --------------------- Text cleaning
        # Convert tabs to 4 spaces
        nT = text.replace("\t", "    ")
        # Quit if double quotes in URLs
        if re.search(r'\[(?:[^\[\]\n]+[ ])?[^ "\[\]\n]*?"[^ \[\]\n]*?\]', nT):
            _say_error( "Error: File '"+relfPath+"' contains\n"
                        "       an invalid URL. Correct and try again.\n"
                        "       Quit.")
        # Add line breaks at start/end (for sections)
        nT = "\n\n"+nT+"\n\n"
        # Convert any <> around URLs to [] ??
        #nT = re.sub(r"<[ ]*((?:\S+?\.)+\S+?)[ ]*>", r"[\1]", nT)
        # Escape HTML characters
        nT = _html_escape_noamp(nT, quote=False)
        # Revert &amp; back to & in links
        #nT = re.sub(r"(\[[^\]\n]*?[^ \]\n]+?)&amp;([^ \]\n]+\])", r"\1&\2", nT)
        # Protect code blocks, into their list
        for x in nT.strip().split("\n\n"):
            if re.match(r"(?i)code(?:-\w+)?:\s[ ]*\S",x):
                x = re.sub(r"\A\S[^:\n]*:\s?", "", x)
                preContentL.append(x)
        if preContentL:
            nT = re.sub(r"(?mi)(^code(?:-\w+)?:\s)(.+\n)+(?=\n)", r"\1Quicknr?=preText=?Quicknr\n", nT)
        # Protect Javascript link function arguments, into their list
        #for x in nT.strip().split("\n\n"):
            #for y in re.finditer(r"\[[^\[\]\n]+\(([^\n]*?)\);?\]",x):
                #jsLinkContentL.append(y.group(1))
        #if jsLinkContentL:
            #nT = re.sub(r"(?m)(\[[^\[\]\n]+\()[^\n]*?(\);?\])", r"\1Quicknr?=jsLinkArgs=?Quicknr\2", nT)
        # Delete trailing spaces (not line breaks)
        nT = re.sub(r"(?m)[ ]+$", "", nT)
        # Delete spaces within [] boundaries
        nT = re.sub(r"(\[)[ ]+", r"\1", nT)
        nT = re.sub(r"[ ]+(\])", r"\1", nT)
        # Delete single or double quotes surrounding link in []
        nT = re.sub(r"(\[)([^\]]+[ ])?([\"'])([^ \]]+)\3(\])", r"\1\2\4\5", nT)
        # Delete any duplicate brackets
        nT = re.sub(r"(\[|\])\1+", "\1", nT)
        # Unify image link pointing to link
        nT = re.sub(r"(\.jpg|\.png|\.gif|\.svg)\]\[", r"\1Quicknr?=IL=?Quicknr", nT)
        # Delete leading spaces in lists
        nT = re.sub(r"(?:\n+[ ]*\*[ ].+)(?:\n+[ ]*\*[ ].+)+", 
                                    _delete_leading_spaces, nT)
        nT = re.sub(r"(?:\n+[ ]*\d+\.?[ ].+)(?:\n+[ ]*\d+\.?[ ].+)+", 
                                    _delete_leading_spaces, nT)
        # Delete duplicate spaces after list prefixes
        nT = re.sub(r"(?m)^(\*[ ]|\d+\.?[ ])[ ]+", r"\1", nT)
        # Insert any missing line break before list (corrected next)
        nT = re.sub(r"((?:\n+[ ]*\*[ ].+)(?:\n+[ ]*\*[ ].+)+)", r"\n\1", nT)
        nT = re.sub(r"((?:\n+[ ]*\d+\.?[ ].+)(?:\n+[ ]*\d+\.?[ ].+)+)", r"\n\1", nT)
        # Delete empty lines in lists
        nT = re.sub(r"(?<=\n)(\*[ ].+\n)\n+(?=\*[ ])", r"\1", nT)
        nT = re.sub(r"(?<=\n)(\d+\.?[ ].+\n)\n+(?=\d+\.?[ ])", r"\1", nT)
        # Max two line breaks
        nT = re.sub(r"(\n\n)\n+", r"\1", nT)
        
        # --------------------- Title
        mo = re.match(r"\n*[ ][ ]+\S.{0,80}\n\n+", nT)
        if mo:
            title = mo.group().strip()
            if title.startswith("[") and title.endswith("]"):
                titleAppear = False
                title = title[1:-1]
        if title:
            if titleAppear: blocks.append([title, "title"])
            # Update config
            CD["HTML_PAGE_TITLE"] = title # Already escaped, and will be again
            nT = re.sub(r"\A\s*\S.*", "", nT)
        
        # --------------------- Headings sections
        while True:
            mo = re.search(r"\n\n+([ ][ ]+\S.*)\n\n+", nT) # !No length limit
            if mo:
                tS = nT[:mo.start(1)]
                if tS.strip(): blocks.append([tS, "section"])
                nT = nT[mo.end(1):]
                blocks.append([mo.group(1).strip(), "heading"])
            else:
                blocks.append([nT, "section"])
                # nT now consumed and transfered to blocks
                break
        
        # --------------------- Process blocks
        sCount = 0 # Section/heading counter, 0-indexed for no headings
        for i, b in enumerate(blocks):
            if b[1] == "title":
                blocks[i][0] = '<h1 class="title">%s</h1>' % b[0]
            if b[1] == "heading":
                sCount += 1
                hhh = '<h2 class="heading {} heading_{}">{}</h2>'
                blocks[i][0] = hhh.format(sCount%2 and "odd" or "even",sCount,b[0]) 
            if b[1] == "section":
                # Delete leading spaces in section
                sT = re.sub(r"(?m)^[ ]+", "", b[0])
                nS = "" # New section
                pCount = 0 # Paragraph block counter, 1-indexed within section
                dCount = 0 # Definition list count
                cCount = 0 # Code block count
                iCount = 0 # Image block count
                fCount = 0 # Image float count
                vCount = 0 # Video count
                lCount = 0 # List count
                for pT in sT.split("\n\n"):
                    if not pT.strip(): continue
                    
                    # --------------------- Link block types: link, image, video
                    if pT and pT.startswith("[") and pT.endswith("]") and \
                                    "[" not in pT[1:-1] and "]" not in pT[1:-1]:
                        linkType = _link_type(pT[1:-1])
                        # Separate link text and link URL
                        if " " in pT:
                            linkText, linkURL = pT[1:-1].rsplit(maxsplit=1)
                        else:
                            if linkType != "image" and linkType != "YTvideo":
                                linkText = pT[1:-1]
                            else:
                                linkText = ""
                            linkURL = pT[1:-1] # May not equal linkText later
                        if re.search(r'["]', linkURL):
                            _say_error( "Error: File '"+relfPath+"' contains\n"
                                        "       an invalid URL. Correct and try again.\n"
                                        "       Quit.")
                        # Escape quotes, not done earlier
                        origLinkText = linkText[:] # Copy to preserve original for comparing
                        linkText = linkText.replace("'", "&#x27;").replace('"', "&quot;")
                        # Handle different link block types
                        if linkType == "link":
                            pCount += 1
                            if CD["JAVASCRIPT_LINK_SPAN"] == "YES" and re.match(r"[^():]+\([^()]*\)",linkURL):
                                if origLinkText == linkURL: linkText = " " # Prevent empty tag
                                if re.search(r"[^A-Za-z0-9_\-'\.;()]", linkURL):
                                    _say_error( "Error: File '"+relfPath+"' contains an invalid\n"
                                                "       Javascript function call. Correct and try again.\n"
                                                "       Quit.")
                                linkURL = CD["JAVASCRIPT_LINK_PRE"] + linkURL + CD["JAVASCRIPT_LINK_POST"]
                                pT = '<p class="p_{} link_p {} section_{}"><span class="js_call" onclick="{}">{}</span></p>'
                                pT = pT.format(pCount,pCount%2 and "odd" or "even",sCount,linkURL,linkText)
                            else:
                                pT = '<p class="p_{} link_p {} section_{}"><a href="{}">{}</a></p>'
                                pT = pT.format(pCount,pCount%2 and "odd" or "even",sCount,linkURL,linkText)
                        elif linkType == "image":
                            clickLinkURL = "" # Handle images as links
                            if "Quicknr?=IL=?Quicknr" in linkURL:
                                linkURL, clickLinkURL = linkURL.split("Quicknr?=IL=?Quicknr", maxsplit=1)
                                if "Quicknr?=IL=?Quicknr" in clickLinkURL:
                                    _say_error( "Error: File '"+relfPath+"' contains one or more\n"
                                                "       image link sequences of more than two [] parts.\n"
                                                "       Correct and try again.\n"
                                                "       Quit.")
                            iCount += 1
                            pT = '<div class="imgblock imgblock_{} {} section_{}">\n'
                            if clickLinkURL:
                                if CD["JAVASCRIPT_LINK_SPAN"] == "YES" and re.match(r"[^():]+\([^()]*\)",clickLinkURL):
                                    if re.search(r"[^A-Za-z0-9_\-'\.;()]", clickLinkURL):
                                        _say_error( "Error: File '"+relfPath+"' contains an invalid\n"
                                                    "       Javascript function call. Correct and try again.\n"
                                                    "       Quit.")
                                    clickLinkURL = CD["JAVASCRIPT_LINK_PRE"] + clickLinkURL + CD["JAVASCRIPT_LINK_POST"]
                                    pT = '<div class="imgblock link_img imgblock_{} {} section_{}">\n<span class="js_call"'
                                    pT += ' onclick="{}">\n'
                                else:
                                    pT = '<div class="imgblock link_img imgblock_{} {} section_{}">\n<a href="{}">\n'
                            pT += '<img src="{}" alt="{}" />\n'
                            if clickLinkURL:
                                pT = pT.format(iCount,iCount%2 and "odd" or "even",
                                                sCount,clickLinkURL,linkURL,linkText)
                            else:
                                pT = pT.format(iCount,iCount%2 and "odd" or "even",
                                                sCount,linkURL,linkText)
                            if clickLinkURL:
                                if '<span class="js_call"' in pT:
                                    pT += '</span>\n'
                                else:
                                    pT += '</a>\n'
                            if linkText: pT += '<p class="imgcaption">{}</p>\n'.format(linkText)
                            pT += '</div>'
                        elif linkType == "YTvideo":
                            vCount += 1
                            # Need the space between <iframe> tags for xml formatter
                            pT = '<div class="ytvideo vidblock_{} {} section_{}">\n<iframe src="{}" '
                            pT += 'frameborder="0" allowfullscreen="allowfullscreen"> </iframe>\n'
                            pT = pT.format(vCount,vCount%2 and "odd" or "even",sCount,linkURL)
                            pT += '</div>'
                    
                    # --------------------- Import and Python directives
                    elif re.match(r"@python:|@import:", pT):
                        pass # Don't convert directives to HTML
                    
                    # --------------------- Lists
                    elif len(re.findall(r"(?m)^\*[ ]", pT)) > 1: # Unordered list
                        lCount += 1
                        liCount = 0 # List item count
                        npT1 = ""
                        for x in re.findall(r"(?m)^\*[ ]+(.+)$", pT):
                            liCount += 1
                            npT = '<li class="li_{} {}">{}</li>\n'
                            npT1 += npT.format(liCount, liCount%2 and "odd" or "even", x)
                        pT = '<ul class="list_{} {} section_{}">\n{}</ul>'
                        pT = pT.format(lCount, lCount%2 and "odd" or "even", sCount, npT1)
                    elif len(re.findall(r"(?m)^\d+\.?[ ]", pT)) > 1: # Ordered list
                        lCount += 1
                        liCount = 0
                        npT1 = ""
                        for x in re.findall(r"(?m)^\d+\.?[ ]+(.+)$", pT):
                            liCount += 1
                            npT = '<li class="li_{} {}">{}</li>\n'
                            npT1 += npT.format(liCount, liCount%2 and "odd" or "even", x)
                        pT = '<ol class="list_{} {} section_{}">\n{}</ol>'
                        pT = pT.format(lCount, lCount%2 and "odd" or "even", sCount, npT1)
                    
                    # --------------------- Code block (must come before the next test)
                    elif "Quicknr?=preText=?Quicknr" in pT and pT.lower().startswith("code"):
                        cCount += 1
                        pT1 = pT.split(":", 1)[0]
                        npT = '<div class="{} codeblock_{} {} section_{}">\n{}\n</div>'
                        pT = '<pre class="code">Quicknr?=preText=?Quicknr</pre>'
                        dClass = pT1.lower()
                        if dClass != "code": dClass = "code "+dClass
                        pT = npT.format(dClass,cCount,cCount%2 and "odd" or "even",sCount,pT)
                    
                    # --------------------- Note: etc. definition
                    elif re.match(r"(?:\w+:\s*\S)|(?:\S[^:\n]*:\n[ ]*\S)",pT):
                        dCount += 1
                        pT1 = pT.split(":", 1)[0]; pT = re.sub(r"\A\S[^:\n]*:\s?", "", pT)
                        npT = '<dl class="{} dlblock dlblock_{} {} section_{}">\n'
                        npT += '<dt>{}</dt>\n<dd>{}</dd>\n</dl>'
                        dClass = pT1.lower()
                        if " " in dClass: dClass = "definition"
                        pT = npT.format(dClass,dCount,dCount%2 and "odd" or "even",sCount,pT1,pT)
                    
                    # --------------------- Image float before paragraph
                    elif re.match(r"\[.+?(?:\.jpg|\.png|\.gif|\.svg)(?:Quicknr\?=IL=\?Quicknr[^\]]+)?\][ ]*\S.+",pT):
                        linkURL, ppT = pT[1:].split("]", maxsplit=1)
                        ppT = ppT.strip()
                        # Image part of paragraph
                        if " " in linkURL:
                            linkText, linkURL = linkURL.rsplit(maxsplit=1)
                            linkText = linkText.replace("'", "&#x27;").replace('"', "&quot;")
                        else:
                            linkText = ""
                        if re.search(r'["]', linkURL):
                            _say_error( "Error: File '"+relfPath+"' contains\n"
                                        "       an invalid URL. Correct and try again.\n"
                                        "       Quit.")
                        clickLinkURL = "" # Handle images as links
                        if "Quicknr?=IL=?Quicknr" in linkURL:
                            linkURL, clickLinkURL = linkURL.split("Quicknr?=IL=?Quicknr", maxsplit=1)
                            if "Quicknr?=IL=?Quicknr" in clickLinkURL:
                                _say_error( "Error: File '"+relfPath+"' contains one or more\n"
                                            "       image link sequences of more than two [] parts.\n"
                                            "       Correct and try again.\n"
                                            "       Quit.")
                        fCount += 1;
                        ipT = '<div class="imgfloat imgfloat_{} {} section_{}">\n'
                        if clickLinkURL:
                            if CD["JAVASCRIPT_LINK_SPAN"] == "YES" and re.match(r"[^():]+\([^()]*\)",clickLinkURL):
                                if re.search(r"[^A-Za-z0-9_\-'\.;()]", clickLinkURL):
                                    _say_error( "Error: File '"+relfPath+"' contains an invalid\n"
                                                "       Javascript function call. Correct and try again.\n"
                                                "       Quit.")
                                clickLinkURL = CD["JAVASCRIPT_LINK_PRE"] + clickLinkURL + CD["JAVASCRIPT_LINK_POST"]
                                ipT = '<div class="imgfloat link_img imgfloat_{} {} section_{}">\n<span class="js_call"'
                                ipT += ' onclick="{}">\n'
                            else:
                                ipT = '<div class="imgfloat link_img imgfloat_{} {} section_{}">\n<a href="{}">\n'
                        ipT += '<img src="{}" alt="{}" />\n'
                        if clickLinkURL:
                            ipT = ipT.format(fCount,fCount%2 and "odd" or "even",sCount,
                                                        clickLinkURL,linkURL,linkText)
                        else:
                            ipT = ipT.format(fCount,fCount%2 and "odd" or "even",sCount,
                                                        linkURL,linkText)
                        if clickLinkURL:
                            if '<span class="js_call"' in ipT:
                                ipT += '</span>\n'
                            else:
                                ipT += '</a>\n'
                        if linkText: ipT += '<p class="imgcaption">{}</p>\n'.format(linkText)
                        ipT += '</div>'
                        # Text part of paragraph
                        pCount += 1
                        pT = '<p class="p_{} img_p {} section_{}">{}</p>'
                        pT = pT.format(pCount, pCount%2 and "odd" or "even", sCount, ppT)
                        # Image and text combo
                        pT = ipT + "\n" + pT
                    
                    # --------------------- Paragraph
                    else:
                        pCount += 1
                        npT = '<p class="p_{} {} section_{}">{}</p>'
                        pT = npT.format(pCount,pCount%2 and "odd" or "even",sCount,pT)
                    # Combine with new section
                    nS = nS + pT + "\n"
                hhh = '<div class="section {} section_{}">\n{}\n</div>'
                blocks[i][0] = hhh.format(sCount%2 and "odd" or "even",sCount,nS[:-1])
        # Combine blocks
        rT = ""
        sCount = 0
        for i, x in enumerate(blocks):
            # Surround heading & section pairs with div
            if x[1] == "heading":
                sCount += 1
                if len(blocks) > i+1 and blocks[i+1][1] == "section":
                    hhh = '<div class="headed_section {} section_{}">\n{}'
                    x[0] = hhh.format(sCount%2 and "odd" or "even",sCount,x[0])
                    blocks[i+1][0] += '\n</div>'
            rT += x[0] + "\n"
        
        # --------------------- Delete empty sections
        rT = re.sub(r"\s*<div [^>]+>\s*</div>", "", rT)
        # --------------------- Process inline markup
        rT = _process_inline_markup(rT)
        
        # Final wrap (penultimate actually; by default, head snippet adds <div class="page">)
        # Place file name in class for main div (if it is "html clean")
        docN = ""
        if not re.search(r"[<>\"'&]", os.path.splitext(os.path.basename(CD["sourceFilePath"]))[0]):
            docN = os.path.splitext(os.path.basename(CD["sourceFilePath"]))[0]
        # If news post, insert link to news listing, named per pref
        hCode = ""
        if os.path.split(os.path.dirname(CD["sourceFilePath"]))[1] == "news":
            hCode = '<div class="news_links">\n<span class="listing_link">'
            hCode += '<a href="../news{}">{}{}</a></span>\n</div>\n'
            hCode = hCode.format(   CD["PAGE_FILE_EXTENSION"],
                                    _html_escape_noamp(CD["NEWS_LIST_LINK_PREFIX"]),
                                    _html_escape_noamp(CD["NEWS_LIST_LINK"]))
        if CD["NEWS_LIST_LINK_POSITION"] == "START":
            rT = "<div class=\"user_content "+docN+"\">\n"+hCode+rT+"</div>\n"
        else:
            rT = "<div class=\"user_content "+docN+"\">\n"+rT+hCode+"</div>\n"
        return rT
    
    def _get_file_record_date(filePath, wT=""):
        """
        Returns the date recorded with the relative file path in quicknr_data.txt
        The return is a date object or None
        
        """
        # If record exists, obtain its date
        if not wT:
            with open(os.path.join(CD["siteDir"], "quicknr_private/quicknr_data.txt"), mode="r") as f:
                wT = f.read()
        rfP = os.path.relpath(filePath, CD["siteDir"])
        if rfP in wT:
            for x in wT.splitlines()[1:]:
                if x.split("\t")[0] == rfP:
                    ods = x.split("\t")[1]; ot = ods.split("_")[1]; ods = ods.split("_")[0]
                    oh, omin, osec = ot.split("-") # Hour, minute, second
                    oy, om, od = ods.split("-") # Year, month, day
                    return dt.datetime(int(oy),int(om),int(od),int(oh),int(omin),int(osec))
            else: # No break
                _data_file_corrupted_quit(CD["siteFolder"])
        else: return None
    
    def _get_date_from_filename(filePath, mode="record"):
        """
        Returns string-formatted date from filename of filePath, if named in
        this format, with first word as YYYYMMDD:
        
            20160401-april-fools-joke.txt
        
        Returns today's date if the first word of the filename is not a date, 
        or throws an error if date numbers are in an invalid range
        
        The date is formatted according to mode, "record", "news_list" or "news_stamp"
        
        """
        mo = re.match(r"\d{8}(?=\D)", os.path.basename(filePath))
        if mo:
            dY = int(mo.group()[:4])
            dM = int(mo.group()[4:6])
            dD = int(mo.group()[6:8])
            try:
                if mode == "record":
                    # Construct date component from filename
                    dDate = dt.datetime(dY, dM, dD).strftime("%Y-%m-%d")
                    # Set the time component to present time
                    dTime = dt.datetime.now().strftime("_%H-%M-%S")
                    return dDate + dTime
                elif mode == "news_stamp":
                    return dt.datetime(dY, dM, dD).strftime(CD["NEWS_DATE_FORMAT"])
                elif mode == "news_list":
                    return dt.datetime(dY, dM, dD).strftime("%Y-%b-%d")
            except Exception as e: # In case the date cannot be constructed from filename
                print("Error: Invalid date in filename '"+os.path.basename(filePath)+"':")
                print(e)
                _say_quit()
        else:
            # Date not in filename, return today's
            if mode == "record":
                return dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            elif mode == "news_stamp":
                return dt.date.today().strftime(CD["NEWS_DATE_FORMAT"])
            elif mode == "news_list":
                return dt.date.today().strftime("%Y-%b-%d")
    
    def _news_date_stamp(text, wdataT):
        """
        Inserts the current date, in a format set by the configuration, at the
        start of the <div class="user_content"> tag, if the file being
        worked on is new and in the 'page_sources/news/' folder
        
        Existing news files are dated by their original date from the record
        
        Any additional "Published on " phrase is left to CSS
        
        """
        if os.path.split(os.path.dirname(CD["sourceFilePath"]))[1] == "news":
            dDate = _get_file_record_date(CD["sourceFilePath"], wdataT)
            if dDate:
                dTime = dDate.strftime(CD["NEWS_DATE_FORMAT"])
            else:
                if CD["NEWS_DATE_FROM_FILENAME"] == "YES":
                    dTime = _get_date_from_filename(CD["sourceFilePath"],mode="news_stamp")
                else:
                    dTime = dt.date.today().strftime(CD["NEWS_DATE_FORMAT"])
            rT = re.sub(r"(<div class=\"user_content[^>\"]*?\">)", 
                            r'\1\n<p class="news_date_stamp">{}</p>'.format(dTime), text)
            return rT
        else: return text
    
    def _get_news_post_img_url(newsT):
        """
        Returns the first image url in news post or empty. URL is relative
        to "public_html", containing "news.html" listing file
        
        """
        mo = re.search(r"(?m)^\[([^\]]+?(?:\.jpg|\.png|\.gif))\]", newsT)
        if mo:
            imgURL = mo.group(1)
            if len(imgURL.split()) > 1: # Drop non-URL part if any
                imgURL = imgURL.rsplit(maxsplit=1)[1]
            # Return if it's an external link
            if re.match(r"http|www\.", imgURL): return imgURL
            # Resolve relative URL
            if imgURL.startswith("../"):
                imgURL = imgURL[3:]
                # Return empty if illegal URL out of "public_html"
                if imgURL.startswith("../"): return ""
                return imgURL
            else:
                imgURL = "news/" + imgURL
                return imgURL
        return ""
    
    def _get_news_post_thumb_url(newsT):
        """
        Returns either the thumb or full-size image URL for first image in news post,
        depending on whether a thumb is available, or PIL can be used to create it
        
        Returns empty if no image found
        
        """
        mo = re.search(r"(?m)^\[([^\]]+?(?:\.jpg|\.png|\.gif))\]", newsT)
        if mo:
            imgURL = mo.group(1)
            if len(imgURL.split()) > 1: # Drop non-URL part if any
                imgURL = imgURL.rsplit(maxsplit=1)[1]
            # Return if it's an external link
            if re.match(r"http|www\.", imgURL): return imgURL
            # Resolve relative URL
            if imgURL.startswith("../"):
                imgURL = imgURL[3:]
                # Return empty if illegal URL out of "public_html"
                if imgURL.startswith("../"): return ""
            else: imgURL = "news/" + imgURL
            thumbPath, fXt = os.path.splitext(imgURL)
            # If image is a thumb itself, return it
            if thumbPath.endswith("thumb"):
                return imgURL
            for x in ["thumb","-thumb","_thumb"]:
                if os.path.exists(os.path.join(CD["siteDir"], "public_html/"+thumbPath+x+fXt)):
                    return thumbPath+x+fXt
            # Thumb file not found, try to create it, if PIL available
            if imgModule:
                tP = _save_image_thumbnail(os.path.join(CD["siteDir"],"public_html/"+imgURL))
                return os.path.relpath(tP, os.path.join(CD["siteDir"], "public_html/"))
            else:
                return imgURL
        else:
            return ""

    def _indent_html_tree(text):
        """
        Returns HTML text as indented tree
        
        """
        # Record line numbers of lines with opening and closing tags:
            # For every opener, qualify it by searching for a matching closer:
                # If closer found, increase indent level for content down from opener
                # If no closer found, keep indent level as is
            # For every closer down, decrease indent level for it and for content down
        # Apply indents to the lines, not if text content
        
        # Remove leading whitespace before tags at line starts
        text = re.sub(r"(?m)^\s+(<)", r"\1", text)
        
        indentsL = []
        indentLevel = 0
        tL = text.splitlines()
        for i, tLine in enumerate(tL):
            mo = re.match(r"<(\w+|!--)", tLine)
            if mo:
                if "</"+mo.group(1)+">" not in tLine: # Not closed inline
                    if len(tL) > i+1: # Account for possibly last line (redundant?)
                        mo1 = re.search(r"(?m)^</"+mo.group(1)+">", "\n".join(tL[i+1:]))
                        if mo1:
                            # Check for an inline closer before mo1, not a nester
                            checkT = "\n".join(tL[i+1:])[:mo1.start()]
                            mo2 = re.search(r"</"+mo.group(1)+">",checkT)
                            if mo2:
                                if "<"+mo.group(1) not in checkT[:mo2.start()]:
                                    continue
                            # mo is confirmed as an opener, increase indent for lines down
                            indentLevel += 1
                            indentsL.append([i+1, indentLevel])
                        # else: No change to indentsL, keep existing indent
            else:
                mo = re.match(r"</\w", tLine)
                if mo:
                    # mo is confirmed as a closer, decrease indent
                    indentLevel -= 1
                    indentsL.append([i, indentLevel])
            # If neither opener nor closer found, it is content text that won't be indented
        indentLevel = 0
        for i, tLine in enumerate(tL[:]): # Copy
            for x in indentsL:
                if i == x[0]: # indent level change
                    indentLevel = x[1]
                    #break # Don't break, need to consider all
            if tLine.startswith("<"): # Not content text
                tL[i] = "  "*max(0,indentLevel) + tLine
            # else: Content text, not indenting
        text = "\n".join(tL)
        return text
    
    def _set_title_from_filename(filename):
        """
        Sets CD["HTML_PAGE_TITLE"] to the title derived from filename
        
        """
        nonlocal CD
        
        if filename == "index":
            title = "Home"
        else:
            title = filename.replace("-", " ").replace("_", " ").title()
        CD["HTML_PAGE_TITLE"] = html.escape(title)
    
    def _get_news_listing_items(fxNC, htmlDirs, wdataT):
        """
        Returns components of the news item source text:
            - date (in "%Y-%b-%d" format)
            - news item title
            - HTML file path
            - first image
            - first image as linked thumb
            - first paragraph
        
        Assumes that the title is in the CD variable and HTML file path is known
        
        """
        # Get title, first paragraph, and file path relative to html dir
        #nhTitle = html.unescape(CD["HTML_PAGE_TITLE"])
        nhTitle = CD["HTML_PAGE_TITLE"]
        # ...but the unescape doesn't catch everything, so we correct
        #nhTitle = re.sub(r"&amp;([A-Za-z0-9#]{2,8};)", r"&\1", nhTitle)
        nhFP = "" # First paragraph
        with open(fxNC, mode="r") as f: fT = f.read()
        # Get first image URL from news post (for <meta> cards), could be empty
        nhImg = _get_news_post_img_url(fT)
        # Get first image URL from news post (if thumbs are enabled), thumb if possible
        nhImgThumb = ""; nhImgThumbLink = ""
        if CD["NEWS_LIST_THUMBS"] == "YES":
            nhImgThumb = _get_news_post_thumb_url(fT)
            if nhImgThumb: nhImgThumbLink = "[" + nhImgThumb + "]"
        # Get first paragraph, skip headings, link paras, img floats & directives
        fT = re.sub(r"(?:@import:|@python:) \"[^\"\n]*\"", "", fT)
        fT = re.sub(r"(?m)^\[[^\n]+?\]$", "", fT)
        fT = re.sub(r"(?m)^\[[^\n]+?(?:\.jpg|\.png|\.gif|\.svg)\] (\S)",r"\1",fT)
        mo = re.search(r"(?m)^\S.+?$(?=\n\n)", fT)
        if mo: nhFP = mo.group()
        # Get rid of any links in first paragraph
        if "[" in nhFP and "]" in nhFP:
            nhFP = re.sub(r"\[+[ ]*([^ \]]+)[ ]*\]+", r"\1", nhFP)
            nhFP = re.sub(r"\[+[ ]*([^\]]+?)[ ]+[^ \]]+[ ]*\]+", r"\1", nhFP)
        elif len(nhFP) > int(CD["NEWS_BLURB_LENGTH"]): # Nicely shorten by word
            nhFP = nhFP[:int(CD["NEWS_BLURB_LENGTH"])].rsplit(maxsplit=1)[0]+"..."
        nhPath = os.path.relpath(CD["htmlFilePath"], htmlDirs[0])
        if nhImgThumbLink: nhImgThumbLink += "[" + nhPath + "] " # Make thumb link to post
        # Date: get record or from filename or today's
        dD = _get_file_record_date(fxNC, wdataT)
        if dD:
            dDS = dD.strftime("%Y-%b-%d")
        else:
            if CD["NEWS_DATE_FROM_FILENAME"] == "YES":
                dDS = _get_date_from_filename(fxNC, mode="news_list")
            else:
                dDS = dt.date.today().strftime("%Y-%b-%d")
        return dDS, nhTitle, nhPath, nhImg, nhImgThumb, nhImgThumbLink, nhFP
        
    def _edit_card_titles(hT):
        """
        Returns HTML text with Open Graph and Twitter Card <meta> title tags
        edited to contain the full title of the page from <title></title>
        
        """
        fullTitle = re.search(r"<title>([^<]+)</title>", hT)
        if fullTitle:
            tt = _html_escape_noamp(fullTitle.group(1)) # Needed again, escaping quotes
            hT = re.sub(r'<meta [^>]*?((?:name|property)=["\'](?:og|twitter):title["\'])[^>]*>', 
                                    '<meta \\1 content="'+tt+'" />', hT)
        return hT
        
    def _edit_canonical_url(hT, docPath):
        """
        Returns HTML text with canonical <link> tag edited to the URL of
        the current page. The <link> tag is assumed to exist already, this
        code does not create it
        
        Does the same for Open Graph URL <meta> tag
        
        """
        # Construct URL from html file path
        linkURL = urljoin(CD["META_BASE_URL"], pathname2url(docPath))
        # Replace in text
        hT = re.sub(r'<link [^>]*?(rel=["\']canonical["\'])[^>]*>', 
                                    '<link \\1 href="'+linkURL+'" />', hT)
        hT = re.sub(r'<meta [^>]*?((?:name|property)=["\']og:url["\'])[^>]*>', 
                                    '<meta \\1 content="'+linkURL+'" />', hT)
        return hT
        
    def _edit_meta_cards(hT, nhTitle, nhFP, nhPath, nhImg):
        """
        Returns HTML text with <meta> og and twitter cards edited with
        data from the calling news post: title, description, url & image
        
        If META_DESCRIPTION is YES, regular <meta name="description"...> tag
        will be edited as well
        
        The <meta> tags are assumed to exist already, this code does not
        create them
        
        """
        # Remove text styling markup from title & description, html escape
        nhTitle = _html_escape_noamp(_delete_inline_styling(nhTitle))
        ogDesc = _html_escape_noamp(_delete_inline_styling(nhFP))
        # Construct URL from html file path
        ogURL = ""
        if CD["META_BASE_URL"]:
            ogURL = urljoin(CD["META_BASE_URL"], pathname2url(nhPath))
        # Construct image URL from image file path
        ogImg = ""
        if nhImg and CD["META_BASE_URL"]:
            if nhImg.startswith("http"): ogImg = nhImg
            elif nhImg.startswith("www."): ogImg = "http://" + nhImg
            else: ogImg = urljoin(CD["META_BASE_URL"], pathname2url(nhImg))
        # Replace in text
        if nhTitle:
            hT = re.sub(r'<meta [^>]*?((?:name|property)=["\'](?:og|twitter):title["\'])[^>]*>', 
                                    '<meta \\1 content="'+nhTitle+'" />', hT)
        if ogDesc:
            hT = re.sub(r'<meta [^>]*?((?:name|property)=["\'](?:og|twitter):description["\'])[^>]*>', 
                                    '<meta \\1 content="'+ogDesc+'" />', hT)
            if CD["META_DESCRIPTION"] == "YES":
                hT = re.sub(r'<meta [^>]*?(name=["\']description["\'])[^>]*>', 
                                        '<meta \\1 content="'+ogDesc+'" />', hT)
        if ogImg:
            hT = re.sub(r'<meta [^>]*?((?:name|property)=["\'](?:og|twitter):image["\'])[^>]*>', 
                                    '<meta \\1 content="'+ogImg+'" />', hT)
        if ogURL:
            hT = re.sub(r'<meta [^>]*?((?:name|property)=["\']og:url["\'])[^>]*>', 
                                        '<meta \\1 content="'+ogURL+'" />', hT)
        return hT

    def _convert_sources_to_html(sourcesDirs, htmlDirs, sLxNC, wdataT):
        """
        Converts source ".txt"/".mdml" files that are either new or the user
        has changed, to HTML. Also concatenates any HTML source files with
        configuration snippets into output HTML files without conversion
        
        """
        nonlocal CD
        nonlocal preContentL
        #nonlocal jsLinkContentL
        nonlocal rebuildNewsList
        
        # Execute user functions file
        if os.path.exists(os.path.join(CD["siteDir"], "config/user_functions.py")):
            with open(os.path.join(CD["siteDir"], "config/user_functions.py")) as f:
                userFunctions = f.read()
            exec(userFunctions)
        else: _say_error("Error: 'user_functions.py' file is missing. Quit.")
        
        # Sort old news according to date, for correct listing
        sLxNC1 = []
        oNL = [] # List of 2-item lists of [date, path] of old news
        nNL = [] # New news files not in record
        for x in sLxNC:
            if os.path.split(os.path.dirname(x))[1] == "news":
                if os.path.relpath(x, CD["siteDir"]) in wdataT:
                    wD = _get_file_record_date(x, wdataT)
                    oNL.append([wD.strftime("%Y-%m-%d_%H-%M-%S"), x])
                else:
                    nNL.append(x)
            else:
                sLxNC1.append(x)
        oNL.sort()
        nNL.sort() # Might be worth it if named well (would be if dating from filename)
        sLxNC1.sort()
        sLxNC1.extend([y for x, y in oNL])
        sLxNC1.extend(nNL)
        sLxNC = sLxNC1[:]
        
        if updateNewsList:
            sLxNC.append(os.path.join(sourcesDirs[0], "news.txt"))
        convertedFiles = []
        for i, fxNC in enumerate(sLxNC):
            fX = os.path.splitext(fxNC)[1]
            relfxNC = os.path.relpath(fxNC, CD["siteDir"])
            # Markdown not supported for news
            if os.path.split(os.path.dirname(fxNC))[1] == "news" and \
                        (fX == ".mdml" or CD["QLM_OR_MARKDOWN"] == "MARKDOWN"):
                print("       File '%s' not converted, Markdown not supported for news." % relfxNC)
                continue
            preContentL = [] # Clear list of <pre> instances
            #jsLinkContentL = [] # Ditto js link args
            docType = "" # Clear docType declaration
            print("\n  Converting to HTML (file {} of {}):".format(i+1, len(sLxNC)))
            print("       " + relfxNC)
            with open(fxNC, mode="r") as f:
                hT = f.read()
            # Protect links in news files before we prepend ../ to links from snippets
            if os.path.split(os.path.dirname(fxNC))[1] == "news":
                hT = re.sub(r"(\[(?:[^\]]+[ ])?)([^ \]]+\])", r"\1Quicknr__newsLink__Quicknr\2", hT)
            # Update CD with source file path
            CD["sourceFilePath"] = fxNC
            # Keep file extension, will change later if ".txt"/".mdml"
            hF = os.path.join(htmlDirs[0], os.path.relpath(fxNC, sourcesDirs[0]))
            # Process only if source is ".txt" or ".mdml"
            if fX == ".txt" or fX == ".mdml":
                # Updates CD html page title
                hT = _plaintext_to_html(hT, fX, relfxNC)
                if not hT: continue # Markdown processing attempt without module
                # Update CD html head snippet with title
                _enter_html_title()
                # Change source ".txt"/".mdml" extension to HTML config preference
                hF = os.path.splitext(hF)[0] + CD["PAGE_FILE_EXTENSION"]
            else:
                # File types other than ".txt"/".mdml" get title from filename
                _set_title_from_filename(os.path.splitext(os.path.basename(fxNC))[0])
                _enter_html_title()
            # Store doctype, we may need it later
            if re.match(r"\s*<!DOCTYPE[^>]+>", CD["HTML_HEAD"]):
                docType = re.match(r"\s*<!DOCTYPE[^>]+>\n", CD["HTML_HEAD"]).group()
                
            # Combine with snippets
            hT = CD["HTML_HEAD"] + hT + CD["HTML_TAIL"]
            # Update CD with html file path
            CD["htmlFilePath"] = hF
            # Date stamp for news, using original date from record if editing old news
            hT = _news_date_stamp(hT, wdataT)
            
            # Get imports, before <meta>/<link> tags are edited, so they can be
            #   imported conditionally first
            hT = _import_files(hT)
            
            # --------------------- Meta tag edits
            if CD["META_EDIT"] == "YES":
                if os.path.splitext(os.path.basename(fxNC))[0] != "index":
                    # Edit Open Graph and Twitter card <meta> titles
                    # Home page is left at pre-existing value
                    hT = _edit_card_titles(hT)
                if CD["META_BASE_URL"]:
                    # Edit canonical <link> and OG URL <meta> tags to page URL
                    docPath = os.path.relpath(CD["htmlFilePath"], htmlDirs[0])
                    hT = _edit_canonical_url(hT, docPath)
            
            # --------------------- If news post, prepare for listing "news.txt" 
            #                           & get data for <meta> cards
            if os.path.split(os.path.dirname(fxNC))[1] == "news":
                # We read plain text original, so not affected by links protection above
                dDS, nhTitle, nhPath, nhImg, nhImgThumb, nhImgThumbLink, nhFP = \
                                        _get_news_listing_items(fxNC, htmlDirs, wdataT)
                
                # --------------------- Edit news <meta> tags in HTML, OG and Twitter
                if CD["META_EDIT"] == "YES":
                    hT = _edit_meta_cards(hT, nhTitle, nhFP, nhPath, nhImg)
                        
            # Prepend local links with "../" if file in news subfolder
            if os.path.split(os.path.dirname(fxNC))[1] == "news":
                hT = re.sub(r"((?:href|src)=\")(?!(?:\.\./|http:|https:|file:|ftp:|javascript:|mailto:))", 
                                                                    r"\1../",hT)
                hT = re.sub(r"((?:href|src)=\")\.\./(#)", r"\1\2", hT) # Correction (for bug?)
                hT = re.sub(r"(?:\.\./)?Quicknr__newsLink__Quicknr", "", hT) # Ditto
                hT = re.sub(r"((?:href|src)=\")(www\.)", r"\1http://\2", hT)
                
            # Process user functions
            if "@python:" in hT:
                while True:
                    if not hT:
                        _say_error( "Error: Processing aborted on '{}', no text available.\n"
                                    "       Check that a Python function is not failing to return.\n"
                                    "       Quit.".format(relfxNC))
                    mo = re.search(r"@python:\s+['\"](.*?)['\"]\n*", hT)
                    if not mo: break
                    # Lose the directive
                    hT = hT[:mo.start()]+hT[mo.end():]
                    if mo.group(1): # We have a function name
                        # No exception handling at this level
                        hT = eval(mo.group(1) + "(hT, " + str(mo.start()) + ", CD)")
                
            # Enter IDs in DIV, P, H1-6, IMG, IFRAME, DL, DT, DD, OL, UL, and LI
            if CD["HTML_TAG_ID"] == "YES":
                idCount = 0
                def _id_generator(mo):
                    """Enters numerical series of IDs into tags"""
                    nonlocal idCount
                    if ' id="' in mo.group():
                        return mo.group()
                    else:
                        idCount += 1
                        return r'{} id="id{}"{}'.format(mo.group(1),idCount,mo.group(2))
                hT = re.sub(r"(<(?:div|p|h\d|img|iframe|dl|dt|dd|ol|ul|li)(?:[ ][^>]*?)*?)(/?>)", 
                                                                    _id_generator, hT)
            
            # Put back spaces at /> tag ends (id generating above)
            hT = re.sub(r"(?<![ ])(/>)", r" \1", hT)
            hT = re.sub(r" ( id=\")", r"\1", hT)
            # Remove empty lines & whitespace between tags
            hT = re.sub(r">\s*\n\s*<",">\n<",hT)
            # Remove whitespace between closing tag and punctuation
            hT = re.sub(r"(</[^>]+>)\s+(?=[,.?!'\"\)])", r"\1", hT)
            # Remove whitespace at start of <p> block 
            # for Chrome's handling of white-space CSS
            hT = re.sub(r"(<p [^>]+>)\s+", r"\1", hT)
            
            hT = _indent_html_tree(hT)
            # Bring in <pre> code text (protected earlier)
            if preContentL:
                for x in preContentL:
                    #x = html.escape(x, quote=False) # Done already
                    hT = hT.replace(">Quicknr?=preText=?Quicknr</pre>", ">" + x + "</pre>", 1)
            # Bring in Javascript link argument text (protected earlier)
            #if jsLinkContentL:
                #for x in jsLinkContentL:
                    ##x = html.escape(x, quote=False) # Done already
                    #hT = hT.replace("(Quicknr?=jsLinkArgs=?Quicknr)", "(" + x + ")", 1)
            # Correct overzealous char entity conversion of &
            hT = re.sub(r"&amp;([A-Za-z0-9#]{2,8};)", r"&\1", hT)
            # Remove whitespace around &nbsp;
            hT = re.sub(r"\s*(&nbsp;)\s*", r"\1", hT)
            
            # --------------------- Fill out and insert news list item block
            if os.path.split(os.path.dirname(fxNC))[1] == "news":
                if nhImgThumb:
                    nlib = newsListItemBlock.replace("DATE_TEXT", dDS)
                    nlib = nlib.replace("THUMB_URL", nhImgThumb)
                else: # No thumbnail
                    nlib = newsListItemBlockNoThumb.replace("DATE_TEXT", dDS)
                nlib = nlib.replace("POST_URL", nhPath)
                nlib = nlib.replace("HEADING_TEXT", 
                        _bold_italic_mono(_html_escape_noamp(nhTitle, quote=False)))
                nlib = nlib.replace("BLURB_TEXT", 
                        _bold_italic_mono(_html_escape_noamp(nhFP, quote=False)))
                nlib = nlib.replace("MORE_TEXT", CD["NEWS_MORE_PHRASE"])
                # Place news list item block into news post HTML
                hT = re.sub(r"(<div class=\"user_content[^>]+?>)",r'\1{}'.format(nlib),hT)
            
            # --------------------- Final
            # HTML5 tags correction from Quicknr's internal XHTML
            if CD["ALWAYS_XHTML_TAGS"] == "NO":
                if re.match(r"(?i)\s*<\s*!\s*doctype\s+html\s*>", hT):
                    hT = re.sub(r"\s*/>", ">", hT)
            # Write HTML file
            with open(hF, mode="w") as f:
                f.write(hT)
            relhF = os.path.relpath(hF, CD["siteDir"])
            # Return both source and html relative paths
            convertedFiles.append(relhF)
            convertedFiles.append(relfxNC)
            print("  Converted file:\n       " + relhF)
            
            # --------------------- If this was a news post, list in "news.txt"
            if os.path.split(os.path.dirname(fxNC))[1] == "news":
                # Construct news listing item; linked heading and a para: title, img & intro
                nhNItem = "   _"+dDS+"_ ["+nhTitle+" "+nhPath+"]\n\n"+\
                                    nhImgThumbLink+nhFP+" ["+CD["NEWS_MORE_PHRASE"]+" "+nhPath+"]"
                # --------------------- News listing source file
                nlT = ""
                if not rebuildNewsList:
                    if os.path.exists(os.path.join(sourcesDirs[0], "news.txt")):
                        with open(os.path.join(sourcesDirs[0], "news.txt"), mode="r") as f:
                            nlT = f.read()
                rebuildNewsList = False # Re-set variable, must only be considered once
                if not nlT:
                    nlT = "   "+CD["NEWS_LIST_TITLE"]+"\n\n"
                else:
                    # Replace title with preference
                    nlT = re.sub(r"\A\s*.+\n", "   "+CD["NEWS_LIST_TITLE"]+"\n", nlT)
                # Insert updated news item in its slot, replacing original
                if nhPath in nlT:
                    nlL = nlT.split("\n\n")
                    for i, x in enumerate(nlL):
                        if nhPath in x: # Got the first occurrence, replace it
                            nlT = "\n\n".join(nlL[:i])+"\n\n"+nhNItem+"\n\n"+"\n\n".join(nlL[i+2:])
                            break
                else: # New news item, place it between title and first old item
                    nlT = nlT.split("\n\n")[0]+"\n\n"+nhNItem+"\n\n"+nlT.split("\n\n",maxsplit=1)[1]
                # Shorten list length to config preference by dropping last news item
                niCount = len(nlT.split("\n\n")[1:-1])
                if niCount > 2*int(CD["NEWS_LIST_ITEMS"]):
                    niCount = niCount - (2*int(CD["NEWS_LIST_ITEMS"])) + 1
                    nlT = "\n\n".join(nlT.split("\n\n")[:-niCount])+"\n\n"
                # Tidy up, just in case
                nlT = re.sub(r"[ ]+\n", "\n", nlT)
                nlT = re.sub(r"(\n\n)\n+", r"\1", nlT)
                # Write news listing file
                with open(os.path.join(sourcesDirs[0], "news.txt"), mode="w") as f:
                    f.write(nlT)
        return convertedFiles
    
    def _record_new_files(convertedFiles, qnrDataPath, fT):
        """
        Record converted source and resulting HTML files in quicknr_data.txt as 
        tab-delimited fields. Overwrites pre-existing records of the same name
        
        Record format: filepath,time,size,hash,NOTUP|UP
        
        filepath - relative to website folder
        time - date and time of entry, in 'Year-Month-Day_Hour-Min-Sec' format
        size - file size in bytes
        hash - hexadecimal digest of file contents
        NOTUP|UP - not uploaded|uploaded (HTML files only)
        
        """
        convertedFiles = list(set(convertedFiles)) # Get rid of duplicates ("news.txt")
        convertedFiles.sort()
        nfRecords = []
        recordsDeleted = False
        fTL = fT.splitlines()[1:]
        for x in convertedFiles:
            d = dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") # Must be here
            sF, hF = _file_size_and_hash(x) # May quit, if file over 1MB
            if re.match(r".?public_html", x):
                nfRecords.append(x+"\t"+d+"\t"+sF+"\t"+hF+"\tNOTUP")
            else: # Source file
                # Get date of old news file instead of using today's
                if os.path.split(os.path.dirname(x))[1] == "news":
                    dD = _get_file_record_date(os.path.join(CD["siteDir"], x), fT)
                    if dD:
                        d = dD.strftime("%Y-%m-%d_%H-%M-%S")
                    else: # New news file, no recorded date
                        if CD["NEWS_DATE_FROM_FILENAME"] == "YES":
                            d = _get_date_from_filename(x, mode="record")
                nfRecords.append(x+"\t"+d+"\t"+sF+"\t"+hF)
            if fTL: # Check for matching file names
                if x in fT:
                    for o in fTL:
                        if o.split("\t", 1)[0] == x:
                            fT = re.sub(r"(?m)^"+x+r"\t.+?\n", "", fT)
                            recordsDeleted = True
                            break # Only one match possible
                    else: # No break
                        _data_file_corrupted_quit(CD["siteFolder"])
        if recordsDeleted:
            with open(qnrDataPath, mode="w") as f: f.write(fT)
        rT = "\n".join(nfRecords)
        if rT[-1] != "\n": rT += "\n"
        with open(qnrDataPath, mode="a") as f: f.write(rT)
    
    def _record_news_images(imgFiles, qnrDataPath):
        """
        Record news image files in quicknr_data.txt as tab-delimited fields if image
        is new or, if changed in size, overwrite pre-existing record of same name
        
        Record format: filepath,time,size,NOTUP|UP
        
        filepath - relative to website folder
        time - date and time of entry, in 'Year-Month-Day_Hour-Min-Sec' format
        size - file size in bytes
        NOTUP|UP - not uploaded|uploaded
        
        """
        d = dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        nfRecords = []
        recordsDeleted = False
        with open(qnrDataPath, mode="r") as f: fT = f.read()
        fTL = fT.splitlines()[1:]
        for x in imgFiles:
            filePath = os.path.join(CD["siteDir"], x)
            sF = os.path.getsize(filePath) # Bytes
            if CD["FILE_SIZE_LIMIT"] and sF > 1100000:
                _say_error( "Error: File '"+x+"' is over 1MB in size,\n" + \
                            "         too large for publication.\n" + \
                            "       Reduce the size to under 1MB and try again.\n" + \
                            "       Quit.")
            if x not in fT:
                nfRecords.append(x+"\t"+d+"\t"+str(sF)+"\tNOTUP")
            else: # Check for matching file name and changed size
                for o in fTL:
                    if o.split("\t")[0] == x:
                        if o.split("\t")[2] != str(sF):
                            nfRecords.append(x+"\t"+d+"\t"+str(sF)+"\tNOTUP")
                            fT = re.sub(r"(?m)^"+x+r"\t.+?\n", "", fT)
                            recordsDeleted = True
                        break # Only one name match is possible
                else: # No break
                    _data_file_corrupted_quit(CD["siteFolder"])
        if nfRecords:
            if recordsDeleted:
                with open(qnrDataPath, mode="w") as f: f.write(fT)
            rT = "\n".join(nfRecords)
            if rT[-1] != "\n": rT += "\n"
            with open(qnrDataPath, mode="a") as f: f.write(rT)
    
    def _get_records_to_upload(qnrDataPath):
        """
        Looks for data file records of files to upload and returns them
        Records of any non-existent files are removed from the data file
        
        """
        recordsToUpload = []; recordsDeleted = False
        with open(qnrDataPath, mode="r") as f: fT = f.read()
        for x in fT.splitlines()[1:]:
            if os.path.exists(os.path.join(CD["siteDir"], x.split("\t", 1)[0])):
                if "\tNOTUP" in x:
                    recordsToUpload.append(x)
            else:
                fT = fT.replace("\n"+x, "")
                recordsDeleted = True
        if recordsDeleted:
            with open(qnrDataPath, mode="w") as f: f.write(fT)
        return recordsToUpload
    
    def _manage_server_files(recordsToUse, workMode, qnrDataPath):
        """
        If workMode = "upload"
            uploads files to server and updates data file
            recordsToUse are expected to be data records
                or file paths relative to siteDir
        
        If workMode = "delete"
            deletes files
            recordsToUse are expected to be file paths relative to siteDir
        
        """
        if not CD["FTP_SERVER"] or not CD["FTP_USERNAME"] or not CD["FTP_PATH"]:
            _say_error( "Error: No FTP server or username or path set in configuration.\n"
                        "       Quit.")
        if not CD["FTP_PASSWORD"]:
            CD["FTP_PASSWORD"] = getpass.getpass("Enter your FTP password (or Q to quit): ")
            if not CD["FTP_PASSWORD"] or CD["FTP_PASSWORD"] in "qQ": _say_quit()
        with open(qnrDataPath, mode="r") as f: fT = f.read()
        print("Connecting to FTP server: {}".format(CD["FTP_SERVER"]))
        try:
            with ftp.FTP(CD["FTP_SERVER"],CD["FTP_USERNAME"],CD["FTP_PASSWORD"],CD["FTP_ACCT"]) as fc:
                # --------------------- Start FTP connection
                if CD["FTP_DEBUG"] == "1" or CD["FTP_DEBUG"] == "2":
                    fc.set_debuglevel(int(CD["FTP_DEBUG"]))
                print("\n"+fc.getwelcome())
                # Will throw error if path does not exist, cannot create dir
                fc.cwd(CD["FTP_PATH"])
                print("\n"+fc.pwd())
                fc.dir(); print("")
                for x in recordsToUse:
                    if workMode == "upload":
                        if x in fT: fP = x.split("\t", 1)[0]
                        else: fP = x[:] # Copy
                    elif workMode == "delete":
                        fP = x[:]
                    fN = os.path.basename(fP); fD = os.path.dirname(fP)
                    # --------------------- Get sub-folders
                    subDs = []; splitfD = [fD]
                    if os.path.split(fD)[0]: # Head and tail, slash char in fD
                        while True:
                            splitfD = os.path.split(splitfD[0])
                            if splitfD[0]: subDs.append(splitfD[1])
                            else: break
                        subDs.reverse()
                        for a in subDs:
                            try: fc.cwd(a)
                            except:
                                if workMode == "upload":
                                    fc.mkd(a)
                                    fc.cwd(a)
                                elif workMode == "delete":
                                    fc.quit()
                                    _say_error( "Error: Directory '"+a+"' not found on server.\n"+\
                                                "       File '"+x+"' not deleted.\n"+\
                                                "       Quit.\n")
                    print("\n"+fc.pwd())
                    if workMode == "upload":
                        # --------------------- Upload
                        print("  Uploading file '{}' ...".format(fP), end="")
                        with open(os.path.join(CD["siteDir"], fP), mode="rb") as uf:
                            fc.storbinary("STOR "+fN, uf)
                            print(" Done.")
                    elif workMode == "delete":
                        # --------------------- Delete
                        print("  Deleting file '{}' ...".format(fP), end="")
                        fc.delete(fN)
                        print(" Done.")
                    if subDs: fc.cwd("../"*len(subDs))
                    if workMode == "upload":
                        # --------------------- Update data file
                        if x in fT and "\t" in x: # Separate out argparse files
                            parts = fT.partition(x) # x is whole line from record
                            fT = parts[0]+parts[1].rsplit("\t", 1)[0]+"\tUP"+parts[2]
        except Exception as e:
            print(e) # No need for full trace, just print the error
            _say_quit()
        else:
            if workMode == "upload":
                with open(qnrDataPath, mode="w") as f: f.write(fT)
                print("\nUploading completed.")
            elif workMode == "delete":
                print("\nFile deletion from server completed.")
    
    def _mark_all_changed(wdT):
        """
        Marks all source files in data record as changed, to be converted again
        
        """
        wL = wdT.splitlines()
        if not wL[-1]: wL = wL[:-1] # Drop empty line at end
        if len(wL) < 2:
            return wdT # No record of files
        xts = [".txt", ".mdml", ".html", ".php", ".htm"]
        changed = False
        for i, x in enumerate(wL):
            if i > 0 and "\t" in x: # Skip first line, site folder name
                xL = x.split("\t")
                if re.match(r".?page_sources", xL[0]) and os.path.splitext(xL[0])[1] in xts:
                    # Change recorded file size to 0
                    wL[i] = xL[0] + "\t" + xL[1] + "\t0\t" + "\t".join(xL[3:])
                    changed = True
        if changed: return "\n".join(wL) + "\n"
        else: return wdT
    
    def _get_files_for_upload(mode):
        """
        Returns relative paths to files in folder suggested by mode
        
        """
        if mode == "all": subPath = "public_html"
        elif mode == "res": subPath = "public_html/res"
        elif mode == "css": subPath = "public_html/res/css"
        elif mode == "js": subPath = "public_html/res/js"
        elif mode == "font": subPath = "public_html/res/font"
        elif mode == "img": subPath = "public_html/res/img"
        else: return None
        rPaths = []
        for dp, dns, fns in os.walk(os.path.join(CD["siteDir"], subPath)):
            for fn in fns:
                rPaths.append(os.path.relpath(os.path.join(dp, fn), CD["siteDir"]))
        return rPaths
    
    def _check_file_folder_names():
        """
        Checks that all files in the website folder have file extensions
        and no spaces or html <>&"' characters in their names
        
        Conversely, checks that folders have no spaces, html characters and 
        no extensions
        
        """
        fpL = []; spL = []; dxL = []; dsL = []; fhL = []; dhL = []
        for dp, dn, fns in os.walk(CD["siteDir"]):
            for d in dn:
                if " " in d:
                    dsL.append(os.path.relpath(os.path.join(dp, d), CD["siteDir"]))
                if os.path.splitext(d)[1]:
                    dxL.append(os.path.relpath(os.path.join(dp, d), CD["siteDir"]))
                if "<" in d or ">" in d or "&" in d or "'" in d or '"' in d:
                    dhL.append(os.path.relpath(os.path.join(dp, d), CD["siteDir"]))
            for fn in fns:
                if " " in fn:
                    spL.append(os.path.relpath(os.path.join(dp, fn), CD["siteDir"]))
                if not os.path.splitext(fn)[1]:
                    fpL.append(os.path.relpath(os.path.join(dp, fn), CD["siteDir"]))
                if "<" in fn or ">" in fn or "&" in fn or "'" in fn or '"' in fn:
                    fhL.append(os.path.relpath(os.path.join(dp, fn), CD["siteDir"]))
        if spL:
            sp = "\n         ".join(spL)
            _say_error( "Error: some files in '{}' have spaces in their names:\n\n"
                        "           {}\n\n"
                        "       Fix and try again.\n"
                        "       Quit.".format(CD["siteFolder"],sp))
        if fpL:
            sp = "\n         ".join(fpL)
            _say_error( "Error: some files in '{}' do not have file extensions like\n"
                        "       '.txt', '.html', '.jpg', etc.:\n\n"
                        "           {}\n\n"
                        "       Fix and try again.\n"
                        "       Quit.".format(CD["siteFolder"],sp))
        if fhL:
            sp = "\n         ".join(fhL)
            _say_error( "Error: some files in '{}' have html characters in their names:\n\n"
                        "           {}\n\n"
                        "       Fix and try again.\n"
                        "       Quit.".format(CD["siteFolder"],sp))
        if dsL:
            sp = "\n         ".join(dsL)
            _say_error( "Error: some folders in '{}' have spaces in their names:\n\n"
                        "           {}\n\n"
                        "       Fix and try again.\n"
                        "       Quit.".format(CD["siteFolder"],sp))
        if dxL:
            sp = "\n         ".join(dxL)
            _say_error( "Error: some folders in '{}' have file extensions:\n\n"
                        "           {}\n\n"
                        "       Fix and try again.\n"
                        "       Quit.".format(CD["siteFolder"],sp))
        if dhL:
            sp = "\n         ".join(dhL)
            _say_error( "Error: some folders in '{}' have html characters in their names:\n\n"
                        "           {}\n\n"
                        "       Fix and try again.\n"
                        "       Quit.".format(CD["siteFolder"],sp))
    
    def _get_news_file_list(qnrDataPath):
        """
        Returns list of 2-item lists of news date and HTML files, 
        matching sources from record, sorted by date
        
        """
        with open(qnrDataPath, mode="r") as f: fT = f.read()
        nfL = [] # List of 2-item lists of news date and HTML file rel URL
        for line in fT.splitlines()[1:]:
            pfP = line.split("\t", maxsplit=1)[0]
            if re.match(r".?page_sources", pfP) and os.path.split(os.path.dirname(pfP))[1] == "news":
                # We allow Markdown files for any future compatibility
                if os.path.splitext(pfP)[1] in [".txt", ".mdml"]:
                    x = os.path.join(CD["siteDir"], pfP)
                    wD = _get_file_record_date(x, fT)
                    xbn = os.path.splitext(os.path.basename(x))[0] # No extension
                    for y in fT.splitlines()[1:]:
                        ypfP = y.split("\t", maxsplit=1)[0]
                        if re.match(r".?public_html", ypfP) and os.path.split(os.path.dirname(ypfP))[1] == "news":
                            ybn = os.path.splitext(os.path.basename(ypfP))[0] # No ext
                            if ybn == xbn: # HTML file name matches txt source
                                nfL.append([wD.strftime("%Y-%m-%d_%H-%M-%S"), os.path.basename(ypfP)])
                                break
        nfL.sort()
        return nfL
    
    def _check_files_for_news(fList):
        """
        Returns true if file list contains news
        
        """
        for x in fList:
            if "\t" in x: x = x.split("\t", maxsplit=1)[0]
            if os.path.split(os.path.dirname(x))[1] == "news" or \
                        os.path.splitext(os.path.basename(x))[0] == "news":
                return True
        return False
    
    
    # --------------------- TOOLS MODE ---------------------
    
    def _tool_delete_news_post(qnrDataPath):
        """
        Deletes a news post by deleting:
            * source text file
            * converted HTML file, if any
            * news item from news listing file
            * record from list in news.js
            * record from data file
            * if uploaded already, HTML file from server
        
        """
        
        # --------------------- Get news post to delete, source & html
        
        filesToDelete = []
        nfL = os.listdir(os.path.join(CD["siteDir"], "page_sources/news"))
        if len(nfL) == 0:
            _say_error("Error: No news posts to delete.\n       Quit.")
        elif len(nfL) < 2:
            _say_error( "Error: A news post cannot be deleted if no others would remain.\n"
                        "       Create another first, then try again.\n"
                        "       Quit.")
        nfL.sort(reverse=True) # Good naming strategy is assumed...
        nfL = nfL[:99] # Shorten file list to what UI can handle
        print("")
        prompt = "Enter the number of the news post to delete (or Q to quit): "
        delF = _ui_list_menu(nfL, "Delete News Post", prompt)
        if not delF: _say_quit()
        filesToDelete.append(os.path.join(CD["siteDir"], "page_sources/news/"+delF))
        # Find HTML counterpart
        for x in os.listdir(os.path.join(CD["siteDir"], "public_html/news")):
            if os.path.splitext(x)[0] == os.path.splitext(delF)[0]:
                filesToDelete.append(os.path.join(CD["siteDir"], "public_html/news/"+x))
                break
        print("\nYou are about to delete:\n")
        for x in filesToDelete:
            print("  "+os.path.relpath(x, os.path.join(qnrDir, "websites/")))
        print("\n    This action CANNOT be undone!\n")
        while True:
            r = input(  "Enter Y to DELETE the file"
                        "{}(or Q to quit): ".format(len(filesToDelete)%2 and " " or "s locally and from the server "))
            if not r or r in "qQ": _say_quit()
            elif r in "yY": break
            
        # --------------------- Delete files
        
        print("")
        relSFP = os.path.relpath(filesToDelete[0], CD["siteDir"])
        with open(qnrDataPath, mode="r") as f: qdT = f.read()
        qdTL = qdT.splitlines()
        # If HTML file exists, check if uploaded, attempt deletion on server or quit
        if len(filesToDelete) > 1:
            relHFP = os.path.relpath(filesToDelete[1], CD["siteDir"])
            for i, x in enumerate(qdTL):
                if relHFP in x:
                    if x.rsplit("\t", maxsplit=1)[1] == "UP":
                        # Quit if unable to delete (no connection usually)
                        _manage_server_files([relHFP], "delete", qnrDataPath)
                    del qdTL[i]
                    break
        # Delete source file from data
        for i, x in enumerate(qdTL):
            if relSFP in x:
                del qdTL[i]
                break
        # Save modified data file
        qdT = "\n".join(qdTL)
        if qdT[-1] != "\n": qdT += "\n" # Because splitlines() != split()
        with open(qnrDataPath, mode="w") as f: f.write(qdT)
        # Delete files locally
        for x in filesToDelete: os.remove(x)
        if len(filesToDelete) > 1: # We assume html exists if in news list
            # Delete item from news listing
            newsListFP = os.path.join(CD["siteDir"], "page_sources/news.txt")
            newsHFP = os.path.relpath(filesToDelete[1], 
                            os.path.join(CD["siteDir"], "public_html/"))
            if os.path.exists(newsListFP):
                with open(newsListFP, mode="r") as f: nlT = f.read()
                if newsHFP in nlT:
                    nlTL = nlT.split("\n\n")
                    for i, x in enumerate(nlTL):
                        if newsHFP in x: # Found in title
                            del nlTL[i] # Delete title and blurb
                            del nlTL[i]
                            nlT = "\n\n".join(nlTL)
                            break
                    with open(newsListFP, mode="w") as f: f.write(nlT)
            # Delete item from news.js
            njsFP = os.path.join(CD["siteDir"], "public_html/res/js/news.js")
            with open(njsFP, mode="r") as f: njsT = f.read()
            hFN = os.path.basename(filesToDelete[1])
            njsT1, njsT2 = njsT.split("//==DO_NOT_EDIT_THIS_LINE")
            njsT1a, njsT1b = njsT1.split("var news_files_list = [")
            if hFN in njsT1b:
                njsT1b = njsT1b.replace(hFN, "")
                njsT1b = re.sub(', ""', "", njsT1b)
                njsT1b = re.sub('"", ', "", njsT1b)
                njsT =  njsT1a + \
                        "var news_files_list = [" + \
                        njsT1b + \
                        "//==DO_NOT_EDIT_THIS_LINE" + \
                        njsT2
                with open(njsFP, mode="w") as f: f.write(njsT)
        # Done
        print(  "\nNews post deletion completed.\n\n"
                "  Run Quicknr again, not in Tools mode, to update the news listing\n"
                "    HTML file and upload it together with 'news.js'.\n")
    
    def _tool_upgrade_config_file(qnrDataPath):
        """
        Copies settings from the website "config.txt" file to a copy
        of the Quicknr "config.txt" file, presumed to be the latest version,
        and saves the result as the website "config.txt" file
        
        Any settings that are new in the Quicknr file will now be active in
        the updated website file, at their default values
        
        If there are settings in the website file that are no longer used in
        the Quicknr file, those settings will be removed from the upgraded
        website file
        
        The result will be a website "config.txt" file that is in sync with the
        latest Quicknr version, but contains pre-existing user preferences
        
        The old website file will be kept as a backup
        
        """
        q_configPath = os.path.join(qnrDir, "config/config.txt")
        w_configPath = os.path.join(CD["siteDir"], "config/config.txt")
        with open(q_configPath, mode="r") as f: qT = f.read()
        with open(w_configPath, mode="r") as f: wT = f.read()
        # Regular settings
        # The following regex features the harmless bug of replacing the middle quote
        # in the first set of triple quotes used by snippets
        for mo in re.finditer(r"(?m)^([A-Z_]+):[ ]+['\"]?(.*?)['\"]?[ ]*$", wT):
            qT = re.sub(r"(?m)^("+mo.group(1)+r"):[ ]+(['\"]?).*?\2[ ]*$", 
                                    "\\1: \\g<2>"+mo.group(2).replace("\\","\\\\")+"\\2", qT)
        # Snippets
        for mo in re.finditer(r"(?ms)^([A-Z_]+):[ ]+['\"]{3}(.*?)['\"]{3}[ ]*$", wT):
            qT = re.sub(r"(?ms)^"+mo.group(1)+r":[ ]+(['\"]{3}).*?\1[ ]*$", 
                            mo.group(1)+': """'+mo.group(2).replace("\\","\\\\")+'"""', qT)
        # Backup website file
        shutil.copy2(w_configPath, os.path.join(CD["siteDir"], "config/config_old_backup.txt"))
        # Paranoid mode, check backup is fine
        with open(os.path.join(CD["siteDir"], "config/config_old_backup.txt"), mode="r") as f:
            fT = f.read()
            if fT != wT:
                _say_error( "Error: Config file upgrade aborted due to a problem with backup.\n"
                            "       Quit.")
        # Write upgraded website file
        with open(w_configPath, mode="w") as f: f.write(qT)
        print('\n  Website "config.txt" file has been upgraded, with your settings retained.\n')
    
    def _tools(qnrDataPath):
        """
        Tools mode, for various admin tasks
        
        """
        cmdL = [    "Delete a news post",
                    "Upgrade 'config.txt' file to latest version"   ]
        prompt = "Enter the number of the command to run (or Q to quit): "
        toolCmd = _ui_list_menu(cmdL, "Tools", prompt)
        if not toolCmd: _say_quit()
        if toolCmd == cmdL[0]:
            _tool_delete_news_post(qnrDataPath)
        elif toolCmd == cmdL[1]:
            _tool_upgrade_config_file(qnrDataPath)
        print("Quit.")
        sys.exit()
    
    # --------------------- In Quicknr() namespace
    # ================================================================
    
    # --------------------- Read commandline arguments
    cliArgs = None
    if len(sys.argv) > 1:
        cliArgs = _parse_cli_args()
    # --------------------- Prompt for website
    CD["siteFolder"] = _ui_get_site_dir() # May create website (& data file)
    CD["siteDir"] = os.path.join(qnrDir, "websites/" + CD["siteFolder"])
    qnrDataPath = os.path.join(CD["siteDir"], "quicknr_private/quicknr_data.txt")
    _check_file_folder_names() # Quit if invalid names
    with open(qnrDataPath, mode="r") as f: qnrDT = f.read()
    if cliArgs and cliArgs.convertall:
        # All sources to be converted again
        qnrDT = _mark_all_changed(qnrDT)
        # Mark news.txt to be rebuilt
        rebuildNewsList = True
    # --------------------- Get site configuration settings
    CD = _get_site_config(CD)
    # --------------------- Scan source files for new or changed
    sourcesDirs, htmlDirs = _get_pages_folders(CD["siteDir"])
    # sL - List of source files, relative to sources dir, no file extension
    # sLx - Full source paths with file extensions
    # sLxN - Full source paths that have no matching html counterpart
    # sLxC - Full source paths that have a counterpart and differ from record
    # hL - List of HTML files, relative to html dir, no file extension
    sL, sLx, sLxN, sLxC, hL = _get_pages_files(sourcesDirs,htmlDirs,qnrDT)
    
    print("\n---------------------- Website: " + CD["siteFolder"] + "\n")
    
    # --------------------- New website
    if not sL+hL:
        print(  "  This is your new website, with no content yet.\n"
                "  Create the content, then run Quicknr again.\n"
                "  Quit.")
        sys.exit()
    
    # --------------------- Tools mode
    if cliArgs and cliArgs.tools:
        _tools(qnrDataPath) # Will quit
    
    # --------------------- No new or changed sources to convert
    elif not sLxN and not sLxC:
        print("There are no new or updated source files to convert to HTML.")
    # --------------------- Convert sources to HTML
    elif sLxN:
        print("These source files are yet to be converted to HTML pages:\n\n")
        for x in sLxN: print("     "+os.path.relpath(x, sourcesDirs[0]))
    if sLxC:
        print("These source files have changed since conversion to HTML pages:\n\n")
        for x in sLxC: print("     "+os.path.relpath(x, sourcesDirs[0]))
    if sLxN or sLxC:
        while True:
            if sLxC:
                r = input(  "\nEnter Y to CONVERT these files, "
                            "OVERWRITING existing HTML files (or Q to quit): ")
            elif sLxN:
                r = input("\nEnter Y to CONVERT these files to HTML (or Q to quit): ")
            if not r or r in "qQ": _say_quit()
            elif r in "yY": break
        # New and changed together
        sLxNC = sLxN[:]
        sLxNC.extend(sLxC)
        # Check for news items to be converted, then set "news.txt" to update too
        for x in sLxNC:
            if os.path.split(os.path.dirname(x))[1] == "news":
                updateNewsList = True
                break
        convertedFiles = _convert_sources_to_html(sourcesDirs,htmlDirs,sLxNC,qnrDT)
        if convertedFiles: _record_new_files(convertedFiles, qnrDataPath, qnrDT)
        # Data file must be updated by this point, and it is
        # If news were updated, update res/js/news.js for dynamic prev/next links
        if updateNewsList:
            # Get list of news files from record, sorted by date
            newsFL = _get_news_file_list(qnrDataPath)
            # Write file list to res/js/news.js
            if newsFL:
                jsfP = os.path.join(CD["siteDir"], "public_html/res/js/news.js")
                jsfT = ""
                if os.path.exists(jsfP): # If no news.js, its function must be elsewhere
                    with open(jsfP, mode="r") as f:
                        jsfT = f.read()
                        jsfT = jsfT.split("//==DO_NOT_EDIT_THIS_LINE", maxsplit=1)[1]
                for i,x in enumerate(newsFL):
                    if not i: jsfT = '"'+x[1]+'"];\n\n//==DO_NOT_EDIT_THIS_LINE'+jsfT
                    else: jsfT = '"' + x[1] + '", ' + jsfT
                jsfT = '\nvar news_files_list = [' + jsfT
                jsfT = '\nvar news_list_items = ' + CD["NEWS_LIST_ITEMS"] + ';' + jsfT
                jsfT = '\nvar news_next_link_text = "' + CD["NEWS_NEXT_LINK"] + '";' + jsfT
                jsfT = '\nvar news_prev_link_text = "' + CD["NEWS_PREV_LINK"] + '";' + jsfT
                with open(jsfP, mode="w") as f: f.write(jsfT)
        print("\nDone.")
        
    # --------------------- Upload files to server
    # First, record news images if they are new (not yet in record) or changed in size
    newsImgDir = os.path.join(htmlDirs[0], "news/images")
    if os.path.exists(newsImgDir):
        iXL = [".jpg",".png",".gif",".svg"]
        ifL = [] # List of image files
        for x in os.listdir(newsImgDir):
            if os.path.splitext(os.path.join(newsImgDir, x))[1] in iXL:
                rIF = os.path.relpath(os.path.join(newsImgDir, x), CD["siteDir"])
                ifL.append(rIF)
        if ifL: _record_news_images(ifL, qnrDataPath)
    # Ready to upload
    filesToUpload = _get_records_to_upload(qnrDataPath) # Must run, deletes nonexistent
    if cliArgs: # Order matters
        if cliArgs.allupload: filesToUpload = _get_files_for_upload("all")
        elif cliArgs.resupload: filesToUpload.extend(_get_files_for_upload("res"))
        else:
            if cliArgs.stylesupload: filesToUpload.extend(_get_files_for_upload("css"))
            if cliArgs.jsupload: filesToUpload.extend(_get_files_for_upload("js"))
            if cliArgs.fontsupload: filesToUpload.extend(_get_files_for_upload("font"))
            if cliArgs.imgupload: filesToUpload.extend(_get_files_for_upload("img"))
    # Checking updateNewsList only wouldn't always work, must check files list
    if _check_files_for_news(filesToUpload):
        if not cliArgs:
            filesToUpload.append("public_html/res/js/news.js")
        elif not cliArgs.allupload and not cliArgs.resupload and not cliArgs.jsupload:
            filesToUpload.append("public_html/res/js/news.js")
    if filesToUpload:
        filesToUpload.sort()
        print(  "\n  These files will now be uploaded:\n\n    " + \
                "\n    ".join([x.split("\t", 1)[0] for x in filesToUpload]))
        while True:
            r = input("\nEnter Y to UPLOAD the files (or Q to quit): ")
            if not r or r in "qQ": _say_quit()
            elif r in "yY": break
        _manage_server_files(filesToUpload, "upload", qnrDataPath)
        if cliArgs and cliArgs.allupload: # Not handled in _manage_server_files()
            with open(qnrDataPath, mode="r") as f: fT = f.read()
            fT = re.sub(r"\tNOTUP", r"\tUP", fT)
            with open(qnrDataPath, mode="w") as f: f.write(fT)
    else:
        print("There are no files marked for upload to server.")
    
    # --------------------- Exit or continue in the loop
    while True:
        r = input("\nEnter Y to continue working with Quicknr (or Q to quit): ")
        if not r or r in "qQ": _say_quit()
        elif r in "yY": break
    return 0

if __name__ == "__main__":
    while True:
        Quicknr()

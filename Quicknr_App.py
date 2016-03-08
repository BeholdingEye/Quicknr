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
#                            Version 1.2.2                             #
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
from contextlib import suppress
try: import markdown
except ImportError: markdownModule = False
else: markdownModule = True


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
    
    print("\n===================== QUICKNR 1.2.2 =====================\n")
    
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
                    NEWS_LIST_LINK_POSITION = "END",
                    NEWS_LIST_LINK_PREFIX = "",
                    NEWS_DATE_FORMAT = "%A, %d %B %Y",
                    NEWS_PREV_LINK = "&lt; Older",
                    NEWS_NEXT_LINK = "Newer &gt;",
                    INDENT_HTML_TREE = "YES",
                    DEBUG_ERRORS = "NO",
                    FTP_SERVER = "",
                    FTP_PATH = "",
                    FTP_USERNAME = "",
                    FTP_PASSWORD = "",
                    FTP_ACCT = "",
                    FTP_DEBUG = "0",
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
    
    # Boolean toggle for 'page_sources/news.txt' updating conversion
    updateNewsList = False
    
    # Javascript that Quicknr will place in "public_html/res/js/news.js" file
    newsLinksJavascript = """

//==DO_NOT_EDIT_THIS_LINE
// Quicknr requires the above line for placing of news files list

// ======================= NEWS PREV NEXT LINKS =====================

function CreateNewsPrevNextLinks() {
    // Check if we're in news folder
    wHref = window.location.href;
    wDirPath = wHref.substr(0,wHref.lastIndexOf("/"));
    wDir = wDirPath.substr(wDirPath.lastIndexOf("/")+1);
    if ((wDir == "news") && (news_files_list.length > 1)) {
        prevLink = "";
        nextLink = "";
        for (var i = 0; i < news_files_list.length; i++) {
            if (window.location.href.split("/").pop() == news_files_list[i]) {
                // The newest file is first in the list, the oldest last
                if (i == 0) {
                    prevLink = news_files_list[i+1];
                    nextLink = "";
                }
                else if (i == news_files_list.length - 1) {
                    prevLink = "";
                    nextLink = news_files_list[i-1];
                }
                else {
                    prevLink = news_files_list[i+1];
                    nextLink = news_files_list[i-1];
                }
                break;
            }
        }
        linksDiv = document.getElementsByClassName("news_links")[0];
        linksDivText = linksDiv.innerHTML;
        if (prevLink != "") {
            prevLink = '\n<span class="prev_link"><a href="'+prevLink+'">'+news_prev_link_text+'</a></span>';
            linksDivText = prevLink + linksDivText;
        }
        if (nextLink != "") {
            nextLink = '<span class="next_link"><a href="'+nextLink+'">'+news_next_link_text+'</a></span>\n';
            linksDivText = linksDivText + nextLink;
        }
        linksDiv.innerHTML = linksDivText;
    }
}

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
            while True:
                r1 = input( "\nEnter the website FOLDER name, using alphanumerical characters and\n"
                            "the underscore (A-Za-z0-9_) only and no spaces (or Q to quit).\n"
                            "Choose the name well, website folder names cannot be changed later: ")
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
            # --------------------- Create news.js file
            with open(os.path.join(qnrDir, 
                                    "websites/" + r1 + "/public_html/res/js/news.js"), 
                                    mode="w") as f:
                f.write(newsLinksJavascript)
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
              /public_html/res/js  - Javascript files, including news.js
                                     continually updated by Quicknr for 
                                     dynamic Prev/Next news links
              
              /quicknr_private/       - Location of the 'quicknr_data.txt'
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
    
    def _validate_CD(CD):
        """
        Validates CD values
        
        """
        def _ve(s):
            """ Error call on the error """
            _say_error("Error: Invalid value in config: %s\n       Quit." % s)
            
            return 0
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
        if CD["NEWS_LIST_LINK_POSITION"].strip() not in ["START", "END"]:
            _ve("NEWS_LIST_LINK_POSITION")
        # News list link prefix can be empty, no validation
        if not CD["NEWS_DATE_FORMAT"].strip(): _ve("NEWS_DATE_FORMAT")
        if not CD["NEWS_PREV_LINK"].strip(): _ve("NEWS_PREV_LINK")
        if not CD["NEWS_NEXT_LINK"].strip(): _ve("NEWS_NEXT_LINK")
        if CD["INDENT_HTML_TREE"] not in ["YES","NO"]: _ve("INDENT_HTML_TREE")
        if CD["DEBUG_ERRORS"] not in ["YES","NO"]: _ve("DEBUG_ERRORS")
        # Leave out server values
        if CD["FTP_DEBUG"] not in ["0","1","2"]: _ve("FTP_DEBUG")
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
            CD["HTML_TITLE_SEPARATOR"] = html.escape(CD["HTML_TITLE_SEPARATOR"])
        if re.search(r"(?m)^HTML_WEBSITE_NAME:",cT):
            CD["HTML_WEBSITE_NAME"] = re.search(r"(?m)^HTML_WEBSITE_NAME:"+rP,cT).group(1)
            CD["HTML_WEBSITE_NAME"] = html.escape(CD["HTML_WEBSITE_NAME"])
        if re.search(r"(?m)^HTML_PAGE_TITLE:",cT):
            CD["HTML_PAGE_TITLE"] = re.search(r"(?m)^HTML_PAGE_TITLE:"+rP,cT).group(1)
            CD["HTML_PAGE_TITLE"] = html.escape(CD["HTML_PAGE_TITLE"])
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
        if re.search(r"(?m)^NEWS_LIST_LINK_POSITION:",cT):
            CD["NEWS_LIST_LINK_POSITION"] = re.search(r"(?m)^NEWS_LIST_LINK_POSITION:"+rP,cT).group(1)
        if re.search(r"(?m)^NEWS_LIST_LINK_PREFIX:",cT):
            CD["NEWS_LIST_LINK_PREFIX"] = re.search(r"(?m)^NEWS_LIST_LINK_PREFIX:"+rP,cT).group(1)
        if re.search(r"(?m)^NEWS_DATE_FORMAT:",cT):
            CD["NEWS_DATE_FORMAT"] = re.search(r"(?m)^NEWS_DATE_FORMAT:"+rP,cT).group(1)
        if re.search(r"(?m)^NEWS_PREV_LINK:",cT):
            CD["NEWS_PREV_LINK"] = re.search(r"(?m)^NEWS_PREV_LINK:"+rP,cT).group(1)
        if re.search(r"(?m)^NEWS_NEXT_LINK:",cT):
            CD["NEWS_NEXT_LINK"] = re.search(r"(?m)^NEWS_NEXT_LINK:"+rP,cT).group(1)
        if re.search(r"(?m)^INDENT_HTML_TREE:",cT):
            CD["INDENT_HTML_TREE"] = re.search(r"(?m)^INDENT_HTML_TREE:"+rP,cT).group(1)
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
        os.chdir(prevCWD)
        _validate_CD(CD)
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
    
    # --------------------- HTML FILE BUILDING FUNCTIONS ---------------------
    
    def _enter_html_title():
        """
        Enters the HTML title from the settings dict in to the empty 
        <title></title> tag of HTML_HEAD snippet in the dict
        
        """
        nonlocal CD
        if "<title>" in CD["HTML_HEAD"]:
            # Clear any pre-existing title
            CD["HTML_HEAD"] = re.sub(r"(<title>).+?(</title>)", r"\1\2", CD["HTML_HEAD"])
            if CD["HTML_TITLE"] == "WEBSITE-PAGE":
                if CD["HTML_PAGE_TITLE"]:
                    htmlTitle = CD["HTML_WEBSITE_NAME"] + CD["HTML_TITLE_SEPARATOR"] + \
                                CD["HTML_PAGE_TITLE"]
                else: htmlTitle = CD["HTML_WEBSITE_NAME"]
            elif CD["HTML_TITLE"] == "WEBSITE": htmlTitle = CD["HTML_WEBSITE_NAME"]
            elif CD["HTML_TITLE"] == "PAGE": htmlTitle = CD["HTML_PAGE_TITLE"]
            CD["HTML_HEAD"] = CD["HTML_HEAD"].replace( "<title></title>", 
                                                "<title>{}</title>".format(htmlTitle))

    def _process_inline_markup(rT):
        """
        Converts inline markup to HTML and returns the text
        
        """
        # --------------------- Links
        if re.search(r"\[.+?\]", rT):
            rT = re.sub(r"\[(.+?)[ ]+(\S+?)\]", r'<a href="\2">\1</a>', rT)
            rT = re.sub(r"\[(\S+?)\]", r'<a href="\1">\1</a>', rT)
            
        # --------------------- Bold, italic and monospace in linked text
        # We use <span> for a sense of CSS 'neutrality', and easier processing with regex
        rT = re.sub(r"(>)(?:\*|_|`){3}([^<]+?)(?:\*|_|`){3}(</a>)", 
            r'\1<span style="font-weight:bold;font-style:italic"><code>\2</code></span>\3', rT)
        # Order matters here, catch double ** and __ as bold & italic, `` as italic
        rT = re.sub(r"(>)(?:\*|_){2}([^<]+?)(?:\*|_){2}(</a>)", 
            r'\1<span style="font-weight:bold;font-style:italic">\2</span>\3', rT)
        rT = re.sub(r"(>)(?:_|`){2}([^<]+?)(?:_|`){2}(</a>)", 
            r'\1<span style="font-style:italic"><code>\2</code></span>\3', rT)
        rT = re.sub(r"(>)(?:\*|`){2}([^<]+?)(?:\*|`){2}(</a>)", 
            r'\1<span style="font-weight:bold"><code>\2</code></span>\3', rT)
        rT = re.sub(r"(>)\*([^<]+?)\*(</a>)", r'\1<span style="font-weight:bold">\2</span>\3', rT)
        rT = re.sub(r"(>)_([^<]+?)_(</a>)", r'\1<span style="font-style:italic">\2</span>\3', rT)
        rT = re.sub(r"(>)`([^<]+?)`(</a>)", r"\1<code>\2</code>\3", rT)
        # Correct for styling - href/src/alt, styling not valid here
        # Three times, to catch all
        rT = re.sub(r"((?:href|src)=\")(\*|_|`)([^\"]+)\2(\")", r"\1\3\4", rT)
        rT = re.sub(r"((?:href|src)=\")(\*|_|`)([^\"]+)\2(\")", r"\1\3\4", rT)
        rT = re.sub(r"((?:href|src)=\")(\*|_|`)([^\"]+)\2(\")", r"\1\3\4", rT)
        rT = re.sub(r"((?:alt)=\")(\*|_|`)([^\"]+)\2", r"\1\3", rT)
        rT = re.sub(r"((?:alt)=\")(\*|_|`)([^\"]+)\2", r"\1\3", rT)
        rT = re.sub(r"((?:alt)=\")(\*|_|`)([^\"]+)\2", r"\1\3", rT)
        
        # Correct http/www.
        rT = re.sub(r"(href|src)=\"www\.", r'\1="http://www.', rT)
        
        # --------------------- Styling outside links
        rT = re.sub(r"(?<=\s)(?:\*|_|`){3}([^ ][^*`]*?)(?:\*|_|`){3}(?!\w)", 
            r'<span style="font-weight:bold;font-style:italic"><code>\1</code></span>', rT)
        # Order matters again
        rT = re.sub(r"(?<=\s)(?:_|\*){2}([^ ][^*]*?)(?:_|\*){2}(?!\w)", 
            r'<span style="font-weight:bold;font-style:italic">\1</span>', rT)
        rT = re.sub(r"(?<=\s)(?:_|`){2}([^ ][^`]*?)(?:_|`){2}(?!\w)", 
            r'<span style="font-style:italic"><code>\1</code></span>', rT)
        rT = re.sub(r"(?<=\s)(?:\*|`){2}([^ ][^*`]*?)(?:\*|`){2}(?!\w)", 
            r'<span style="font-weight:bold"><code>\1</code></span>', rT)
        rT = re.sub(r"(?<=\s)\*([^ ][^*]*)\*(?!\w)", r'<span style="font-weight:bold">\1</span>', rT)
        rT = re.sub(r"(?<=\s)_([^ ].*?)_(?!\w)", r'<span style="font-style:italic">\1</span>', rT)
        rT = re.sub(r"(?<=\s)`([^ ][^`]*)`(?!\w)", r"<code>\1</code>", rT)
        return rT
        

    def _plaintext_to_html(text, fX, relfPath):
        """
        Converts QLM (or Markdown if configured) plain text to HTML and returns it
        
        """
        nonlocal CD
        nonlocal preContentL
        
        if markdownModule and (fX == ".mdml" or CD["QLM_OR_MARKDOWN"] == "MARKDOWN"):
            # A compromise attempt at titling a Markdown page: first para up to 80 chars
            if CD["MARKDOWN_TITLING"] == "YES":
                mo = re.match(r"\S[^\n]{0,80}", text) # !No starting whitespace
                if mo: CD["HTML_PAGE_TITLE"] = html.escape(mo.group().strip())
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
            Return link type of text: link, image, YTvideo, unknown
            
            """
            if "youtube" in sT.lower() or "youtu.be" in sT.lower(): return "YTvideo"
            for x in [".jpg",".png",".gif",".svg"]:
                if sT.lower().endswith(x) or sT.split("Quicknr?=IL=?Quicknr")[0].lower().endswith(x):
                    return "image"
            return "link"
        
        # --------------------- Text cleaning
        # Convert tabs to 4 spaces
        nT = text.replace("\t", "    ")
        # Add line breaks at start/end (for sections)
        nT = "\n\n"+nT+"\n\n"
        # Convert any <> around URLs to [] ??
        #nT = re.sub(r"<[ ]*((?:\S+?\.)+\S+?)[ ]*>", r"[\1]", nT)
        # Escape HTML characters
        nT = html.escape(nT, quote=False)
        # Protect code blocks, into their list
        for x in nT.strip().split("\n\n"):
            if re.match(r"(?i)code(?:-\w+)?:\s[ ]*\S",x):
                x = re.sub(r"\A\S[^:\n]*:\s?", "", x)
                preContentL.append(x)
        if preContentL:
            nT = re.sub(r"(?mi)(^code(?:-\w+)?:\s)(.+\n)+(?=\n)", r"\1Quicknr?=preText=?Quicknr\n", nT)
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
            CD["HTML_PAGE_TITLE"] = html.escape(title)
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
                blocks[i][0] = '<h1 class="title">\n%s\n</h1>' % b[0]
            if b[1] == "heading":
                sCount += 1
                hhh = '<h2 class="heading {} heading_{}">\n{}\n</h2>'
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
                fRand = int(random.choice("10")) # Random control for left/right floating
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
                        # Handle different link block types
                        if linkType == "link":
                            pCount += 1
                            pT = '<p class="p_{} link_p {} section_{}">\n<a href="{}">{}</a>\n</p>'
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
                                pT = '<div class="imgblock link_img imgblock_{} {} section_{}">\n<a href="{}">\n'
                            pT += '<img src="{}" alt="{}" />\n'
                            if clickLinkURL:
                                pT = pT.format(iCount,iCount%2 and "odd" or "even",
                                                sCount,clickLinkURL,linkURL,linkText)
                            else:
                                pT = pT.format(iCount,iCount%2 and "odd" or "even",
                                                sCount,linkURL,linkText)
                            if clickLinkURL: pT += '</a>\n'
                            if linkText: pT += '<p class="imgcaption">\n{}\n</p>\n'.format(linkText)
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
                            npT = '<li class="li_{} {}">\n{}\n</li>\n'
                            npT1 += npT.format(liCount, liCount%2 and "odd" or "even", x)
                        pT = '<ul class="list_{} {} section_{}">\n{}</ul>'
                        pT = pT.format(lCount, lCount%2 and "odd" or "even", sCount, npT1)
                    elif len(re.findall(r"(?m)^\d+\.?[ ]", pT)) > 1: # Ordered list
                        lCount += 1
                        liCount = 0
                        npT1 = ""
                        for x in re.findall(r"(?m)^\d+\.?[ ]+(.+)$", pT):
                            liCount += 1
                            npT = '<li class="li_{} {}">\n{}\n</li>\n'
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
                        npT += '<dt>\n{}\n</dt>\n<dd>\n{}\n</dd>\n</dl>'
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
                        else:
                            linkText = ""
                        clickLinkURL = "" # Handle images as links
                        if "Quicknr?=IL=?Quicknr" in linkURL:
                            linkURL, clickLinkURL = linkURL.split("Quicknr?=IL=?Quicknr", maxsplit=1)
                            if "Quicknr?=IL=?Quicknr" in clickLinkURL:
                                _say_error( "Error: File '"+relfPath+"' contains one or more\n"
                                            "       image link sequences of more than two [] parts.\n"
                                            "       Correct and try again.\n"
                                            "       Quit.")
                        fCount += 1;
                        # Random control of which side floating zig-zag starts in section
                        if fRand:
                            oe1 = "even"
                            oe2 = "odd"
                        else:
                            oe1 = "odd"
                            oe2 = "even"
                        ipT = '<div class="imgfloat imgfloat_{} {} section_{}">\n'
                        if clickLinkURL:
                            ipT = '<div class="imgfloat link_img imgfloat_{} {} section_{}">\n<a href="{}">\n'
                        ipT += '<img src="{}" alt="{}" />\n'
                        if clickLinkURL:
                            ipT = ipT.format(fCount,fCount%2 and oe1 or oe2,sCount,
                                                        clickLinkURL,linkURL,linkText)
                        else:
                            ipT = ipT.format(fCount,fCount%2 and oe1 or oe2,sCount,
                                                        linkURL,linkText)
                        if clickLinkURL: ipT += '</a>\n'
                        if linkText: ipT += '<p class="imgcaption">\n{}\n</p>\n'.format(linkText)
                        ipT += '</div>'
                        # Text part of paragraph
                        pCount += 1
                        pT = '<p class="p_{} img_p {} section_{}">\n{}\n</p>'
                        pT = pT.format(pCount, pCount%2 and "odd" or "even", sCount, ppT)
                        # Image and text combo
                        pT = ipT + "\n" + pT
                    
                    # --------------------- Paragraph
                    else:
                        pCount += 1
                        npT = '<p class="p_{} {} section_{}">\n{}\n</p>'
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
        
        # --------------------- Process inline markup
        rT = _process_inline_markup(rT)
        
        # Final wrap (penultimate actually; by default, head snippet adds <div class="page">)
        # Place file name in class for main div
        docN = os.path.splitext(os.path.basename(CD["sourceFilePath"]))[0]
        # If news post, insert link to news listing, named per pref
        hCode = ""
        if os.path.split(os.path.dirname(CD["sourceFilePath"]))[1] == "news":
            hCode = '<div class="news_links">\n<span class="listing_link">'
            hCode += '<a href="../news.html">{}{}</a></span>\n</div>\n'
            hCode = hCode.format(html.escape(CD["NEWS_LIST_LINK_PREFIX"],quote=False),CD["NEWS_LIST_TITLE"])
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
            else: dTime = dt.date.today().strftime(CD["NEWS_DATE_FORMAT"])
            rT = re.sub(r"(<div class=\"user_content[^>\"]*?\">)", 
                            r'\1\n<p class="news_date_stamp">\n{}\n</p>'.format(dTime), text)
            return rT
        else: return text
    
    def _convert_sources_to_html(sourcesDirs, htmlDirs, sLxNC, wdataT):
        """
        Converts source ".txt"/".mdml" files that are either new or the user
        has changed, to HTML. Also concatenates any HTML source files with
        configuration snippets into output HTML files without conversion
        
        """
        nonlocal CD
        nonlocal preContentL
        
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
        nNL.sort() # Might be worth it if named well
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
            docType = "" # Clear docType declaration
            print("\n  Converting to HTML (file {} of {}):".format(i+1, len(sLxNC)))
            print("       " + relfxNC)
            with open(fxNC, mode="r") as f:
                hT = f.read()
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
                # File types other than ".txt"/".mdml" will need custom titling solutions
                _enter_html_title()
                # Change source ".txt"/".mdml" extension to HTML config preference
                hF = os.path.splitext(hF)[0] + CD["PAGE_FILE_EXTENSION"]
            # Store doctype, we may need it later
            if re.match(r"\s*<!DOCTYPE[^>]+>", CD["HTML_HEAD"]):
                docType = re.match(r"\s*<!DOCTYPE[^>]+>\n", CD["HTML_HEAD"]).group()
            # Combine with snippets
            hT = CD["HTML_HEAD"] + hT + CD["HTML_TAIL"]
            # Update CD with html file path
            CD["htmlFilePath"] = hF
            # Date stamp for news, using original date from record if editing old news
            hT = _news_date_stamp(hT, wdataT)
            # Get imports
            hT = _import_files(hT)
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
            # Prepend links with "../" if file in news subfolder
            if os.path.split(os.path.dirname(fxNC))[1] == "news":
                hT = re.sub(r"((?:href|src)=\")(?!(?:\.\./|http:|https:|file:|ftp:|javascript:|mailto:))", 
                                                                    r"\1../",hT)
                hT = re.sub(r"((?:href|src)=\")\.\./(#)", r"\1\2", hT) # Correction (for bug?)
            # Enter IDs in DIV, P, H1-6, IMG, IFRAME, DL, DT, DD, OL, UL, and LI
            if CD["HTML_TAG_ID"] == "YES":
                idCount = 0
                def _id_generator(mo):
                    """Enters numerical series of IDs into tags"""
                    nonlocal idCount
                    idCount += 1
                    return r'{} id="id{}"{}'.format(mo.group(1),idCount,mo.group(2))
                hT = re.sub(r"(<(?:div|p|h\d|img|iframe|dl|dt|dd|ol|ul|li)(?:[ ][^>]*?)*?)(/?>)", 
                                                                    _id_generator, hT)
            
            # Indent HTML tree structure (if from ".txt" source)
            if fX == ".txt" and CD["INDENT_HTML_TREE"] == "YES":
                try:
                    hT = re.sub(r">\n+",">",hT)
                    hT = re.sub(r"\n+<","<",hT)
                    with xml.parseString(hT) as dom:
                        hT = dom.documentElement.toprettyxml(indent="  ", newl="\n")
                    # toprettyxml may have lost us the Doctype
                    if re.match(r"\s*<html", hT) and docType:
                        hT = docType + hT
                    # Put back spaces at /> tag ends
                    hT = re.sub(r"(?<![ ])(/>)", r" \1", hT)
                    # Remove whitespace between closing tag and punctuation
                    hT = re.sub(r"(</[^>]+>)\s+(?=[,.?!'\"\)])", r"\1", hT)
                    # Remove whitespace at start of <p> block 
                    # for Chrome's handling of white-space CSS
                    hT = re.sub(r"(<p [^>]+>)\s+", r"\1", hT)
                except: # Fail silently
                    pass
            # Bring in <pre> code text (protected earlier)
            if preContentL:
                for x in preContentL:
                    #x = html.escape(x, quote=False) # Done already
                    hT = hT.replace(">Quicknr?=preText=?Quicknr</pre>", ">" + x + "</pre>", 1)
            # Last correction, for overzealous char entity conversion of &
            hT = re.sub(r"&amp;([A-Za-z0-9#]{2,6};)", r"&\1", hT)
            with open(hF, mode="w") as f:
                f.write(hT)
            relhF = os.path.relpath(hF, CD["siteDir"])
            # Return both source and html relative paths
            convertedFiles.append(relhF)
            convertedFiles.append(relfxNC)
            print("  Converted file:\n       " + relhF)
            
            # --------------------- If this was a news post, list in "news.txt"
            if os.path.split(os.path.dirname(fxNC))[1] == "news":
                # Get title, first paragraph, and file path relative to html dir
                nhTitle = html.unescape(CD["HTML_PAGE_TITLE"])
                # ...but the unescape doesn't catch everything, so we correct
                nhTitle = re.sub(r"&amp;([A-Za-z0-9#]{2,6};)", r"&\1", nhTitle)
                nhFP = ""
                with open(fxNC, mode="r") as f: fT = f.read()
                mo = re.search(r"(?m)^\S.+$(?=\n\n)", fT)
                if mo: nhFP = mo.group()
                # Get rid of any links in first paragraph
                if "[" in nhFP and "]" in nhFP:
                    nhFP = re.sub(r"\[+[ ]*([^ \]]+)[ ]*\]+", "\1", nhFP)
                    nhFP = re.sub(r"\[+[ ]*([^\]]+?)[ ]+[^ \]]+[ ]*\]+", r"\1", nhFP)
                if len(nhFP) < 20: nhFP = "" # Most likely not literal text
                elif len(nhFP) > int(CD["NEWS_BLURB_LENGTH"]): # Nicely shorten by word
                    nhFP = nhFP[:int(CD["NEWS_BLURB_LENGTH"])].rsplit(maxsplit=1)[0]+"..."
                if nhFP: nhFP += " "
                nhPath = os.path.relpath(CD["htmlFilePath"], htmlDirs[0])
                # Date: get record or today's
                dD = _get_file_record_date(fxNC, wdataT)
                if not dD:
                    dD = dt.date.today()
                # Construct news listing item; linked heading and a para: title and intro
                nhNItem = "   _"+dD.strftime("%Y-%b-%d")+"_ ["+nhTitle+" "+nhPath+"]\n\n"+\
                                    nhFP+"["+CD["NEWS_MORE_PHRASE"]+" "+nhPath+"]"
                # --------------------- News listing source file
                nlT = ""
                if os.path.exists(os.path.join(sourcesDirs[0], "news.txt")):
                    with open(os.path.join(sourcesDirs[0], "news.txt"), mode="r") as f:
                        nlT = f.read()
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
                if len(nlT.split("\n\n")[1:]) > 2*int(CD["NEWS_LIST_ITEMS"]):
                    nlT = "\n\n".join(nlT.split("\n\n")[:-2])
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
                    if dD: d = dD.strftime("%Y-%m-%d_%H-%M-%S")
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
    
    def _upload_files(recordsToUpload, qnrDataPath):
        """
        Uploads files to server and updates data file
        
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
                # Will throw error if path not exist, cannot create dir
                fc.cwd(CD["FTP_PATH"])
                print("\n"+fc.pwd())
                fc.dir(); print("")
                for x in recordsToUpload:
                    if x in fT: fP = x.split("\t", 1)[0]
                    else: fP = x[:] # Copy
                    fN = os.path.basename(fP); fD = os.path.dirname(fP)
                    # --------------------- Get sub-folders
                    subDs = []; splitfD = [fD]
                    if os.path.split(fD)[0]: # Head and tail
                        while True:
                            splitfD = os.path.split(splitfD[0])
                            if splitfD[0]: subDs.append(splitfD[1])
                            else: break
                        subDs.reverse()
                        for a in subDs:
                            try: fc.cwd(a)
                            except:
                                fc.mkd(a)
                                fc.cwd(a)
                    # --------------------- Upload
                    print("\n"+fc.pwd())
                    with open(os.path.join(CD["siteDir"], fP), mode="rb") as uf:
                        print("  Uploading file '{}' ...".format(fP), end="")
                        fc.storbinary("STOR "+fN, uf)
                        print(" Done.")
                    if subDs: fc.cwd("../"*len(subDs))
                    # --------------------- Update data file
                    if x in fT and "\t" in x: # Separate out argparse files
                        parts = fT.partition(x) # x is whole line from record
                        fT = parts[0]+parts[1].rsplit("\t", 1)[0]+"\tUP"+parts[2]
        except Exception as e:
            print(e) # No need for full trace, just print the error
        else:
            with open(qnrDataPath, mode="w") as f: f.write(fT)
            print("\nUploading completed.")
    
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
                    wL[i] = xL[0] + "\t" + xL[1] + "\t" + "0" + "\t" + "\t".join(xL[3:])
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
    
    def _check_file_extensions_spaces():
        """
        Checks that all files in the website folder have file extensions
        and no spaces in their names
        
        Conversely, checks that folders have no spaces and no extensions
        
        """
        fpL = []; spL = []; dxL = []; dsL = []
        for dp, dn, fns in os.walk(CD["siteDir"]):
            for d in dn:
                if " " in d:
                    dsL.append(os.path.relpath(os.path.join(dp, d), CD["siteDir"]))
                if os.path.splitext(d)[1]:
                    dxL.append(os.path.relpath(os.path.join(dp, d), CD["siteDir"]))
            for fn in fns:
                if " " in fn:
                    spL.append(os.path.relpath(os.path.join(dp, fn), CD["siteDir"]))
                if not os.path.splitext(fn)[1]:
                    fpL.append(os.path.relpath(os.path.join(dp, fn), CD["siteDir"]))
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
    
    # --------------------- In Quicknr() namespace
    # ================================================================
    
    # --------------------- Read commandline arguments, action them
    cliArgs = None
    if len(sys.argv) > 1:
        cliArgs = _parse_cli_args()
    # --------------------- Prompt for website
    CD["siteFolder"] = _ui_get_site_dir() # May create website (& data file)
    CD["siteDir"] = os.path.join(qnrDir, "websites/" + CD["siteFolder"])
    qnrDataPath = os.path.join(CD["siteDir"], "quicknr_private/quicknr_data.txt")
    _check_file_extensions_spaces() # Quit if no extensions, or have spaces in names
    with open(qnrDataPath, mode="r") as f: qnrDT = f.read()
    if cliArgs and cliArgs.convertall:
        # All sources to be converted again
        qnrDT = _mark_all_changed(qnrDT)
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
    if updateNewsList:
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
        _upload_files(filesToUpload, qnrDataPath)
        if cliArgs and cliArgs.allupload: # Not handled in _upload_files()
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

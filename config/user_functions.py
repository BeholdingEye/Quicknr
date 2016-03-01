########################################################################
#                                                                      #
#                       QUICKNR USER FUNCTIONS                         #
#                                                                      #
#  Define the functions that will be called from HTML snippets with    #
#  '@python: "function-name"' directives to work on completed HTML     #
#  output of a converted source just before it is written to file.     #
#                                                                      #
#  The function must accept exactly three positional parameters:       #
#                                                                      #
#  1) Text of the full HTML output just before writing to file         #
#                                                                      #
#  2) Starting index position of the function directive in the text    #
#                                                                      #
#  3) Configuration dictionary holding website settings. Keys of the   #
#     dictionary have the same names as options in the "config.txt"    #
#     file. Some additional keys are also present: "siteDir" for       #
#     website folder path, "siteFolder" for its folder name, and the   #
#     self-explanatory "sourceFilePath" and "htmlFilePath" of the      #
#     file being worked on. The dictionary is read-only.               #
#                                                                      #
#  The function directive is removed from the text before the call is  #
#  made. After it has done its work, the function must return the      #
#  processed text.                                                     #
#                                                                      #
#  This file as a whole will be read and executed by Quicknr before    #
#  the relevant function is called. It is therefore safest to not      #
#  include any code outside function (or class) definitions.           #
#                                                                      #
########################################################################


def page_style_link(text, i, CD):
    """
    Imports stylesheet link(s) to matching .css file(s) for some pages - adapt to 
    your own needs
    
    """
    import os
    # Values are lists, so that more than one stylesheet can import into a file
    pairsD = {
                    "index.txt"     :   ["index.css"],
                    "about.txt"     :   ["about.css"],
                    "news.txt"      :   ["newslist.css"],
                    "newspost"      :   ["newspost.css"]  } # Will catch any name
    pageMatch = os.path.basename(CD["sourceFilePath"])
    link = '<link rel="stylesheet" href="res/css/{}" type="text/css" />\n'
    # Alter the link for news posts
    if os.path.split(os.path.dirname(CD["sourceFilePath"]))[1] == "news":
        link = '<link rel="stylesheet" href="../res/css/{}" type="text/css" />\n'
        pageMatch = "newspost"
    try:
        nlink = ""
        for x in pairsD[pageMatch]:
            nlink += link.format(x)
    except KeyError: return text
    return text[:i] + nlink + text[i:]


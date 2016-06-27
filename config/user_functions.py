########################################################################
#                                                                      #
#                       QUICKNR USER FUNCTIONS                         #
#                                                                      #
#  Define the functions that will be called from HTML snippets with    #
#  '@python: "function-name"' directives to work on completed HTML     #
#  output of a converted source before it is written to file.          #
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
#  Note that after user functions are executed, Quicknr still          #
#  performs some tidying up before writing to HTML file:               #
#    * whitespace in and around tags is corrected                      #
#    * id attributes are entered in tags (if set so in preferences)    #
#    * HTML tree is indented                                           #
#    * contents of <pre> tags are entered back into the document       #
#      after they had been protected from processing                   #
#    * overzealous character entity conversions are corrected          #
#    * in news post pages, a commented-out news list item block is     #
#      placed at the beginning of the "user_content" DIV (for AJAX     #
#      retrieval when loading more items on the news listing page)     #
#    * XHML style " />" tag endings are converted to HTML ">" syntax   #
#      if the DOCTYPE is HTML 5                                        #
#                                                                      #
#  Because Quicknr works with XHTML and HTML, custom functions should  #
#  assume the tags they search for could be in either format. When     #
#  inserting tags, XHTML syntax is best. XHTML is the syntax used by   #
#  Quicknr internally, and converted to HTML if need be just before    #
#  writing to file.                                                    #
#                                                                      #
########################################################################


def page_style_link(text, i, CD):
    """
    Imports stylesheet link(s) to matching .css file(s) for some pages - adapt to 
    your own needs
    
    The two stylesheets used by default should be kept as they are relied upon
    for news list & post styling
    
    """
    import os
    # Values are lists, so that more than one stylesheet can import into a file
    pairsD = {
                    "news.txt"      :   ["quicknr_base_newslist.css"],
                    "newspost"      :   ["quicknr_base_newspost.css"]  } # Will catch any name
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


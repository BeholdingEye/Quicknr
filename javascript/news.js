
//==DO_NOT_EDIT_THIS_LINE
// Quicknr requires the above line for placing of news files list

// ======================= INSERT NEWS ITEMS =====================

// ----------------------- Globals

var newsListLoadCount           = news_list_items; // Counter of loaded news items
var newsLoaderBtnContainerClass = "user_content"; // Matching the class Quicknr creates
var newsLoaderBtnBlockID        = "NewsLoaderBlock"; // Shouldn't need to be edited, but if it is...
var newsLoaderBtnID             = "LoadMoreNewsBtn"; //   ...remember to mirror the change in CSS
var newsLoaderBtnText           = "Load More"; // Button name in the UI

// ----------------------- Functions

function NewsItemURL(newsItemName) {
    return "news/" + newsItemName;
}

function GetNewsItemText(doc) {
    // Load text from document
    xhr=new XMLHttpRequest();
    xhr.open("GET",doc,false); // False sets it not async
    xhr.send();
    var text=xhr.responseText;
    // Extract DIV from text; [\s\S] is any char including \n
    var re = /<!-- Quicknr-news-list-item-block\s+([\s\S]+?)\s+-->/
    var match = re.exec(text);
    if (match) {
        return match[1];
    }
    return "";
}

function InsertNewsContentHTML(itemHTML) {
    var obj = objClass(newsLoaderBtnContainerClass);
    obj.innerHTML += itemHTML;
}

function InsertNewsItems() {
    var btn = null;
    var obj = objClass(newsLoaderBtnContainerClass);
    if (objID(newsLoaderBtnBlockID)) {
        btn = objID(newsLoaderBtnBlockID);
        //btn = obj.removeChild();
        btn = btn.parentNode.removeChild(btn);
    }
    var nextTarget = newsListLoadCount + news_list_items;
    var realLimit = news_files_list.length;
    var endNum = Math.min(realLimit, nextTarget);
    // Increase number of items to show if close to exhausting the list
    if ((realLimit - endNum) <= (news_list_items/2)) endNum = realLimit;
    if (endNum > newsListLoadCount) {
        for (var i = newsListLoadCount; i < endNum; i++) {
            InsertNewsContentHTML(GetNewsItemText(NewsItemURL(news_files_list[i])));
        }
        newsListLoadCount = endNum;
        // Button will not be inserted when list is exhausted
        if ((btn) && (newsListLoadCount < realLimit)) {
            obj.appendChild(btn);
        }
    }
}

function CreateLoadMoreNewsBtn() {
    var newsBtnHTML = '<div id="'+newsLoaderBtnBlockID+'"><span onclick="InsertNewsItems()" ' +
                                            'id="'+newsLoaderBtnID+'">'+newsLoaderBtnText+'</span></div>';
    InsertNewsContentHTML(newsBtnHTML);
}


// ======================= NEWS PREV NEXT LINKS =====================

function CreateNewsPrevNextLinks() {
    var prevLink = "";
    var nextLink = "";
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
    var linksDiv = objClass("news_links");
    var linksDivText = linksDiv.innerHTML;
    if (prevLink != "") {
        prevLink = '\n<span class="prev_link"><a href="'+prevLink+'">'+
                                        news_prev_link_text+'</a></span>';
        linksDivText = prevLink + linksDivText;
    }
    if (nextLink != "") {
        nextLink = '<span class="next_link"><a href="'+nextLink+'">'+
                                        news_next_link_text+'</a></span>\n';
        linksDivText = linksDivText + nextLink;
    }
    linksDiv.innerHTML = linksDivText;
}


// ======================= NEWS FUNCTIONS =====================

function NewsFunctions() {
    var wHref       = window.location.href;
    var wDirPath    = wHref.substr(0,wHref.lastIndexOf("/"));
    var wDir        = wDirPath.substr(wDirPath.lastIndexOf("/")+1);
    var wFilename   = wHref.split("/").pop(); // Could be empty
    // Create "Load More..." button if more news posts available
    if (((wFilename == "news.html") || (wFilename == "news.php") || (wFilename == "news.htm")) 
                                                && (news_files_list.length > news_list_items)) {
        CreateLoadMoreNewsBtn();
    }
    // Check if we're in news folder
    else if ((wDir == "news") && (news_files_list.length > 1)) {
        CreateNewsPrevNextLinks();
    }
}

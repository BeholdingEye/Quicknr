/* ===========================================================
*
*           QUICKNR GENERAL UTILITY FUNCTIONS
*
*  ===========================================================*/


// ----------------------- Mobile device detector

function DeviceIsMobile() {
    var isMobile = /iPhone|iPad|iPod|Android|Blackberry|Nokia|Opera mini|Windows mobile|Windows phone|iemobile/i.test(navigator.userAgent);
    return isMobile;
}

// ----------------------- Percentage function

function rangeToPercent(number, min, max) {
    return ((number - min) / (max - min)) * 100;
}

// ----------------------- Position functions

// Returns Y position of element, with given offset
function GetYPos(elem, offsetPos) {
    oPos = offsetPos;
    if (elem.offsetParent) {
        do {
            oPos += elem.offsetTop;
        } while (elem = elem.offsetParent);
    }
    return oPos;
}

// Returns X position of element, with given offset
function GetXPos(elem, offsetPos) {
    oPos = offsetPos;
    if (elem.offsetParent) {
        do {
            oPos += elem.offsetLeft;
        } while (elem = elem.offsetParent);
    }
    return oPos;
}

// ----------------------- Image preloader

function LoadImagesIntoMemory(args) {
    // args == [destination HTML filename, list of image URLs, start index in list]
    var htmlFilename    = args[0];
    var imgList         = args[1];
    var startIndex      = args[2];
    if (wFilename == htmlFilename) {
        for (var i = startIndex; i < imgList.length; i++) {
            var img = new Image();
            img.src = imgList[i];
        }
    }
}

// ----------------------- Other functions

function Async(fn, args) {
    // Execute the passed function asynchronously
    setTimeout(function() {fn(args);}, 0);
}

function print(args) {
    console.log(args);
}

// ----------------------- Convenience object-getting functions

function objHtml() {
    return document.documentElement;
}

function objClass(name, parent) {
    if (!parent) {
        return document.getElementsByClassName(name)[0];
    }
    else {
        return parent.getElementsByClassName(name)[0];
    }
}

function objID(id, parent) {
    if (!parent) {
        return document.getElementById(id);
    }
    else {
        return parent.getElementById(id);
    }
    
}

function objTag(tag, parent) {
    if (!parent) {
        return document.getElementsByTagName(tag)[0];
    }
    else {
        return parent.getElementsByTagName(tag)[0];
    }
}

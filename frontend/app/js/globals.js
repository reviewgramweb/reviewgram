var reviewgram = new Reviewgram();
reviewgram.initReviewgramEvents();

function makeBasicAuth(user, password) {
  var tok = user + ':' + password;
  var hash = btoa(tok);
  return "Basic " + hash;
}

var originalAjax = $.ajax
$.ajax = function(options) {
    if (('username' in options) && ('password' in options)) {
        options['beforeSend'] = function (xhr) {
            xhr.setRequestHeader('Authorization', makeBasicAuth(options['username'], options['password']));
        }
    }
    originalAjax(options);
};

// Функция для генерации уникального UUID
var largeUuidv4 = function() {
  var result =  ('xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    var r = nextRandomInt(0xFFFFFFFF) * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
    return  v.toString(16);
  }));
  return (new Date().getTime()) + "-" + result;
};

// Повтореый запрос для получения данных по AJAX
var makeRepeatedRequest = function(options, success)  {
    var ownOptions = options;
    ownOptions["success"] = success;
    ownOptions["error"] = function(xhr) {
         if (xhr.status == 404) {
             if (typeof options["on404"] == "function") {
                 options["on404"]();
             } else {
                 setTimeout(makeRepeatedRequest.bind(null, options, success), 5000);
             }
         } else {
             setTimeout(makeRepeatedRequest.bind(null, options, success), 5000);
        }
    };
    $.ajax(ownOptions);
};

function uint8ArrayToBase64( bytes ) {
    var len = bytes.byteLength;
    for (var i = 0; i < len; i++) {
        binary += String.fromCharCode( bytes[ i ] );
    }
    return window.btoa( binary );
}

function escapeHtml(unsafe) {
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
 }

 function b64DecodeUnicode(str) {
    // Going backwards: from bytestream, to percent-encoding, to original string.
    return decodeURIComponent(atob(str).split('').map(function(c) {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
    }).join(''));
}

function b64EncodeUnicode(str) {
    // first we use encodeURIComponent to get percent-encoded UTF-8,
    // then we convert the percent encodings into raw bytes which
    // can be fed into btoa.
    return btoa(encodeURIComponent(str).replace(/%([0-9A-F]{2})/g,
        function toSolidBytes(match, p1) {
            return String.fromCharCode('0x' + p1);
    }));
}

var wordPartReplacementTable = [
    ["se","ja"],
    ["mi","mie"],
    ["col","cul"],
    ["on","lum"],
    ["qu","g"],
    ["oute","old"],
    ["qu","cul"],
    ["oute","ort"],
    ["quote","quotes"],
    ["quote","proton"],
    ["false","pause"],
    ["else","elsa"],
    ["imp","inp"],
    ["ort","ut"],
    ["n","kn"],
    ["one","own"],
    ["ace","ain"],
    ["ret","rrot"],
    ["ret","rrot"],
    ["ret","ry"],
    ["ret","rried"],
    ["rrot","ry"],
    ["rrot","rried"],
    ["ry","rried"],
    ["ulus","ules"],
    ["ules","ulis"],
    ["ulus","ulis"],
    ["floor","forour"],
    ["shift","just"],
    ["at","as"],
    ["bit","beach"],
    ["wiseand","wyzant"],
    ["hori","where"],
    ["zontal","isonthe"],
    ["col","all"],
    ["on","of"],
    ["double","devil"],
    ["at","that"],
    ["graph","grav"],
    ["icsand","accent"],
    ["tab","temp"],
    ["space","bass"],
    ["four","for"],
    ["for","4"],
    ["4","four"],
    ["as","ave"],
    ["as","ass"],
    ["as","OS"],
    ["ave","ass"],
    ["none","nine"],
    ["none","9"],
    ["nine","9"],
    ["death","def"],
    ["while","i'll"],
    ["while","wow"],
    ["i'll","wow"],
    ["ert","ault"],
    ["def","zelle"],
    ["def","jail"],
    ["def","jeaulous"],
    ["true","future"],
    ["utitlies","chilli's"],
    ["c","sea"],
    ["cmath","cmos"],
    ["math","mos"],
    ["find","fight"],
    ["find","fine"],
    ["os","horse"],
    ["day","date"],
    ["are","every"],
    ["trace","chase"],
    ["dom","and"],
    ["q","queue"],
    ["ecs","ex"],
    ["unicode","unico"],
    ["file","while"],
    ["mapping","metal"],
    ["option","austin"],
    ["pass","carr"],
    ["thread","trade"],
    ["chat","shirt"],
    ["core","or"],
    ["core","score"],
    ["or","score"],
    ["or","query"],
    ["core","query"],
    ["core","corey"],
    ["query","corey"],
    ["ftp","icp"],
    ["smtp","smpp"],
    ["django","junker"],
    ["django","jungle"],
    ["junker","jungle"],
    ["crash","hash"],
    ["mark","smack"],
    ["quo","core"],
    ["score","quo"],
    ["acci","flexi"],
    ["dent","nail"],
    ["type","side"],
    ["type","height"]
];

var similarityLimit = 0.7;
var maxRecursiveDepth = 3;

// Расстояние левенштейна
// Взято из https://gist.github.com/andrei-m/982927
function levenshtein(a, b) {
    if (a.length == 0)
        return b.length;
    if (b.length == 0)
        return a.length;

    var matrix = [];

    // increment along the first column of each row
    var i;
    for (i = 0; i <= b.length; i++){
        matrix[i] = [i];
    }

    // increment each column in the first row
    var j;
    for (j = 0; j <= a.length; j++){
        matrix[0][j] = j;
    }

    // Fill in the rest of the matrix
    for (i = 1; i <= b.length; i++){
        for(j = 1; j <= a.length; j++){
            if (b.charAt(i-1) == a.charAt(j-1)) {
                matrix[i][j] = matrix[i-1][j-1];
            } else {
                matrix[i][j] = Math.min(matrix[i-1][j-1] + 1, // substitution
                                    Math.min(matrix[i][j-1] + 1, // insertion
                                    matrix[i-1][j] + 1)); // deletion
            }
        }
    }

    return matrix[b.length][a.length];
}

function matchesNonExactWithDistWithIndex(test, original, index, depth) {
    var test1 = test.replace(new RegExp("" + wordPartReplacementTable[index][0] + "", "g"), wordPartReplacementTable[index][1]);
    var test2 = test.replace(new RegExp("" + wordPartReplacementTable[index][1] + "", "g"), wordPartReplacementTable[index][0]);
    var dist1 = levenshtein(test1, original);
    var dist2 = levenshtein(test2, original);

    var curTest = test1;
    var minDist = dist1;
    if (dist2 < minDist) {
        curTest = test2;
        minDist = dist2;
    }

    if (depth >= maxRecursiveDepth) {
        return minDist;
    }

    for (var i = index + 1; i < wordPartReplacementTable.length; i++) {
        minDist = Math.min(minDist, matchesNonExactWithDistWithIndex(curTest, original, i, depth + 1));
    }
    return minDist;
}

function matchesNonExactWithDist(test, original) {
    var minDist = levenshtein(test, original);
    for (var i = 0; i < wordPartReplacementTable.length; i++) {
        minDist = Math.min(minDist, matchesNonExactWithDistWithIndex(test, original, i, 1));
    }
    return minDist < original.length * similarityLimit;
}

function matchesNonExact(test, original, replaceSlash) {
    var space = new RegExp("[ \t]", "g");
    var orig1 = original.toLowerCase();
    if (replaceSlash) {
        var slash = new RegExp("slash", "g");
        orig1 = orig1.replace(slash, "/");
    }
    var test1 = test.replace(space, "").toLowerCase();
    orig1 = orig1.replace(space, "").toLowerCase();
    var slashReplace = new RegExp("\\/", "g");

    var fullOrig1 = orig1.replace(slashReplace, "");
    var fullTest1 = test1.replace(slashReplace, "");

    var origParts = orig1.split("/");
    var testParts = test1.split("/");

    var origLast = origParts[origParts.length - 1];
    var testLast = testParts[testParts.length - 1];
    if (replaceSlash) {
        return matchesNonExactWithDist(fullTest1, fullOrig1) || matchesNonExactWithDist(testLast, origLast);
    } else {
        return matchesNonExactWithDist(fullTest1, fullOrig1);
    }
}


if (!String.prototype.endsWith) {
  Object.defineProperty(String.prototype, 'endsWith', {
    value: function(searchString, position) {
      var subjectString = this.toString();
      if (position === undefined || position > subjectString.length) {
        position = subjectString.length;
      }
      position -= searchString.length;
      var lastIndex = subjectString.indexOf(searchString, position);
      return lastIndex !== -1 && lastIndex === position;
    }
  });
}

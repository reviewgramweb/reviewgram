var isEditRequestRunning = false;
var reviewgram = new Reviewgram();

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


// Начало для получения данных из чата для работы системы
var startRequestForRepoInformation = function(chatId, fun)  {
    fetchOrCreateUUID(function(isNew, uuid, timestamp) {
        var wrapper = (function(fun) {
            makeRepeatedRequest({
                "url": "/reviewgram/register_chat_id_for_token/",
                "dataType": "text",
                "data": {
                    "chatId" : reviewgram.requestPeerID(chatId),
                    "uuid": uuid,
                },
                "method": "POST",
            }, fun);
        }).bind(null, fun);
        if (isNew) {
            var text = btoa(uuid);
            reviewgram.sendMessageToBot(text, wrapper);
        } else {
            wrapper();
        }
    });
};

// Получение настроек репозитория
var getRepoSettings = function(chatId, fun, on404)  {
    fetchOrCreateUUID(function(isNew, uuid, timestamp) {
        var wrapper = (function(fun) {
            var wrapInner = function(o) {
                o.password = atob(o.password);
                fun(o);
            };
            makeRepeatedRequest({
                "url": "/reviewgram/get_repo_settings/",
                "dataType": "json",
                "data": {
                    "chatId" : reviewgram.requestPeerID(chatId),
                    "uuid": uuid,
                },
                "method": "GET",
                "on404" : on404
            }, wrapInner);
        }).bind(null, fun);
        if (isNew) {
            var text = btoa(uuid);
            reviewgram.sendMessageToBot(text, wrapper);
        } else {
            wrapper();
        }
    });
};

// Установка настроек репозитория
var setRepoSettings = function(chatId, fun, repoUserName, repoSameName, user, password, on404)  {
    fetchOrCreateUUID(function(isNew, uuid, timestamp) {
        var wrapper = (function(fun) {
            makeRepeatedRequest({
                "url": "/reviewgram/set_repo_settings/",
                "dataType": "json",
                "data": {
                    "chatId" : reviewgram.requestPeerID(chatId),
                    "uuid": uuid,
                    "repoUserName": repoUserName,
                    "repoSameName": repoSameName,
                    "user": user,
                    "password": btoa(password)
                },
                "method": "POST",
                "on404": on404
            }, fun);
        }).bind(null, fun);
        if (isNew) {
            var text = btoa(uuid);
            reviewgram.sendMessageToBot(text, wrapper);
        } else {
            wrapper();
        }
    });
};

var widgetsToCallbacks = {};
var repoSettings = {};
var branchName = "";
var lastCommit = "";
var editedFileName = "";
var editedFileUrl = "";
var editedFileSha = "";
var editedFileContent = "";
var rangeStart = 0;
var rangeEnd = 0;
var aceEditorForRangeSelect = null;
var aceEditorMain = null;
var allowedFileExtensions = [".txt", ".py"];
var editorCursorPosition = null;
var editorAutocompleteSendTimeoutHandle = null;
var editorEditedPart = "";
var namesToModes = {".py": "ace/mode/python"};
var lineSeparator = "";
var resultFileContent = "";
var editedSoundFileBlob = null;
var globalRecorder = null;
var currentRecorderId = 0;

function fileNameToAceMode(fileName) {
    var name = fileName.toLowerCase();
    for (var  key in namesToModes) {
        if (namesToModes.hasOwnProperty(key)) {
            if (name.endsWith(key)) {
                return namesToModes[key];
            }
        }
    }
    return "ace/mode/plain_text";
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

function isMatchesAllowedExtensions(fileName) {
    var name = fileName.toLowerCase();
    for (var  i = 0 ; i < allowedFileExtensions.length; i++) {
        if (name.endsWith(allowedFileExtensions[i])) {
            return true;
        }
    }
    return false;
}
reviewgram.initReviewgramEvents();

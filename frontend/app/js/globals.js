var globalCurrentDialog = "";
var sendMessageRequest = null;
var requestPeerID = null;
var tokenLiveCountMinutes = 150;
var secondsInMinute = 60;

// Функция для генерации уникального UUID
var largeUuidv4 = function() {
  var result =  ('xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    var r = nextRandomInt(0xFFFFFFFF) * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
    return  v.toString(16);
  }));
  return (new Date().getTime()) + "-" + result;
};

// Получение/сохранение идентификатора
var fetchOrCreateUUID = function(fun) {
    var uuid = localStorage.getItem("reviewgram_uuid");
    var timestamp = parseInt(localStorage.getItem("reviewgram_uuid_timestamp"));
    if ((uuid === null) || (timestamp === null)) {
        uuid = largeUuidv4();
        timestamp = parseInt((new Date()).getTime() / 1000.0);
        localStorage.setItem("reviewgram_uuid", uuid);
        localStorage.setItem("reviewgram_uuid_timestamp", timestamp);
        fun(true, uuid, timestamp);
    } else {
        currentTimestamp = parseInt((new Date()).getTime() / 1000.0);
        if (currentTimestamp - timestamp >= tokenLiveCountMinutes * secondsInMinute) {
            uuid = largeUuidv4();
            timestamp = currentTimestamp;
            localStorage.setItem("reviewgram_uuid", uuid);
            localStorage.setItem("reviewgram_uuid_timestamp", timestamp);
            fun(true, uuid, timestamp);
        } else {
            fun(false, uuid, timestamp);
        }
    }
};

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
                    "chatId" : requestPeerID(chatId),
                    "uuid": uuid,
                },
                "method": "POST",
            }, fun);
        }).bind(null, fun);
        if (isNew) {
            var text = btoa(uuid);
            sendMessageRequest(text, wrapper);
        } else {
            wrapper();
        }
    });
};

// Получение настроек репозитория
var getRepoSettings = function(chatId, fun, on404)  {
    fetchOrCreateUUID(function(isNew, uuid, timestamp) {
        var wrapper = (function(fun) {
            makeRepeatedRequest({
                "url": "/reviewgram/get_repo_settings/",
                "dataType": "json",
                "data": {
                    "chatId" : requestPeerID(chatId),
                    "uuid": uuid,
                },
                "method": "GET",
                "on404" : on404
            }, fun);
        }).bind(null, fun);
        if (isNew) {
            var text = btoa(uuid);
            sendMessageRequest(text, wrapper);
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
                    "chatId" : requestPeerID(chatId),
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
            sendMessageRequest(text, wrapper);
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
var allowedFileExtensions = [".txt", ".py"];

// Инициализация виджета микрофона
// TODO: Нормальная работа
var initMicrophoneWidgets = function() {
    var e = $(".reviewgram-microphone-widget");
    e.html("<div class=\"button-wrapper\"><div class=\"button\"></div><div class=\"label\">Нажмите, чтобы ввести голосом</div></div>");
    for (var i = 0; i < e.length; i++) {
        $(e[i]).attr("specific-id", i);
    }
    e.click(function() {
        if ($(this).hasClass("in-process")) {
            $(this).removeClass("in-process");
            $(this).addClass("recognizing");
            $(this).find(".label").html("Производится распознавание");
            // TODO: callback here
        } else {
            if ($(this).hasClass("recognizing")) {
                $(this).removeClass("recognizing");
                $(this).find(".label").html("Нажмите, чтобы ввести голосом");
                // TODO: callback here
            } else {
                $(this).addClass("in-process");
                $(this).find(".label").html("Введите команду");
                // TODO: callback here
            }
        }
    });
}


$("body").on("click", ".reviewgram-select-box li", function() {
    $(this).closest(".reviewgram-select-box").find("li").removeClass("selected");
    $(this).addClass("selected");
});

var makeSearchSubstringHandler = function(dependentSelector) {
    return function() {
        var a = $(this).val().trim();
        var elements = $(dependentSelector);
        for (var i = 0; i < elements.length; i++) {
            var element = $(elements[i]);
            var name = element.attr("data-name");
            var match = true;
            if (a.length > 0) {
                match = (name.indexOf(a) != -1);
            }
            if (match) {
                element.removeClass("hidden").css("display", "block");
            } else {
                element.addClass("hidden").css("display", "none");
            }
        }
    }
};

$("body").on("cut paste keyup", "#branchNameSearch", makeSearchSubstringHandler("#branchName ul li"));
$("body").on("cut paste keyup", "#commitFileSearch", makeSearchSubstringHandler("#commitFile ul li"));


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

function isMatchesAllowedExtensions(fileName) {
    var name = fileName.toLowerCase();
    for (var  i = 0 ; i < allowedFileExtensions.length; i++) {
        if (name.endsWith(allowedFileExtensions[i])) {
            return true;
        }
    }
    return false;
}

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
    ownOptions["error"] = function() {
        setTimeout(makeRepeatedRequest.bind(null, options, success), 5000);
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
                    "chatId" : chatId,
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

from reviewgramdb import *
import os
import os.path
import re

# Формирует имя папки репозитория
def repo_folder_name(repoUserName, repoName, branchId):
    return repoUserName + "_" + repoName + "_" + re.sub(r"[^0-9a-zA-Z_]", "__", branchId)


# существует ли папка репозитория
def is_repo_folder_exists(repoUserName, repoName, branchId):
    folderName = repo_folder_name(repoUserName, repoName, branchId)
    path = os.path.dirname(os.path.abspath(__file__))
    fullPath = path + "/repos/" + folderName + "/.git/"
    return os.path.isdir(fullPath)

# полная папка репозитория
def full_repo_folder_name(repoUserName, repoName, branchId):
    folderName = repo_folder_name(repoUserName, repoName, branchId)
    path = os.path.dirname(os.path.abspath(__file__))
    fullPath = path + "/repos/" + folderName + "/"
    return fullPath

# Пытается вставить задачу на клонирование репозитория
def try_insert_cloning_repo_task(con, repoSite, repoUserName, repoSameName, branchId):
    result = select_and_fetch_one(con, "SELECT * FROM `repository_cache_storage_table` WHERE `REPO_SITE` = %s AND `REPO_USER_NAME` = %s  AND `REPO_SAME_NAME` = %s  AND `BRANCH_ID` = %s LIMIT 1" , [repoSite, repoUserName, repoSameName, branchId])
    if (result is None):
        execute_update(con, "INSERT INTO `repository_cache_storage_table`(REPO_SITE, REPO_USER_NAME, REPO_SAME_NAME, BRANCH_ID, TSTAMP) VALUES (%s, %s, %s, %s, 0)", [repoSite, repoUserName, repoSameName, branchId])



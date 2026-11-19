

local account = ARGV[1]
local base = ARGV[2]
local acc_key = "sha@acc2uuid"

local uuid = redis.call("hget", acc_key, account)
if uuid == false then
    return { -1, "" }
end

local data_key = "sha@data_"..uuid
local base_field = "base"
redis.call("hset", data_key, base_field, base)
redis.call("publish", "db_savebase", uuid)
return 0
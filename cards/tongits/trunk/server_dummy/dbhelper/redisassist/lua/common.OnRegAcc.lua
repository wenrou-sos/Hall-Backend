

local uuid = ARGV[1]
local account = ARGV[2]
local user_base = ARGV[3]
local channel = ARGV[4]

local tmp_holder_acc = "var@thga_"..account
if redis.call("get", tmp_holder_acc) then
    local acc_key = "sha@acc2uuid"
    redis.call("hset", acc_key, account, uuid)
    local data_key = "sha@data_"..uuid
    local base_field = "base"
    redis.call("hset", data_key, base_field, user_base)
    local channel_failed = "channel"
    redis.call("hset", data_key, channel_failed, channel)
    redis.call("publish", "db_savebase", uuid)
    return 0
else
    return -1
end
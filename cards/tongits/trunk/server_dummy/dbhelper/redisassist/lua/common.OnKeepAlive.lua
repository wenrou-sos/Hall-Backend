
local uuid = ARGV[1]
local nowtime = ARGV[2]
local force = ARGV[3]

local keepalive_field = "sha@keepalive"
local data_key = "sha@data_"..uuid

if redis.call("exists", data_key) == 0 then
    return -1
end

if force == "0" then
    if redis.call("hexists", keepalive_field, uuid) == 0 then
        return -2
    end
end

redis.call("hset", keepalive_field, uuid, nowtime)
return 0
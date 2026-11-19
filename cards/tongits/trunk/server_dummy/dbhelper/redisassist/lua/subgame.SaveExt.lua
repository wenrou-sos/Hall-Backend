
local uuid = ARGV[1]
local svr_id = ARGV[2]
local jdata = ARGV[3]
local force = ARGV[4]

local data_key = "sha@sgjson_"..uuid
local sub_key = "ext_"..svr_id
if redis.call("hget", data_key, sub_key) ~= false then
    if force == "0" then
        return -1
    end
end
redis.call("hset", data_key, sub_key, jdata)

return 0
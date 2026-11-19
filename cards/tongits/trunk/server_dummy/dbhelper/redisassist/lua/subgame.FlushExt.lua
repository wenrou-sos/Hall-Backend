
local uuid = ARGV[1]
local svr_id = ARGV[2]

local data_key = "sha@sgjson_"..uuid
local sub_key = "ext_"..svr_id
local ext = redis.call("hget", data_key, sub_key)
if ext == false then
    return -1, false
end
redis.call("hdel", data_key, sub_key)

return 0, ext
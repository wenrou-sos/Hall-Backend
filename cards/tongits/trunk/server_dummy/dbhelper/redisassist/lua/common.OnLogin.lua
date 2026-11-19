
local uuid = ARGV[1]
local base = ARGV[2]
local new_token = ARGV[3]
local acs_token = ARGV[4]
local channel = ARGV[5]

local base_field = "base"
local token_field = "token"
local svrid_field = "svr_id"
local acces_field = "acs_token"
local channel_field = "channel"

local svr_id = ""

local data_key = "sha@data_"..uuid
local lock_field = "locker"
if redis.call("hget", data_key, lock_field) then
    return {-3, svr_id}
end

redis.call("hset", data_key, token_field, new_token)
redis.call("hset", data_key, acces_field, acs_token)
redis.call("hset", data_key, base_field, base)
redis.call("hset", data_key, channel_field, channel)

local cur_svr_id = redis.call("hget", data_key, svrid_field)
if cur_svr_id ~= false then
    svr_id = cur_svr_id
end

return {0, svr_id}
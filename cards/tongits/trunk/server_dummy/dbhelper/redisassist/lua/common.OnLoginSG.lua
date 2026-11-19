
local uuid = ARGV[1]
local token = ARGV[2]
local req_svr_id = ARGV[3]

local data_key = "sha@data_"..uuid
local lock_field = "locker"
if redis.call("hget", data_key, lock_field) then
    return { -3, "" }
end

local base_field = "base"
local token_field = "token"
local svr_id_field = "svr_id"

local base = redis.call("hget", data_key, base_field)
if base == false then
    return { -1, "" }
end

local cur_token = redis.call("hget", data_key, token_field)
if cur_token == false then
    return { -2, "" }
end

if cur_token ~= token then
    return { -2, "" }
end

local cur_svr_id = redis.call("hget", data_key, svr_id_field)
if cur_svr_id ~= false then
    if cur_svr_id ~= req_svr_id then
        return { -4, "" }
    end
end

redis.call("hset", data_key, svr_id_field, req_svr_id)
local uuid2sid_key = "sha@uuid2sid"
redis.call("hset", uuid2sid_key, uuid, req_svr_id)

return { 0, base }

local uuid = ARGV[1]
local data_key = "sha@data_"..uuid
local base_field = "base"
local base = redis.call("hget", data_key, base_field)

local svr_id_field = "svr_id"
local cur_svr_id = redis.call("hget", data_key, svr_id_field)
local svr_id = ""
if cur_svr_id ~= false then
    svr_id = cur_svr_id
end

local token_field = "token"
local cur_token = redis.call("hget", data_key, token_field)
local token = "0"
if cur_token ~= false then
    token = cur_token
end

local acces_field = "acs_token"
local acs_token = redis.call("hget", data_key, acces_field)
if acs_token == false then
    acs_token = "0"
end

return { 0, base, svr_id, token, acs_token }
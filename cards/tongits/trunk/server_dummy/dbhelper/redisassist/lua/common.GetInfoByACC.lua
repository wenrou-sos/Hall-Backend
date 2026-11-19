
local account = ARGV[1]
local acc_key = "sha@acc2uuid"

local uuid = redis.call("hget", acc_key, account)
if uuid == false then
    return { -1, "", "" }
end

local data_key = "sha@data_"..uuid
local base_field = "base"
local base = redis.call("hget", data_key, base_field)
local svr_id_field = "svr_id"
local cur_svr_id = redis.call("hget", data_key, svr_id_field)
local svr_id = ""
if cur_svr_id ~= false then
    svr_id = cur_svr_id
end

return { 0, base, svr_id }

local account = ARGV[1]
local acc_key = "sha@acc2uuid"
local uuid = redis.call("hget", acc_key, account)
if uuid ~= false then
    local data_key = "sha@data_"..uuid
    local base_field = "base"
    local base = redis.call("hget", data_key, base_field)
    if base == false then
        return { -1, 0, "" }
    end
    return { 0, 1, base }
end

local tmp_holder_acc = "var@thga_"..account
if redis.call("get", tmp_holder_acc) then
    return { -3, 0, "" }
end

if not redis.call("set", tmp_holder_acc, 1, "ex", 5) then
    return { -4, 0, "" }
end

local var_uuid = "var@uuid"
local new_uuid = redis.call("get", var_uuid)
redis.call("incr", var_uuid)

return { 0, 2, new_uuid }
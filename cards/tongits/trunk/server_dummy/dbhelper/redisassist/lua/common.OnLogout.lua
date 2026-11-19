
local uuid = ARGV[1]

local token_field = "token"
local acces_field = "acs_token"

local data_key = "sha@data_"..uuid
if redis.call("exists", data_key) == 0 then
    return -1
end

redis.call("hdel", data_key, token_field)
redis.call("hdel", data_key, acces_field)
return 0
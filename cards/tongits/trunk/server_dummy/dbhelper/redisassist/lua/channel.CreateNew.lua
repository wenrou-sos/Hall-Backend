local chl = ARGV[1]
local name = ARGV[2]
local api_key = ARGV[3]
local ex_data = ARGV[4]

local chl_key = "sha@chl_"..chl
if redis.call("exists", chl_key) == 1 then
    return -1
end

local name_field = "name"
local akey_field = "apikey"
local st_field = "status"
local tr_field = "totalreg"
local svr_field = "servers"
local ex_field = "extra"
local onl_field = "onlines"
local unq_id_field = "unq_id"
redis.call("hset", chl_key, name_field, name)
redis.call("hset", chl_key, akey_field, api_key)
redis.call("hset", chl_key, st_field, 0)
redis.call("hset", chl_key, tr_field, 0)
redis.call("hset", chl_key, svr_field, "{}")
redis.call("hset", chl_key, ex_field, ex_data)
redis.call("hset", chl_key, onl_field, 0)
local new_unq_id = tonumber(redis.call("get", "var@chluid")) * 100000
redis.call("hset", chl_key, unq_id_field, new_unq_id)
redis.call("incr", "var@chluid")
redis.call("publish", "db_savechl", chl)
return 0

local uuid = ARGV[1]
local base = ARGV[2]

local data_key = "sha@data_"..uuid
local base_field = "base"
redis.call("hset", data_key, base_field, base)
redis.call("publish", "db_savebase", uuid)
return 0
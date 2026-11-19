
local uuid = ARGV[1]
local svr_id = ARGV[2]
local jdata = ARGV[3]

local data_key = "sha@sgjson_"..uuid
redis.call("hset", data_key, svr_id, jdata)
redis.call("publish", "db_savesg", uuid.."|"..svr_id)

return 0